"""Cognitive state updater — the single authoritative write entry point for
logic card belief state.

Implements the cognitive loop:
    judge_report -> structured belief delta -> atomic card update

All mutations to a logic card's contract, memory, threads, and status flow
through :func:`apply_belief_delta`.  This guarantees ONE load + ONE save per
card per reflection cycle and keeps the audit surface minimal.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from research.logic._yaml_utils import now_ts
from research.logic.lifecycle import validate_transition, build_transition_record
from research.storage.yaml_io import load_yaml, load_yaml_any, save_yaml

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------
# Data contracts
# -----------------------------------------------------------------------


@dataclass
class LogicBeliefDelta:
    """Per-logic cognitive update.  Structured, not narrative."""

    logic_id: str
    batch_id: str
    # Lifecycle
    status_change: Optional[str] = None
    status_reason: str = ""
    # Contract evolution
    focus_question_update: Optional[str] = None
    families_to_add: List[str] = field(default_factory=list)
    families_to_remove: List[str] = field(default_factory=list)
    ops_to_add: List[str] = field(default_factory=list)
    avoid_patterns_to_add: List[str] = field(default_factory=list)
    # Compressed memory
    new_productive: List[dict] = field(default_factory=list)
    new_failed: List[dict] = field(default_factory=list)
    new_exhausted: List[dict] = field(default_factory=list)
    bottleneck_update: Optional[str] = None
    generated_this_batch: int = 0
    admits_this_batch: int = 0
    # Deepening threads
    threads_to_add: List[dict] = field(default_factory=list)
    threads_to_update: List[dict] = field(default_factory=list)
    threads_to_park: List[str] = field(default_factory=list)
    # Next actions
    next_actions: List[str] = field(default_factory=list)


@dataclass
class GlobalEscalationDelta:
    """Cross-logic signals.  Persisted with status machine."""

    batch_id: str
    status: str = "pending"  # pending -> consumed -> applied|dismissed
    proposed_lessons: List[dict] = field(default_factory=list)
    proposed_forbidden: List[dict] = field(default_factory=list)
    logic_proposals: List[dict] = field(default_factory=list)
    saturation_signal: Optional[dict] = None
    consumed_at: Optional[str] = None
    resolved_at: Optional[str] = None
    resolution: Optional[str] = None


# -----------------------------------------------------------------------
# Core write entry point
# -----------------------------------------------------------------------

_VALID_ESCALATION_TRANSITIONS: Dict[str, frozenset] = {
    "pending": frozenset({"consumed"}),
    "consumed": frozenset({"applied", "dismissed"}),
    "applied": frozenset(),
    "dismissed": frozenset(),
}


def apply_belief_delta(
    card_path: Path,
    delta: LogicBeliefDelta,
) -> dict:
    """Atomic card updater.  ONE load, all mutations in memory, ONE save.

    Parameters
    ----------
    card_path
        Path to the logic card YAML file.
    delta
        The structured belief delta to apply.
    Returns
    -------
    dict
        The updated card dict (as saved to disk).

    Raises
    ------
    ValueError
        If a requested status transition is illegal.
    FileNotFoundError
        If *card_path* does not exist.
    """
    if not card_path.exists():
        raise FileNotFoundError(f"Card file not found: {card_path}")

    # 1. Single load
    card = load_yaml(card_path)

    old_status = card.get("status", "")
    # 2. Status transition (validated first so we fail before mutating)
    if delta.status_change is not None:
        validate_transition(old_status, delta.status_change)
        card["status"] = delta.status_change
        transitions = card.setdefault("evidence_summary", {}).setdefault(
            "transitions", []
        )
        transitions.append(
            build_transition_record(old_status, delta.status_change, delta.status_reason)
        )

    # 3. Contract mutations
    contract = card.setdefault("contract", {})
    if delta.focus_question_update is not None:
        contract["current_focus_question"] = delta.focus_question_update

    families = contract.setdefault("preferred_families", [])
    for fam in delta.families_to_add:
        if fam not in families:
            families.append(fam)
    for fam in delta.families_to_remove:
        if fam in families:
            families.remove(fam)

    ops = contract.setdefault("suggested_ops", [])
    for op in delta.ops_to_add:
        if op not in ops:
            ops.append(op)

    avoid = contract.setdefault("avoid_patterns", [])
    for pat in delta.avoid_patterns_to_add:
        if pat not in avoid:
            avoid.append(pat)

    # 4. Memory mutations
    evidence = card.setdefault("evidence_summary", {})

    if delta.new_productive:
        productive = evidence.setdefault("productive_families", [])
        for entry in delta.new_productive:
            _merge_family_entry(productive, entry)

    if delta.new_failed:
        failed = evidence.setdefault("failed_families", [])
        for entry in delta.new_failed:
            _merge_family_entry(failed, entry)

    if delta.new_exhausted:
        exhausted = evidence.setdefault("exhausted_routes", [])
        for entry in delta.new_exhausted:
            _merge_family_entry(exhausted, entry)

    if delta.bottleneck_update is not None:
        evidence["current_bottleneck"] = delta.bottleneck_update

    # Counters
    evidence["factors_generated"] = (
        evidence.get("factors_generated", 0) + delta.generated_this_batch
    )
    evidence["factors_admitted"] = (
        evidence.get("factors_admitted", 0) + delta.admits_this_batch
    )
    if delta.admits_this_batch > 0:
        evidence["rounds_without_admit"] = 0
    else:
        evidence["rounds_without_admit"] = (
            evidence.get("rounds_without_admit", 0) + 1
        )

    # 5. Thread mutations
    threads = card.setdefault("deepening_threads", [])

    for thread in delta.threads_to_add:
        threads.append(thread)

    for update in delta.threads_to_update:
        tid = update.get("id", "")
        for existing in threads:
            if existing.get("id") == tid:
                existing.update(update)
                break

    for tid in delta.threads_to_park:
        for existing in threads:
            if existing.get("id") == tid:
                existing["status"] = "parked"
                break

    # 6. Next actions and bookkeeping
    card["next_actions"] = delta.next_actions
    card["last_reflected_batch"] = delta.batch_id
    card["updated_at"] = now_ts()

    # 7. Single save
    save_yaml(card_path, card)

    return card


# -----------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------

def _merge_family_entry(family_list: list, new_entry: dict) -> None:
    """Merge by family_id: update existing or append new."""
    fid = new_entry.get("family_id", "")
    if not fid:
        family_list.append(new_entry)
        return
    for i, existing in enumerate(family_list):
        if existing.get("family_id") == fid:
            existing.update(new_entry)
            return
    family_list.append(new_entry)


# -----------------------------------------------------------------------
# Reflection markdown
# -----------------------------------------------------------------------


def write_reflection_md(
    reflection_path: Path,
    delta: LogicBeliefDelta,
    narrative: str,
) -> None:
    """Append a batch reflection section to the markdown file."""
    reflection_path.parent.mkdir(parents=True, exist_ok=True)

    header = f"\n## Batch {delta.batch_id} — {now_ts()}\n\n"
    body_lines = [
        f"**Logic**: {delta.logic_id}\n",
        f"**Generated**: {delta.generated_this_batch}  |  "
        f"**Admitted**: {delta.admits_this_batch}\n",
    ]
    if delta.status_change:
        body_lines.append(
            f"**Status change**: → {delta.status_change} ({delta.status_reason})\n"
        )
    if delta.bottleneck_update:
        body_lines.append(f"**Bottleneck**: {delta.bottleneck_update}\n")
    if delta.next_actions:
        body_lines.append("**Next actions**:\n")
        for action in delta.next_actions:
            body_lines.append(f"- {action}\n")
    body_lines.append(f"\n{narrative}\n")

    section = header + "".join(body_lines)

    with open(reflection_path, "a", encoding="utf-8") as f:
        f.write(section)


# -----------------------------------------------------------------------
# Global escalation persistence
# -----------------------------------------------------------------------


def _escalation_to_dict(delta: GlobalEscalationDelta) -> dict:
    """Serialize a GlobalEscalationDelta to a plain dict."""
    d: Dict[str, Any] = {
        "batch_id": delta.batch_id,
        "status": delta.status,
        "proposed_lessons": delta.proposed_lessons,
        "proposed_forbidden": delta.proposed_forbidden,
        "logic_proposals": delta.logic_proposals,
    }
    if delta.saturation_signal is not None:
        d["saturation_signal"] = delta.saturation_signal
    if delta.consumed_at is not None:
        d["consumed_at"] = delta.consumed_at
    if delta.resolved_at is not None:
        d["resolved_at"] = delta.resolved_at
    if delta.resolution is not None:
        d["resolution"] = delta.resolution
    return d


def save_global_escalation(path: Path, delta: GlobalEscalationDelta) -> None:
    """Persist to YAML.  If file has existing entries, append."""
    entries = load_global_escalation(path)
    entries.append(_escalation_to_dict(delta))
    _save_global_escalation_entries(path, entries)


def load_global_escalation(path: Path) -> list:
    """Load all escalation entries.  Return empty list if file missing."""
    data = load_yaml_any(path)
    if data == {}:
        return []
    if isinstance(data, list):
        return data
    if _is_ledger_path(path) and isinstance(data, dict):
        entries = data.get("global_escalations", [])
        return entries if isinstance(entries, list) else []
    if isinstance(data, dict):
        # Wrap a single dict in a list for backward compat
        return [data]
    return []


def transition_escalation(
    path: Path,
    batch_id: str,
    new_status: str,
    resolution: str = "",
) -> None:
    """Transition a specific escalation entry's status.

    Valid transitions: pending->consumed, consumed->applied|dismissed.
    Raises ValueError if the transition is invalid or entry not found.
    """
    entries = load_global_escalation(path)

    target = None
    for entry in entries:
        if entry.get("batch_id") == batch_id:
            target = entry
            break

    if target is None:
        raise ValueError(f"No escalation entry found for batch_id={batch_id!r}")

    current = target.get("status", "pending")
    allowed = _VALID_ESCALATION_TRANSITIONS.get(current, frozenset())
    if new_status not in allowed:
        raise ValueError(
            f"Cannot transition escalation from {current!r} to {new_status!r}. "
            f"Allowed: {sorted(allowed)}"
        )

    target["status"] = new_status
    if new_status == "consumed":
        target["consumed_at"] = now_ts()
    if new_status in ("applied", "dismissed"):
        target["resolved_at"] = now_ts()
        if resolution:
            target["resolution"] = resolution

    _save_global_escalation_entries(path, entries)


def consume_pending_escalations(path: Path) -> List[dict]:
    """Batch-consume all pending escalation entries.

    Transitions each ``pending`` entry to ``consumed`` and returns
    the list of consumed entries for the caller to act on.
    Returns an empty list if no pending entries exist.
    """
    entries = load_global_escalation(path)
    consumed = []
    for entry in entries:
        if entry.get("status") == "pending":
            entry["status"] = "consumed"
            entry["consumed_at"] = now_ts()
            consumed.append(entry)
    if consumed:
        _save_global_escalation_entries(path, entries)
    return consumed


def resolve_escalation(
    path: Path,
    batch_id: str,
    resolution: str,
    *,
    dismiss: bool = False,
) -> None:
    """Resolve a consumed escalation entry to applied or dismissed.

    Parameters
    ----------
    path
        Path to ``global_escalation.yaml``.
    batch_id
        The batch_id of the entry to resolve.
    resolution
        Free-text reason for the resolution.
    dismiss
        If True, status becomes ``dismissed``; otherwise ``applied``.
    """
    new_status = "dismissed" if dismiss else "applied"
    transition_escalation(path, batch_id, new_status, resolution=resolution)


# -----------------------------------------------------------------------
# Derived state recompute
# -----------------------------------------------------------------------


def recompute_research_state(cards_dir: Path, state_store: Any) -> dict:
    """Glob L*.yaml, extract statuses, update research state.

    Updates ``active_logic_ids``, ``warm_logic_ids``, and
    ``schedulable_logic_ids`` (active + productive + warm).
    All other state fields (current_batch, etc.) are preserved.

    Parameters
    ----------
    cards_dir
        Directory containing logic card YAML files (``L*.yaml``).
    state_store
        An object with ``update_state(patch: dict) -> dict`` method
        (typically :class:`research.storage.state_store.StateStore`).

    Returns
    -------
    dict
        The full updated state dict.
    """
    active: List[str] = []
    warm: List[str] = []
    productive: List[str] = []

    for card_file in sorted(cards_dir.glob("L*.yaml")):
        card = load_yaml(card_file)
        lid = card.get("logic_id", "")
        status = card.get("status", "")
        if status == "active":
            active.append(lid)
        elif status == "warm":
            warm.append(lid)
        elif status == "productive":
            productive.append(lid)

    return state_store.update_state(
        {
            "active_logic_ids": active,
            "warm_logic_ids": warm,
            "schedulable_logic_ids": sorted(active + productive + warm),
        }
    )


def _is_ledger_path(path: Path) -> bool:
    return path.name == "ledger.yaml"


def _save_global_escalation_entries(path: Path, entries: list[dict]) -> None:
    if _is_ledger_path(path):
        ledger = load_yaml(path)
        ledger["global_escalations"] = entries
        save_yaml(path, ledger)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    save_yaml(path, entries)
