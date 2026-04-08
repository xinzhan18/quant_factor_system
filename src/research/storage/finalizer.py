"""Batch finalization: judge report -> logic cards -> research state.

Expanded flow:
1.  Load judge_report
2.  Validate batch phase (must be judged → finalized)
3.  Build LogicBeliefDelta per logic (expanded: threads_to_park, new_productive, new_failed)
4.  apply_belief_delta() per logic
5.  write_reflection_md() per logic (structural safety net, skip if already written)
6.  record_batch_usage_from_sources() via LedgerStore
7.  recompute_research_state()
8.  Update state (current_batch=None, last_completed=batch_id)
9.  Close superseded holdout entries (conservative: by candidate_id or logic+family)
10. Update batch_usage phase to "finalized"
11. Append audit entry
12. Run consistency check (soft fail)
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from research.domain.batch_phases import validate_phase_transition
from research.governance.holdout_queue import HoldoutQueue
from research.logic.reflect import (
    LogicBeliefDelta,
    apply_belief_delta,
    recompute_research_state,
    write_reflection_md,
)
from research.storage.consistency import StorageConsistencyChecker
from research.storage.ledger_store import LedgerStore
from research.storage.paths import StoragePaths
from research.storage.result_store import ResultStore
from research.storage.state_store import StateStore
from research.storage.yaml_io import load_yaml

logger = logging.getLogger(__name__)


@dataclass
class FinalizeResult:
    batch_id: str
    updated_logic_ids: list[str]
    active_logic_ids: list[str]
    warm_logic_ids: list[str]
    schedulable_logic_ids: list[str] = field(default_factory=list)
    consistency_ok: bool = True
    consistency_errors: list[str] = field(default_factory=list)
    batch_phase: str = "finalized"

    def to_dict(self) -> dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "updated_logic_ids": list(self.updated_logic_ids),
            "active_logic_ids": list(self.active_logic_ids),
            "warm_logic_ids": list(self.warm_logic_ids),
            "schedulable_logic_ids": list(self.schedulable_logic_ids),
            "consistency_ok": self.consistency_ok,
            "consistency_errors": list(self.consistency_errors),
            "batch_phase": self.batch_phase,
        }


class BatchFinalizer:
    """Apply a judged batch's decisions to persistent cognitive state."""

    def __init__(self, paths: StoragePaths | None = None) -> None:
        self._paths = paths or StoragePaths()
        self._results = ResultStore(self._paths)
        self._state = StateStore(self._paths)
        self._ledger = LedgerStore(self._paths)

    def finalize_batch(self, batch_id: str) -> FinalizeResult:
        # 1. Load judge_report
        report = self._results.load_judge_report(batch_id)
        if not report:
            raise FileNotFoundError(f"judge_report missing for {batch_id}")

        # 2. Validate phase transition
        bu = self._ledger.load_batch_usage().get("batches", {})
        current_phase = bu.get(batch_id, {}).get("phase", "judged")
        if current_phase != "finalized":
            try:
                validate_phase_transition(current_phase, "finalized")
            except ValueError:
                logger.warning(
                    "Phase transition %s→finalized not standard, proceeding anyway",
                    current_phase,
                )

        # 3. Build deltas
        diagnostics = _logic_mapping(report.get("logic_diagnostics", {}))
        recommendations = _logic_mapping(report.get("logic_recommendations", {}))
        candidate_verdicts = report.get("candidate_verdicts", [])
        candidate_counts = _candidate_counts(candidate_verdicts)

        # 4. Apply belief deltas + 5. Write reflections
        updated_logic_ids: list[str] = []
        deltas: list[LogicBeliefDelta] = []
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
                candidate_verdicts=candidate_verdicts,
            )
            apply_belief_delta(card_path, delta)
            updated_logic_ids.append(logic_id)
            deltas.append(delta)

        # 5. Write reflection markdown (structural safety net)
        for delta in deltas:
            reflection_path = self._paths.logic_reflection_file(delta.logic_id)
            # Guard: skip if this batch's header already exists
            if reflection_path.exists():
                content = reflection_path.read_text(encoding="utf-8")
                if f"## Batch {batch_id}" in content:
                    continue
            narrative = _build_structural_narrative(delta, diagnostics.get(delta.logic_id, {}))
            write_reflection_md(reflection_path, delta, narrative)

        # 6. Record batch_usage
        manifest = load_yaml(self._paths.batch_manifest_file(batch_id))
        packet_path = self._paths.judge_packet_file(batch_id)
        packet = load_yaml(packet_path) if packet_path.exists() else None
        self._ledger.record_batch_usage_from_sources(
            batch_id, manifest,
            judge_report=report,
            judge_packet=packet,
            phase="finalized",
        )

        # 7. Recompute research state
        state = recompute_research_state(self._paths.logic_cards_dir, self._state)

        # 8. Update state
        state = self._state.update_state(
            {
                "current_batch": None,
                "current_batch_phase": "finalized",
                "last_completed_batch": batch_id,
            }
        )

        # 9. Close superseded holdout entries (conservative)
        self._close_superseded_holdouts(batch_id, candidate_verdicts)

        # 10. Update batch_usage phase
        self._ledger.update_batch_phase(batch_id, "finalized")

        # 11. Audit entry
        self._ledger.append_audit_entry(
            actor="research.finalize",
            action="finalize_batch",
            target=batch_id,
            detail=f"updated_logics={','.join(updated_logic_ids)}",
        )

        # 12. Consistency check (soft)
        consistency_errors: list[str] = []
        consistency_ok = True
        try:
            checker = StorageConsistencyChecker(self._paths)
            cr = checker.check(batch_id=batch_id)
            consistency_errors = cr.errors
            consistency_ok = cr.ok
            if not cr.ok:
                for err in cr.errors:
                    logger.warning("Consistency: %s", err)
        except Exception as e:
            logger.warning("Consistency check failed: %s", e)
            consistency_errors = [str(e)]
            consistency_ok = False

        return FinalizeResult(
            batch_id=batch_id,
            updated_logic_ids=updated_logic_ids,
            active_logic_ids=list(state.get("active_logic_ids", [])),
            warm_logic_ids=list(state.get("warm_logic_ids", [])),
            schedulable_logic_ids=list(state.get("schedulable_logic_ids", [])),
            consistency_ok=consistency_ok,
            consistency_errors=consistency_errors,
            batch_phase="finalized",
        )

    def _close_superseded_holdouts(
        self,
        batch_id: str,
        candidate_verdicts: list[dict[str, Any]],
    ) -> None:
        """Close holdout entries for candidates with definitive verdicts.

        Conservative rule:
        - Match by candidate_id directly, OR
        - Match by (logic_id + family_id) where the entry is an older pending
          and this batch has a definitive verdict (admit/reject/replace/kill).
        """
        definitive = {"admit", "reject", "replace", "kill"}
        # Build lookup: (logic_id, family_id) → has definitive verdict
        verdict_keys: set[tuple[str, str]] = set()
        verdict_candidates: set[str] = set()
        for v in candidate_verdicts:
            if not isinstance(v, dict):
                continue
            if str(v.get("verdict", "")) in definitive:
                lid = str(v.get("logic_id", ""))
                fid = str(v.get("family_id", ""))
                cid = str(v.get("candidate_id", ""))
                if lid and fid:
                    verdict_keys.add((lid, fid))
                if cid:
                    verdict_candidates.add(cid)

        if not verdict_keys and not verdict_candidates:
            return

        queue = HoldoutQueue.load_yaml(str(self._paths.pending_holdout_queue_file))
        changed = False
        for entry in queue.entries:
            if entry.status != "pending":
                continue
            # Match by candidate_id
            if entry.candidate_id in verdict_candidates:
                entry.status = "superseded"
                changed = True
                continue
            # Match by logic_id + family_id (conservative)
            if entry.logic_id and entry.family_id:
                if (entry.logic_id, entry.family_id) in verdict_keys:
                    # Only supersede if from an older batch
                    if entry.batch_id != batch_id:
                        entry.status = "superseded"
                        changed = True

        if changed:
            queue.save_yaml(str(self._paths.pending_holdout_queue_file))
            actual_pending = len(queue.pending())
            self._state.update_state({"pending_holdout_count": actual_pending})


