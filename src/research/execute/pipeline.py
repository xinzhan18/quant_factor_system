"""Research execute pipeline: the main orchestrator.

Pipeline steps per candidate:

    precheck → compute_signal → preprocess (+ factor_flat)
    → stat_evidence → redundancy → risk_review → feasibility
    → execution_gate → support_window_review → holdout_review
    → judge packet build

All heavy computation is delegated to injected callables.
BatchSharedData is pre-fetched once via prepare_batch before the candidate loop.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional

from .config import EvaluationProfile, load_evaluation_profile, load_sample_policy
from .precheck import run_precheck
from .execution_gate import ExecutionGate, GateResult
from .judge_packet_builder import JudgePacketBuilder

logger = logging.getLogger(__name__)


class ResearchExecutePipeline:
    """Orchestrate the research execute pipeline for a batch of candidates."""

    def __init__(
        self,
        profile: Optional[EvaluationProfile] = None,
        sample_policy: Optional[Dict[str, Any]] = None,
        compute_signal: Optional[Callable] = None,
        preprocess_signal: Optional[Callable] = None,
        compute_stat_evidence: Optional[Callable] = None,
        compute_redundancy: Optional[Callable] = None,
        compute_feasibility: Optional[Callable] = None,
        risk_engine: Optional[Any] = None,
        prepare_batch: Optional[Callable] = None,
    ):
        self.profile = profile or load_evaluation_profile()
        self.sample_policy = sample_policy or load_sample_policy()
        self._compute_signal = compute_signal
        self._preprocess_signal = preprocess_signal
        self._compute_stat_evidence = compute_stat_evidence
        self._compute_redundancy = compute_redundancy
        self._compute_feasibility = compute_feasibility
        self._risk_engine = risk_engine
        self._prepare_batch = prepare_batch
        self._gate = ExecutionGate()
        self._packet_builder = JudgePacketBuilder()

    # ----- single candidate -----------------------------------------------
    def execute_candidate(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the full pipeline for a single candidate."""
        cid = candidate.get("candidate_id") or candidate.get("name", "unknown")
        logger.info("Executing candidate %s", cid)

        # Carry forward ALL manifest fields so nothing is lost
        result: Dict[str, Any] = {
            "candidate_id": cid,
            "name": candidate.get("name", cid),
            "expression": candidate.get("expression", ""),
            "direction": candidate.get("direction"),
            "logic_id": candidate.get("logic_id"),
            "route_id": candidate.get("route_id"),
            "experiment_lineage_tag": candidate.get("experiment_lineage_tag"),
            "family_id": candidate.get("family_id"),
            "route_type": candidate.get("route_type"),
            "source_type": candidate.get("source_type", "dsl"),
            "rationale": candidate.get("rationale"),
            "probe_ic": candidate.get("probe_ic"),
        }

        # Step 1: Precheck
        precheck = run_precheck(candidate)
        result["precheck"] = precheck.to_dict()

        if not precheck.passed:
            logger.info("Candidate %s failed precheck: %s", cid, precheck.reason_codes)
            result.update(self._empty_evaluation_sections())
            gate = self._gate.evaluate(result)
            result["execution_gate"] = gate.to_dict()
            result["search_context"] = {}
            result["holdout_review"] = {"recommended": False, "trigger_reason_codes": []}
            result["support_window_review"] = {"support_window_warning": "none"}
            return result

        # Step 2: Compute base signal
        base = self._compute_signal(candidate, self.profile)
        result["diagnostics"] = base.get("diagnostics", {})

        # Step 3: Preprocessing → evaluation_ready_signal + factor_flat
        signal = self._preprocess_signal(base, self.profile)

        # Step 4: Statistical evidence
        evaluation = self._compute_stat_evidence(signal, self.sample_policy)
        result["evaluation"] = evaluation

        # Step 5: Redundancy
        similarity = self._compute_redundancy(signal, candidate)
        result["similarity"] = similarity

        # Step 6: Risk model review
        if self._risk_engine is not None:
            eval_signal = signal.get("evaluation_ready_signal")
            factor_flat = signal.get("factor_flat")
            if eval_signal is not None:
                risk_obj = self._risk_engine.compute_risk_review(
                    eval_signal, self.sample_policy, self.profile,
                    factor_flat=factor_flat,
                )
                result["risk_review"] = risk_obj.to_dict()
            else:
                from research.risk.schema import RiskReview
                result["risk_review"] = RiskReview.stub().to_dict()
        else:
            from research.risk.schema import RiskReview
            result["risk_review"] = RiskReview.stub().to_dict()

        # Step 7: Feasibility
        feasibility = self._compute_feasibility(signal)
        result["feasibility"] = feasibility

        # Step 8: Execution gate
        gate = self._gate.evaluate(result)
        result["execution_gate"] = gate.to_dict()

        # Step 9: Support window review
        result["support_window_review"] = _compute_support_window_review(evaluation)

        # Step 10: Holdout review trigger
        result["holdout_review"] = _should_recommend_holdout(
            evaluation, similarity, gate
        )

        return result

    # ----- analysis (thread-safe, no Qlib) ---------------------------------
    def _analyze_candidate(
        self,
        candidate: Dict[str, Any],
        precheck,
        signal: Optional[Dict[str, Any]],
        base: Optional[Dict[str, Any]],
        search_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run steps 4-10 for a single candidate. Thread-safe (no Qlib calls)."""
        cid = candidate.get("candidate_id") or candidate.get("name", "unknown")

        result: Dict[str, Any] = {
            "candidate_id": cid,
            "name": candidate.get("name", cid),
            "expression": candidate.get("expression", ""),
            "direction": candidate.get("direction"),
            "logic_id": candidate.get("logic_id"),
            "route_id": candidate.get("route_id"),
            "experiment_lineage_tag": candidate.get("experiment_lineage_tag"),
            "family_id": candidate.get("family_id"),
            "route_type": candidate.get("route_type"),
            "source_type": candidate.get("source_type", "dsl"),
            "rationale": candidate.get("rationale"),
            "probe_ic": candidate.get("probe_ic"),
        }

        result["precheck"] = precheck.to_dict()

        if not precheck.passed:
            result.update(self._empty_evaluation_sections())
            gate = self._gate.evaluate(result)
            result["execution_gate"] = gate.to_dict()
            result["search_context"] = search_context or {}
            result["holdout_review"] = {"recommended": False, "trigger_reason_codes": []}
            result["support_window_review"] = {"support_window_warning": "none"}
            return result

        result["diagnostics"] = base.get("diagnostics", {}) if base else {}

        # Step 4: Statistical evidence
        evaluation = self._compute_stat_evidence(signal, self.sample_policy)
        result["evaluation"] = evaluation

        # Step 5: Redundancy
        similarity = self._compute_redundancy(signal, candidate)
        result["similarity"] = similarity

        # Step 6: Risk model review
        if self._risk_engine is not None:
            eval_signal = signal.get("evaluation_ready_signal") if signal else None
            factor_flat = signal.get("factor_flat") if signal else None
            if eval_signal is not None:
                risk_obj = self._risk_engine.compute_risk_review(
                    eval_signal, self.sample_policy, self.profile,
                    factor_flat=factor_flat,
                )
                result["risk_review"] = risk_obj.to_dict()
            else:
                from research.risk.schema import RiskReview
                result["risk_review"] = RiskReview.stub().to_dict()
        else:
            from research.risk.schema import RiskReview
            result["risk_review"] = RiskReview.stub().to_dict()

        # Step 7: Feasibility
        result["feasibility"] = self._compute_feasibility(signal)

        # Step 8: Execution gate
        gate = self._gate.evaluate(result)
        result["execution_gate"] = gate.to_dict()

        # Step 9: Support window review
        result["support_window_review"] = _compute_support_window_review(evaluation)

        # Step 10: Holdout review trigger
        result["holdout_review"] = _should_recommend_holdout(evaluation, similarity, gate)

        result["search_context"] = search_context or {}
        return result

    # ----- batch -----------------------------------------------------------
    def execute_batch(
        self,
        batch_id: str,
        candidates: List[Dict[str, Any]],
        search_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute the pipeline for an entire batch."""
        logger.info("Executing batch %s with %d candidates", batch_id, len(candidates))

        # Pre-fetch shared data for the batch
        if self._prepare_batch is not None:
            self._prepare_batch(self.sample_policy, self._risk_engine)

        # Phase A: compute signals sequentially (Qlib not thread-safe)
        signals: List[Dict[str, Any]] = []
        for candidate in candidates:
            cid = candidate.get("candidate_id") or candidate.get("name", "unknown")
            precheck = run_precheck(candidate)
            if not precheck.passed:
                signals.append({"candidate": candidate, "precheck": precheck, "signal": None, "base": None})
                continue
            base = self._compute_signal(candidate, self.profile)
            signal = self._preprocess_signal(base, self.profile)
            signals.append({"candidate": candidate, "precheck": precheck, "signal": signal, "base": base})

        # Phase B: analyze in parallel (pure numpy, no Qlib)
        from concurrent.futures import ThreadPoolExecutor

        def _analyze(item: Dict[str, Any]) -> Dict[str, Any]:
            return self._analyze_candidate(
                item["candidate"], item["precheck"], item["signal"], item["base"],
                search_context,
            )

        with ThreadPoolExecutor(max_workers=min(len(candidates), 4)) as pool:
            candidate_results = list(pool.map(_analyze, signals))

        # Build judge packet
        packet = self._packet_builder.build(
            batch_id=batch_id,
            candidate_results=candidate_results,
            search_context=search_context,
            sample_policy_version=self.sample_policy.get(
                "validation_policy_version", "research_sample_v3"
            ),
            evaluation_profile_id=self.profile.get("profile_id", "research_eval_v1"),
        )

        summary = self._build_summary(candidate_results)

        return {
            "batch_id": batch_id,
            "sample_policy": dict(self.sample_policy),
            "evaluation_profile_id": self.profile.get("profile_id", "research_eval_v1"),
            "candidate_results": candidate_results,
            "judge_packet": packet,
            "summary": summary,
        }

    # ----- helpers ---------------------------------------------------------
    @staticmethod
    def _empty_evaluation_sections() -> Dict[str, Any]:
        return {
            "diagnostics": {},
            "evaluation": {},
            "similarity": {},
            "risk_review": {},
            "feasibility": {},
        }

    @staticmethod
    def _build_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        total = len(results)
        precheck_failed = sum(
            1 for r in results if r.get("precheck", {}).get("status") == "failed"
        )
        gate_pass = sum(
            1 for r in results if r.get("execution_gate", {}).get("status") == "pass"
        )
        gate_warn = sum(
            1 for r in results if r.get("execution_gate", {}).get("status") == "warn"
        )
        gate_fail = sum(
            1 for r in results if r.get("execution_gate", {}).get("status") == "fail_technical"
        )
        return {
            "total_candidates": total,
            "precheck_failed": precheck_failed,
            "gate_pass": gate_pass,
            "gate_warn": gate_warn,
            "gate_fail_technical": gate_fail,
        }


# ---------------------------------------------------------------------------
# Holdout review trigger
# ---------------------------------------------------------------------------

def _should_recommend_holdout(
    evaluation: Dict[str, Any],
    similarity: Dict[str, Any],
    gate: GateResult,
) -> Dict[str, Any]:
    trigger_codes: List[str] = []

    mt_bucket = evaluation.get("multiple_testing_risk_bucket", "low")
    effect_strong = (
        abs(evaluation.get("ic_mean_validation", 0) or 0) >= 0.015
        and abs(evaluation.get("ic_ir_validation", 0) or 0) >= 0.15
    )
    redundancy_low = abs(similarity.get("max_lib_corr", 0) or 0) < 0.40

    if effect_strong and redundancy_low:
        trigger_codes.append("high_confidence_candidate")
    if mt_bucket == "high" and effect_strong:
        trigger_codes.append("high_mining_risk_but_strong_validation")

    # If holdout was actually computed, add holdout-specific trigger codes
    ic_ho = evaluation.get("ic_mean_holdout")
    if ic_ho is not None:
        icir_ho = abs(evaluation.get("ic_ir_holdout", 0) or 0)
        ic_ho_abs = abs(ic_ho)
        if ic_ho_abs >= 0.01 and icir_ho >= 0.10:
            trigger_codes.append("holdout_confirms_signal")
        elif ic_ho_abs < 0.005:
            trigger_codes.append("holdout_signal_vanished")

    recommended = len(trigger_codes) > 0 and gate.status != "fail_technical"
    return {
        "recommended": recommended,
        "trigger_reason_codes": trigger_codes,
    }


def _compute_support_window_review(evaluation: Dict[str, Any]) -> Dict[str, Any]:
    checks = evaluation.get("support_window_checks", [])
    flip_count = sum(
        1 for c in checks if not c.get("sign_consistency_support", True)
    )
    if flip_count >= 2:
        warning = "repeated_sign_flip"
    elif flip_count == 1:
        warning = "single_window_flip"
    else:
        warning = "none"
    return {"support_window_warning": warning}
