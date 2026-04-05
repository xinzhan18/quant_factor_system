"""Research execute pipeline: the main orchestrator.

This is the formal evidence-generation layer of the research system.
It processes a batch of frozen candidates through a deterministic sequence
of steps and produces structured results plus a compressed judge packet.

Pipeline steps (per ``docs/refacor_logic/research_execute.md``):

    precheck
    -> base_signal computation
    -> preprocessing (primary pipeline)
    -> statistical evidence
       - effect strength
       - stability
       - statistical reliability
       - support window checks
    -> redundancy analysis
    -> risk model review
    -> feasibility analysis
    -> execution gate
    -> search context assembly
    -> holdout review trigger
    -> judge packet build

Sibling compute/stats/redundancy/feasibility modules are still under
parallel development; this module defines their expected interfaces and
accepts callables via dependency injection so they can be mocked in tests.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Optional, Protocol

from .config import EvaluationProfile, load_evaluation_profile, load_sample_policy
from .precheck import PrecheckResult, run_precheck
from .execution_gate import ExecutionGate, GateResult
from .judge_packet_builder import JudgePacketBuilder

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocols for sibling modules (dependency injection boundaries)
# ---------------------------------------------------------------------------
class ComputeSignal(Protocol):
    """Compute the base signal for a candidate."""

    def __call__(self, candidate: Dict[str, Any], profile: EvaluationProfile) -> Dict[str, Any]:
        """Return ``{"base_signal": ..., "diagnostics": {...}}``."""
        ...


class PreprocessSignal(Protocol):
    """Apply the primary preprocessing pipeline to a base signal."""

    def __call__(self, base_result: Dict[str, Any], profile: EvaluationProfile) -> Dict[str, Any]:
        """Return ``{"evaluation_ready_signal": ...}``."""
        ...


class ComputeStatEvidence(Protocol):
    """Compute statistical evidence on the evaluation-ready signal."""

    def __call__(
        self,
        signal_result: Dict[str, Any],
        sample_policy: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Return evaluation dict with effect, stability, reliability keys."""
        ...


