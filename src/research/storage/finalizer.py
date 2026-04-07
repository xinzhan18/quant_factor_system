"""Batch finalization: judge report -> logic cards -> research state."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from research.logic.reflect import LogicBeliefDelta, apply_belief_delta, recompute_research_state
from research.storage.ledger_store import LedgerStore
from research.storage.paths import StoragePaths
from research.storage.result_store import ResultStore
from research.storage.state_store import StateStore
from research.storage.yaml_io import load_yaml


@dataclass
class FinalizeResult:
    batch_id: str
    updated_logic_ids: list[str]
    active_logic_ids: list[str]
    warm_logic_ids: list[str]
    schedulable_logic_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "updated_logic_ids": list(self.updated_logic_ids),
            "active_logic_ids": list(self.active_logic_ids),
            "warm_logic_ids": list(self.warm_logic_ids),
            "schedulable_logic_ids": list(self.schedulable_logic_ids),
        }


class BatchFinalizer:
    """Apply a judged batch's decisions to persistent cognitive state."""

    def __init__(self, paths: StoragePaths | None = None) -> None:
        self._paths = paths or StoragePaths()
        self._results = ResultStore(self._paths)
        self._state = StateStore(self._paths)
        self._ledger = LedgerStore(self._paths)

    def finalize_batch(self, batch_id: str) -> FinalizeResult:
        report = self._results.load_judge_report(batch_id)
        if not report:
            raise FileNotFoundError(f"judge_report missing for {batch_id}")

        diagnostics = _logic_mapping(report.get("logic_diagnostics", {}))
        recommendations = _logic_mapping(report.get("logic_recommendations", {}))
        candidate_counts = _candidate_counts(report.get("candidate_verdicts", []))

        updated_logic_ids: list[str] = []
        for logic_id, rec in recommendations.items():
            card_path = self._paths.logic_card_file(logic_id)
            if not card_path.exists():
                continue
            delta = _build_delta(
                paths=self._paths,
                logic_id=logic_id,
                batch_id=batch_id,
                recommendation=rec,
                diagnostics=diagnostics.get(logic_id, {}),
                counts=candidate_counts.get(logic_id, {"generated": 0, "admits": 0}),
            )
            apply_belief_delta(card_path, delta)
            updated_logic_ids.append(logic_id)

        state = recompute_research_state(self._paths.logic_cards_dir, self._state)
        state = self._state.update_state(
            {
                "current_batch": None,
                "current_batch_phase": "finalized",
                "last_completed_batch": batch_id,
            }
        )
        self._ledger.append_audit_entry(
            actor="research.finalize",
            action="finalize_batch",
            target=batch_id,
            detail=f"updated_logics={','.join(updated_logic_ids)}",
        )
        return FinalizeResult(
            batch_id=batch_id,
            updated_logic_ids=updated_logic_ids,
            active_logic_ids=list(state.get("active_logic_ids", [])),
            warm_logic_ids=list(state.get("warm_logic_ids", [])),
            schedulable_logic_ids=list(state.get("schedulable_logic_ids", [])),
        )


def _logic_mapping(value: Any) -> dict[str, dict[str, Any]]:
    if isinstance(value, dict):
        return {
            str(k): v for k, v in value.items()
            if isinstance(v, dict)
        }
    if isinstance(value, list):
        out: dict[str, dict[str, Any]] = {}
        for item in value:
            if isinstance(item, dict) and item.get("logic_id"):
                out[str(item["logic_id"])] = item
        return out
    return {}


def _candidate_counts(verdicts: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    counts: dict[str, dict[str, int]] = {}
    for item in verdicts:
        if not isinstance(item, dict):
            continue
        logic_id = str(item.get("logic_id", ""))
        if not logic_id:
            continue
        slot = counts.setdefault(logic_id, {"generated": 0, "admits": 0})
        slot["generated"] += 1
        if str(item.get("verdict", "")) in {"admit", "replace"}:
            slot["admits"] += 1
    return counts


def _build_delta(
    *,
    paths: StoragePaths,
    logic_id: str,
    batch_id: str,
    recommendation: dict[str, Any],
    diagnostics: dict[str, Any],
    counts: dict[str, int],
) -> LogicBeliefDelta:
    target_status = str(recommendation.get("recommended_status", "") or "").strip()
    status_change = target_status if target_status else None
    detail_reason = str(recommendation.get("reason", "") or "").strip()

    next_actions = _next_actions_from_diagnostics(diagnostics)
    avoid_patterns = _failure_boundary_patterns(diagnostics.get("failure_boundary", ""))
    bottleneck = _first_non_empty(
        diagnostics.get("thesis_update", ""),
        detail_reason,
    )

    current_status = ""
    card = load_yaml(paths.logic_card_file(logic_id))
    if card:
        current_status = str(card.get("status", ""))
    if status_change == current_status:
        status_change = None

    return LogicBeliefDelta(
        logic_id=logic_id,
        batch_id=batch_id,
        status_change=status_change,
        status_reason=detail_reason,
        generated_this_batch=int(counts.get("generated", 0)),
        admits_this_batch=int(counts.get("admits", 0)),
        bottleneck_update=bottleneck,
        avoid_patterns_to_add=avoid_patterns,
        next_actions=next_actions,
    )


def _next_actions_from_diagnostics(diagnostics: dict[str, Any]) -> list[str]:
    probes = diagnostics.get("next_best_probes", [])
    actions: list[str] = []
    if isinstance(probes, list):
        for probe in probes:
            if not isinstance(probe, dict):
                continue
            expr = str(probe.get("expr", "")).strip()
            why = str(probe.get("why", "")).strip()
            if expr and why:
                actions.append(f"{expr} — {why}")
            elif expr:
                actions.append(expr)
    return actions


def _failure_boundary_patterns(text: str) -> list[str]:
    if not text:
        return []
    parts = [line.strip(" -\n\t") for line in str(text).splitlines()]
    return [part for part in parts if part]


def _first_non_empty(*values: Any) -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return ""
