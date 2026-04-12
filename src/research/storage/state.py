"""Read/write the system state file (``storage/state.yaml``).

The state file is the single canonical answer to "where is the loop right now".
Schema per refactor_plan.md §10:

    current_batch: null | batch_{NNN}
    current_batch_phase: null | designed | executing | judged | archived
    last_batch: null | batch_{NNN}
    round: int
    last_activity: ISO-8601 timestamp
    rounds_since_last_consolidation: int

Phase transitions (enforced by :func:`transition_phase`):

    null → designed → executing → judged → archived → null (with round++ and
    current_batch = null at the end)

All other transitions raise :class:`InvalidPhaseTransition`. This is how we
get Q32 idempotency for free — double-archive raises because the precondition
``current_batch_phase == judged`` is no longer satisfied.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .yaml_io import load_yaml, save_yaml

# Allowed phase transitions as a DAG. None is the "idle" state.
#
# Naming note: "judged" means "Phase 2 EXECUTE completed, result.yaml exists,
# ready for Phase 3 JUDGE to run" — NOT "has already been judged". The name
# was chosen to mirror the next step's identity (who acts next), not the past.
_PHASE_TRANSITIONS: dict[str | None, set[str | None]] = {
    None: {"designed"},          # Phase 1 START+DESIGN completed
    "designed": {"executing"},   # Phase 2 EXECUTE started
    "executing": {"judged"},     # Phase 2 done → ready for Phase 3 JUDGE
    "judged": {"archived"},      # Phase 3 done → ready for Phase 4 ARCHIVE
    "archived": {None},          # Phase 4 done → idle (round++ in finish_batch)
}

_VALID_PHASES: set[str | None] = {None, "designed", "executing", "judged", "archived"}

_REQUIRED_FIELDS: set[str] = {
    "current_batch",
    "current_batch_phase",
    "last_batch",
    "round",
    "last_activity",
    "rounds_since_last_consolidation",
}


class InvalidPhaseTransition(RuntimeError):
    """Raised when a phase transition violates the state machine."""


class InvalidStateSchema(RuntimeError):
    """Raised when state.yaml on disk is missing required fields."""


@dataclass
class State:
    """In-memory representation of state.yaml.

    Immutable via convention — use :meth:`with_patch` to derive a new instance
    rather than mutating in place.
    """

    current_batch: str | None = None
    current_batch_phase: str | None = None
    last_batch: str | None = None
    round: int = 0
    last_activity: str = ""
    rounds_since_last_consolidation: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "State":
        """Build from a dict, validating required fields are present."""
        missing = _REQUIRED_FIELDS - set(data.keys())
        if missing:
            raise InvalidStateSchema(
                f"state.yaml missing required fields: {sorted(missing)}"
            )
        phase = data["current_batch_phase"]
        if phase not in _VALID_PHASES:
            raise InvalidStateSchema(
                f"current_batch_phase={phase!r} not in {sorted(p for p in _VALID_PHASES if p)}"
            )
        return cls(
            current_batch=data["current_batch"],
            current_batch_phase=phase,
            last_batch=data["last_batch"],
            round=int(data["round"]),
            last_activity=str(data["last_activity"]),
            rounds_since_last_consolidation=int(data["rounds_since_last_consolidation"]),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def with_patch(self, **kwargs: Any) -> "State":
        """Return a new State with the given fields replaced."""
        d = self.to_dict()
        d.update(kwargs)
        return State.from_dict(d)


class StateFile:
    """Read/write facade over state.yaml with phase-transition enforcement."""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def read(self) -> State:
        """Read state.yaml, raising :class:`InvalidStateSchema` on malformed data."""
        data = load_yaml(self._path)
        if not data:
            raise InvalidStateSchema(
                f"state.yaml does not exist or is empty at {self._path}"
            )
        return State.from_dict(data)

    def write(self, state: State) -> None:
        """Stamp ``last_activity`` and atomically write state.yaml."""
        stamped = state.with_patch(last_activity=_now_iso())
        save_yaml(self._path, stamped.to_dict())

    # ------------------------------------------------------------------
    # High-level transitions
    # ------------------------------------------------------------------

    def begin_batch(self, batch_id: str) -> State:
        """Transition from idle → ``designed``. Opens a new batch.

        Raises if already in a batch (current_batch is not None).
        """
        state = self.read()
        if state.current_batch is not None or state.current_batch_phase is not None:
            raise InvalidPhaseTransition(
                f"cannot begin {batch_id}: already in batch "
                f"{state.current_batch!r} at phase {state.current_batch_phase!r}"
            )
        new = state.with_patch(
            current_batch=batch_id,
            current_batch_phase="designed",
        )
        self.write(new)
        return new

    def transition_phase(self, target: str) -> State:
        """Advance ``current_batch_phase`` to *target*, enforcing the DAG.

        Valid sequence: ``designed → executing → judged → archived``.
        Raises :class:`InvalidPhaseTransition` otherwise — this is the
        mechanism that gives us Q32 idempotency (double-archive raises).
        """
        state = self.read()
        current = state.current_batch_phase
        allowed = _PHASE_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise InvalidPhaseTransition(
                f"cannot transition phase {current!r} → {target!r} "
                f"(allowed: {sorted(p for p in allowed if p)})"
            )
        new = state.with_patch(current_batch_phase=target)
        self.write(new)
        return new

    def finish_batch(self) -> State:
        """Close the current batch after ``archived`` and return to idle.

        Increments ``round``, moves ``current_batch`` to ``last_batch``,
        clears ``current_batch_phase``, and bumps
        ``rounds_since_last_consolidation``.
        """
        state = self.read()
        if state.current_batch_phase != "archived":
            raise InvalidPhaseTransition(
                f"cannot finish batch at phase {state.current_batch_phase!r}; "
                "must be archived first"
            )
        new = state.with_patch(
            current_batch=None,
            current_batch_phase=None,
            last_batch=state.current_batch,
            round=state.round + 1,
            rounds_since_last_consolidation=state.rounds_since_last_consolidation + 1,
        )
        self.write(new)
        return new

    def mark_consolidated(self) -> State:
        """Reset ``rounds_since_last_consolidation`` to 0 after Phase 5."""
        state = self.read()
        if state.current_batch is not None:
            raise InvalidPhaseTransition(
                "cannot consolidate while a batch is in flight "
                f"(current_batch={state.current_batch!r})"
            )
        new = state.with_patch(rounds_since_last_consolidation=0)
        self.write(new)
        return new


def _now_iso() -> str:
    """UTC ISO-8601 timestamp with second precision."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
