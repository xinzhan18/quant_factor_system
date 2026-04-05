"""Logic lifecycle — state transitions, family promotion, and arbitration.

States: proposed -> active -> warm -> productive -> saturated -> parked -> dead

Key operations:
- transition():        Move a logic card between states
- promote_family():    Consume 2-batch evidence to promote a family
- record_arbitration(): Record judge recommendation vs logic decision
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from research.logic._yaml_utils import dump_yaml, now_ts
from research.logic.cards import LogicCard, LogicCardStore, VALID_STATUSES

logger = logging.getLogger(__name__)

# Valid state transitions (from -> set of allowed to-states)
ALLOWED_TRANSITIONS: Dict[str, frozenset] = {
    "proposed": frozenset({"active", "warm", "parked", "dead"}),
    "active": frozenset({"warm", "productive", "saturated", "parked", "dead"}),
    "warm": frozenset({"active", "productive", "parked", "dead"}),
    "productive": frozenset({"active", "warm", "saturated", "parked", "dead"}),
    "saturated": frozenset({"warm", "parked", "dead"}),
    "parked": frozenset({"active", "warm", "dead"}),
    "dead": frozenset(),  # terminal
}

# Minimum batches of evidence required to promote a family
MIN_BATCHES_FOR_PROMOTION = 2

# Maximum subspace redundancy allowed for family promotion
MAX_SUBSPACE_REDUNDANCY = 0.7


@dataclass
class ArbitrationRecord:
    """Records a judge recommendation vs. the logic-layer decision."""

    logic_id: str
    factor_id: str
    judge_recommendation: str  # admit / reject
    logic_decision: str  # admit / reject / override_admit / override_reject
    reason: str = ""
    is_override: bool = False
    recorded_at: str = ""

    def __post_init__(self) -> None:
        if not self.recorded_at:
            self.recorded_at = now_ts()
        self.is_override = self.judge_recommendation != self.logic_decision.replace(
            "override_", ""
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "logic_id": self.logic_id,
            "factor_id": self.factor_id,
            "judge_recommendation": self.judge_recommendation,
            "logic_decision": self.logic_decision,
            "reason": self.reason,
            "is_override": self.is_override,
            "recorded_at": self.recorded_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ArbitrationRecord":
        return cls(
            logic_id=data["logic_id"],
            factor_id=data["factor_id"],
            judge_recommendation=data["judge_recommendation"],
            logic_decision=data["logic_decision"],
            reason=data.get("reason", ""),
            is_override=data.get("is_override", False),
            recorded_at=data.get("recorded_at", ""),
        )


class LifecycleManager:
    """Manages logic card state transitions, family promotion, and arbitration."""

    def __init__(self, store: LogicCardStore, storage_dir: Path) -> None:
        self._store = store
        self._storage_dir = Path(storage_dir)
        self._arbitration_dir = self._storage_dir / "logic" / "arbitration"

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    def transition(
        self,
        logic_id: str,
        to_status: str,
        *,
        reason: str = "",
    ) -> LogicCard:
        """Transition a logic card to a new status.

        Raises ValueError if the transition is not allowed.
        Raises KeyError if the logic card is not found.
        """
        if to_status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid target status {to_status!r}; "
                f"must be one of {sorted(VALID_STATUSES)}"
            )

        card = self._store.get(logic_id)
        if card is None:
            raise KeyError(f"Logic card {logic_id!r} not found")

        allowed = ALLOWED_TRANSITIONS.get(card.status, frozenset())
        if to_status not in allowed:
            raise ValueError(
                f"Cannot transition {logic_id} from {card.status!r} to "
                f"{to_status!r}. Allowed targets: {sorted(allowed)}"
            )

        old_status = card.status
        card.status = to_status

        # Record transition in evidence_summary
        transitions = card.evidence_summary.setdefault("transitions", [])
        transitions.append(
            {
                "from": old_status,
                "to": to_status,
                "reason": reason,
                "at": now_ts(),
            }
        )

        self._store.update(card)
        logger.info(
            "Transitioned %s: %s -> %s (reason: %s)",
            logic_id,
            old_status,
            to_status,
            reason or "none",
        )
        return card

    def get_allowed_transitions(self, logic_id: str) -> List[str]:
        """Return the list of states this logic can transition to."""
        card = self._store.get(logic_id)
        if card is None:
            raise KeyError(f"Logic card {logic_id!r} not found")
        return sorted(ALLOWED_TRANSITIONS.get(card.status, frozenset()))

    # ------------------------------------------------------------------
    # Family promotion
    # ------------------------------------------------------------------

    def promote_family(
        self,
        logic_id: str,
        family_id: str,
        *,
        batch_evidence: List[Dict[str, Any]],
        subspace_redundancy: float = 0.0,
    ) -> Tuple[bool, str]:
        """Attempt to promote a family within a logic's evidence.

        Requirements:
        - At least MIN_BATCHES_FOR_PROMOTION batches of evidence
        - Subspace redundancy must be below MAX_SUBSPACE_REDUNDANCY

        Returns (success, reason) tuple.
        """
        card = self._store.get(logic_id)
        if card is None:
            raise KeyError(f"Logic card {logic_id!r} not found")

        if len(batch_evidence) < MIN_BATCHES_FOR_PROMOTION:
            return (
                False,
                f"Need {MIN_BATCHES_FOR_PROMOTION} batches, "
                f"got {len(batch_evidence)}",
            )

        if subspace_redundancy > MAX_SUBSPACE_REDUNDANCY:
            return (
                False,
                f"Subspace redundancy {subspace_redundancy:.2f} exceeds "
                f"max {MAX_SUBSPACE_REDUNDANCY:.2f}",
            )

        # Record promotion
        promoted = card.evidence_summary.setdefault("promoted_families", [])
        promoted.append(
            {
                "family_id": family_id,
                "batch_count": len(batch_evidence),
                "subspace_redundancy": subspace_redundancy,
                "promoted_at": now_ts(),
            }
        )

        self._store.update(card)
        logger.info(
            "Promoted family %s under logic %s (%d batches, redundancy=%.2f)",
            family_id,
            logic_id,
            len(batch_evidence),
            subspace_redundancy,
        )
        return (True, "family promoted")

    # ------------------------------------------------------------------
    # Arbitration
    # ------------------------------------------------------------------

    def record_arbitration(
        self,
        *,
        logic_id: str,
        factor_id: str,
        judge_recommendation: str,
        logic_decision: str,
        reason: str = "",
    ) -> ArbitrationRecord:
        """Record a judge vs. logic arbitration decision.

        The record is always persisted, whether or not it is an override.
        """
        record = ArbitrationRecord(
            logic_id=logic_id,
            factor_id=factor_id,
            judge_recommendation=judge_recommendation,
            logic_decision=logic_decision,
            reason=reason,
        )

        self._arbitration_dir.mkdir(parents=True, exist_ok=True)
        arb_file = self._arbitration_dir / f"arbitration_{logic_id}.yaml"

        existing: List[Dict[str, Any]] = []
        if arb_file.exists():
            with open(arb_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data and isinstance(data, dict):
                existing = data.get("records", [])

        existing.append(record.to_dict())

        dump_yaml(arb_file, {"logic_id": logic_id, "records": existing})

        if record.is_override:
            logger.warning(
                "OVERRIDE: %s factor %s — judge=%s, logic=%s (reason: %s)",
                logic_id,
                factor_id,
                judge_recommendation,
                logic_decision,
                reason,
            )
        else:
            logger.info(
                "Arbitration: %s factor %s — aligned: %s",
                logic_id,
                factor_id,
                logic_decision,
            )

        return record

    def list_arbitrations(
        self, logic_id: str
    ) -> List[ArbitrationRecord]:
        """Return all arbitration records for a given logic."""
        arb_file = self._arbitration_dir / f"arbitration_{logic_id}.yaml"
        if not arb_file.exists():
            return []
        with open(arb_file, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data or not isinstance(data, dict):
            return []
        return [
            ArbitrationRecord.from_dict(r) for r in data.get("records", [])
        ]