def _build_structural_narrative(
    delta: LogicBeliefDelta, diagnostics: dict[str, Any]
) -> str:
    """Build a minimal narrative from delta + diagnostics for the structural reflection."""
    parts: list[str] = []
    thesis = diagnostics.get("thesis_update", "")
    if thesis:
        parts.append(f"Thesis update: {thesis}")
    boundary = diagnostics.get("failure_boundary", "")
    if boundary:
        parts.append(f"Failure boundary: {boundary}")
    if not parts:
        parts.append("[Structural reflection — no detailed narrative available]")
    return "\n".join(parts)


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
    candidate_verdicts: list[dict[str, Any]],
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

    # NEW: threads_to_park — when transitioning to terminal status, park all active threads
    threads_to_park: list[str] = []
    terminal = {"parked", "saturated", "dead"}
    if status_change and status_change in terminal:
        for t in card.get("deepening_threads", []):
            if isinstance(t, dict) and t.get("status") == "active":
                tid = t.get("id", "")
                if tid:
                    threads_to_park.append(tid)

    # NEW: new_productive and new_failed from candidate verdicts
    new_productive: list[dict] = []
    new_failed: list[dict] = []
    for v in candidate_verdicts:
        if not isinstance(v, dict):
            continue
        if str(v.get("logic_id", "")) != logic_id:
            continue
        verdict = str(v.get("verdict", ""))
        fid = str(v.get("family_id", ""))
        if verdict in ("admit", "replace"):
            new_productive.append({"family_id": fid, "batch_id": batch_id})
        elif verdict in ("reject", "kill"):
            reason = str(v.get("reason", v.get("reject_reason", "")))
            new_failed.append({"family_id": fid, "reason": reason})

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
        threads_to_park=threads_to_park,
        new_productive=new_productive,
        new_failed=new_failed,
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
