"""Batch phase state machine and ledger structure validation.

Defines the legal batch lifecycle phases, their transitions, and
the ledger top-level key whitelist used to prevent stray writes.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

BATCH_PHASES = frozenset({
    "frozen",
    "executed",
    "interrupted_judge",
    "judged",
    "finalized",
    "abandoned",
})

PHASE_TRANSITIONS: dict[str, frozenset[str]] = {
    "frozen": frozenset({"executed", "abandoned"}),
    "executed": frozenset({"judged", "interrupted_judge", "abandoned"}),
    "interrupted_judge": frozenset({"judged", "abandoned"}),
    "judged": frozenset({"finalized", "abandoned"}),
    "finalized": frozenset(),
    "abandoned": frozenset(),
}

LEDGER_TOP_LEVEL_WHITELIST = frozenset({
    "batch_usage",
    "holdout_reviews",
    "search_ledger",
    "write_audit_log",
    "global_escalations",
})

BATCH_USAGE_UNIFIED_FIELDS = frozenset({
    "batch_id",
    "candidate_count",
    "logic_ids",
    "phase",
    "holdout_used",
    "train_range",
    "validation_range",
    "validation_window_id",
})


def validate_phase_transition(current: str, target: str) -> None:
    """Raise ValueError if *current* → *target* is not a legal transition."""
    allowed = PHASE_TRANSITIONS.get(current, frozenset())
    if target not in allowed:
        raise ValueError(
            f"Illegal batch phase transition: {current!r} → {target!r}. "
            f"Allowed from {current!r}: {sorted(allowed)}"
        )


def derive_phase_from_files(batch_dir: Path) -> str:
    """Derive the batch phase from which files exist on disk.

    Returns one of: frozen, executed, interrupted_judge, judged.
    """
    has_judge_report = (batch_dir / "judge_report.yaml").exists()
    has_result = (batch_dir / "research_result.yaml").exists()
    has_packet = (batch_dir / "judge_packet.yaml").exists()

    if has_judge_report:
        return "judged"
    if has_result and has_packet:
        # Has result + packet but no report → interrupted between execute and judge
        return "interrupted_judge"
    if has_result:
        return "executed"
    return "frozen"


def validate_ledger_top_level_keys(ledger: dict[str, Any]) -> list[str]:
    """Return a list of unexpected top-level keys in the ledger dict."""
    unexpected = set(ledger.keys()) - LEDGER_TOP_LEVEL_WHITELIST
    return [f"Unexpected ledger top-level key: {k!r}" for k in sorted(unexpected)]