class ComputeRedundancy(Protocol):
    """Compute redundancy (pairwise, family, subspace) against the library."""

    def __call__(self, signal_result: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Return similarity dict."""
        ...


class ComputeRiskReview(Protocol):
    """DEPRECATED — use RiskEngine injection instead.

    Kept only for backward compat during transition; will be removed.
    """

    def __call__(self, signal_result: Dict[str, Any], profile: EvaluationProfile) -> Dict[str, Any]:
        """Return risk_review dict."""
        ...


class ComputeFeasibility(Protocol):
    """Compute implementation feasibility proxy metrics."""

    def __call__(self, signal_result: Dict[str, Any]) -> Dict[str, Any]:
        """Return feasibility dict."""
        ...


# ---------------------------------------------------------------------------
# Default stubs (used when real implementations are not yet available)
# ---------------------------------------------------------------------------
def _stub_compute(candidate: Dict[str, Any], profile: EvaluationProfile) -> Dict[str, Any]:
    return {
        "base_signal": None,
        "diagnostics": {
            "base_valid_ratio": 0.90,
            "base_variance": 1.0,
            "base_outlier_ratio": 0.05,
            "base_skew": 0.0,
            "base_kurtosis": 3.0,
        },
    }


def _stub_preprocess(base_result: Dict[str, Any], profile: EvaluationProfile) -> Dict[str, Any]:
    return {"evaluation_ready_signal": None}


def _stub_stat_evidence(signal_result: Dict[str, Any], sample_policy: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ic_mean_train": 0.0,
        "ic_ir_train": 0.0,
        "ic_mean_validation": 0.0,
        "ic_ir_validation": 0.0,
        "ic_win_rate_validation": 0.50,
        "monotonicity_validation": 0.0,
        "sign_consistency": True,
        "train_validation_decay_ratio": 1.0,
        "split_stability": "medium",
        "regime_stability": "medium",
        "horizon_consistency": "medium",
        "expanding_window_ic_stability": 0.50,
        "expanding_window_sign_consistency": 0.50,
        "expanding_window_pass": True,
        "bootstrap_stability_score": None,
        "bootstrap_sign_consistency": None,
        "purged_walk_forward_score": None,
        "purged_walk_forward_status": None,
        "multiple_testing_risk_bucket": "low",
        "search_adjusted_strength_bucket": "medium",
        "support_window_checks": [],
    }


def _stub_redundancy(signal_result: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "max_lib_corr": 0.0,
        "nearest_factor_id": None,
        "family_overlap_score": 0.0,
        "subspace_redundancy_score": 0.0,
        "residual_incremental_ic": 0.0,
        "replacement_candidate_hint": False,
        "family_redundancy_view": {},
        "subspace_redundancy_view": {},
    }


def _stub_risk_review_dict() -> Dict[str, Any]:
    """Default stub risk review — used when no RiskEngine is injected."""
    from research.risk.schema import RiskReview
    return RiskReview.stub().to_dict()


def _stub_feasibility(signal_result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "turnover": 0.30,
        "coverage": 0.90,
        "half_life": 5.0,
        "holding_period_proxy": "medium",
        "liquidity_coverage_ratio": 0.80,
        "tail_trade_concentration": 0.15,
        "small_cap_concentration": 0.25,
        "rebalance_stress_proxy": "low",
    }


# ---------------------------------------------------------------------------
# Holdout review trigger
# ---------------------------------------------------------------------------
def _should_recommend_holdout(
    evaluation: Dict[str, Any],
    similarity: Dict[str, Any],
    gate: GateResult,
) -> Dict[str, Any]:
    """Determine whether holdout review should be recommended.

    Rules (from ``research_execute.md`` section 11):
    1. Strong stats + low redundancy + low style residual
    2. multiple_testing_risk_bucket = high but validation looks strong
    3. Potential policy/forbidden upgrade impact
    """
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

    recommended = len(trigger_codes) > 0 and gate.status != "fail_technical"
    return {
        "recommended": recommended,
        "trigger_reason_codes": trigger_codes,
    }


# ---------------------------------------------------------------------------
# Support window review
# ---------------------------------------------------------------------------
def _compute_support_window_review(evaluation: Dict[str, Any]) -> Dict[str, Any]:
    """Derive the aggregated support_window_warning from support checks."""
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


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------
class ResearchExecutePipeline:
    """Orchestrate the research execute pipeline for a batch of candidates.

    All heavy computation is delegated to injected callables so that
    the orchestrator can be tested with mocks while sibling modules are
    developed in parallel.
    """

    def __init__(
        self,
        profile: Optional[EvaluationProfile] = None,
        sample_policy: Optional[Dict[str, Any]] = None,
        compute_signal: Optional[ComputeSignal] = None,
        preprocess_signal: Optional[PreprocessSignal] = None,
        compute_stat_evidence: Optional[ComputeStatEvidence] = None,
        compute_redundancy: Optional[ComputeRedundancy] = None,
        compute_risk_review: Optional[ComputeRiskReview] = None,
        compute_feasibility: Optional[ComputeFeasibility] = None,
        risk_engine: Optional[Any] = None,
    ):
        self.profile = profile or load_evaluation_profile()
        self.sample_policy = sample_policy or load_sample_policy()
        self._compute_signal = compute_signal or _stub_compute
        self._preprocess_signal = preprocess_signal or _stub_preprocess
        self._compute_stat_evidence = compute_stat_evidence or _stub_stat_evidence
        self._compute_redundancy = compute_redundancy or _stub_redundancy
        self._compute_feasibility = compute_feasibility or _stub_feasibility
        self._risk_engine = risk_engine
        # Legacy callable fallback (will be removed)
        self._compute_risk_review_legacy = compute_risk_review
        self._gate = ExecutionGate()
        self._packet_builder = JudgePacketBuilder()

    # ----- single candidate -----------------------------------------------
    def execute_candidate(self, candidate: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the full pipeline for a single candidate.

        Returns a result dict conforming to the schema in
        ``research_execute.md`` section 12.1.
        """
        cid = candidate.get("candidate_id", "unknown")
        logger.info("Executing candidate %s", cid)

        result: Dict[str, Any] = {
            "candidate_id": cid,
            "logic_id": candidate.get("logic_id"),
            "route_id": candidate.get("route_id"),
            "experiment_lineage_tag": candidate.get("experiment_lineage_tag"),
            "family_id": candidate.get("family_id"),
            "route_type": candidate.get("route_type"),
            "source_type": candidate.get("source_type", "dsl"),
            "sample_policy": dict(self.sample_policy),
        }

        # Step 1: Precheck
        precheck = run_precheck(candidate)
        result["precheck"] = precheck.to_dict()

        if not precheck.passed:
            logger.info("Candidate %s failed precheck: %s", cid, precheck.reason_codes)
            # Fill with empty sections so downstream consumers have stable keys
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

        # Step 3: Preprocessing (primary pipeline)
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
            if eval_signal is not None:
                risk_obj = self._risk_engine.compute_risk_review(
                    eval_signal, self.sample_policy, self.profile,
                )
                result["risk_review"] = risk_obj.to_dict()
            else:
                result["risk_review"] = _stub_risk_review_dict()
        elif self._compute_risk_review_legacy is not None:
            result["risk_review"] = self._compute_risk_review_legacy(signal, self.profile)
        else:
            result["risk_review"] = _stub_risk_review_dict()

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

    # ----- batch -----------------------------------------------------------
    def execute_batch(
        self,
        batch_id: str,
        candidates: List[Dict[str, Any]],
        search_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute the pipeline for an entire batch.

        Returns a ``BatchExecuteResult`` dict containing:
        - ``batch_id``
        - ``candidate_results``: list of per-candidate result dicts
        - ``judge_packet``: compressed packet for research_judge
        - ``summary``: high-level statistics
        """
        logger.info("Executing batch %s with %d candidates", batch_id, len(candidates))

        candidate_results: List[Dict[str, Any]] = []
        for candidate in candidates:
            result = self.execute_candidate(candidate)
            # Attach search context per candidate
            result["search_context"] = search_context or {}
            candidate_results.append(result)

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

        # Build summary
        summary = self._build_summary(candidate_results)

        return {
            "batch_id": batch_id,
            "candidate_results": candidate_results,
            "judge_packet": packet,
            "summary": summary,
        }

    # ----- helpers ---------------------------------------------------------
    @staticmethod
    def _empty_evaluation_sections() -> Dict[str, Any]:
        """Return empty-but-keyed sections for a failed precheck candidate."""
        return {
            "diagnostics": {},
            "evaluation": {},
            "similarity": {},
            "risk_review": {},
            "feasibility": {},
        }

    @staticmethod
    def _build_summary(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Produce a high-level summary of the batch execution."""
        total = len(results)
        precheck_failed = sum(
            1 for r in results if r.get("precheck", {}).get("status") == "failed"
        )
        gate_pass = sum(
            1 for r in results
            if r.get("execution_gate", {}).get("status") == "pass"
        )
        gate_warn = sum(
            1 for r in results
            if r.get("execution_gate", {}).get("status") == "warn"
        )
        gate_fail = sum(
            1 for r in results
            if r.get("execution_gate", {}).get("status") == "fail_technical"
        )
        return {
            "total_candidates": total,
            "precheck_failed": precheck_failed,
            "gate_pass": gate_pass,
            "gate_warn": gate_warn,
            "gate_fail_technical": gate_fail,
        }
