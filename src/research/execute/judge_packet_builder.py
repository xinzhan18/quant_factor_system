"""Judge packet builder: compress execution results for the research judge.

The judge packet is the *primary* input to ``research_judge``.  It contains
only the compressed evidence the judge needs to make structured verdicts.
Full timeseries, raw signals, and report-specific chart data are excluded.

Design reference: ``docs/refacor_logic/research_execute.md`` section 12.3
and ``docs/refacor_logic/research_judge.md`` section 2.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Bucket helpers
# ---------------------------------------------------------------------------
def _effect_bucket(evaluation: Dict[str, Any]) -> str:
    """Classify validation effect strength into strong / borderline / weak."""
    ic = abs(evaluation.get("ic_mean_validation", 0) or 0)
    ic_ir = abs(evaluation.get("ic_ir_validation", 0) or 0)
    mono = abs(evaluation.get("monotonicity_validation", 0) or 0)

    # Strong: clear IC, decent IR, good monotonicity
    if ic >= 0.015 and ic_ir >= 0.15 and mono >= 0.30:
        return "strong"
    # Weak: one or more metrics clearly below threshold
    if ic < 0.008 or ic_ir < 0.05:
        return "weak"
    return "borderline"


def _stability_bucket(evaluation: Dict[str, Any]) -> str:
    """Classify stability into good / medium / poor."""
    split = evaluation.get("split_stability", "medium")
    regime = evaluation.get("regime_stability", "medium")
    ew_pass = evaluation.get("expanding_window_pass", True)

    if split == "high" and regime == "high" and ew_pass:
        return "good"
    if split == "low" or regime == "low" or not ew_pass:
        return "poor"
    return "medium"


def _redundancy_bucket(similarity: Dict[str, Any]) -> str:
    """Classify redundancy into low / medium / high."""
    max_corr = abs(similarity.get("max_lib_corr", 0) or 0)
    family_bucket = similarity.get("family_redundancy_view", {}).get(
        "overlap_bucket", "low"
    )

    if max_corr >= 0.85 or family_bucket == "high":
        return "high"
    if max_corr >= 0.60 or family_bucket == "medium":
        return "medium"
    return "low"


def _feasibility_bucket(feasibility: Dict[str, Any]) -> str:
    """Classify feasibility into good / acceptable / poor."""
    stress = feasibility.get("rebalance_stress_proxy", "low")
    liq_ratio = feasibility.get("liquidity_coverage_ratio")
    turnover = feasibility.get("turnover")

    if stress == "high":
        return "poor"
    if stress == "medium":
        return "acceptable"
    # Check individual metrics
    if liq_ratio is not None and liq_ratio < 0.30:
        return "poor"
    if turnover is not None and turnover > 1.5:
        return "acceptable"
    return "good"


# ---------------------------------------------------------------------------
# Candidate brief builder
# ---------------------------------------------------------------------------
def _build_candidate_brief(result: Dict[str, Any]) -> Dict[str, Any]:
    """Compress a single candidate result into a brief for the judge."""
    evaluation = result.get("evaluation", {})
    similarity = result.get("similarity", {})
    feasibility = result.get("feasibility", {})
    gate = result.get("execution_gate", {})
    holdout = result.get("holdout_review", {})
    support_review = result.get("support_window_review", {})

    risk_review = result.get("risk_review", {})

    return {
        "candidate_id": result.get("candidate_id"),
        "logic_id": result.get("logic_id"),
        "route_id": result.get("route_id"),
        "route_type": result.get("route_type"),
        "family_id": result.get("family_id"),
        "experiment_lineage_tag": result.get("experiment_lineage_tag"),
        "execution_gate_status": gate.get("status", "pass"),
        "validation_effect_bucket": _effect_bucket(evaluation),
        "stability_bucket": _stability_bucket(evaluation),
        "redundancy_bucket": _redundancy_bucket(similarity),
        "feasibility_bucket": _feasibility_bucket(feasibility),
        "risk_model_review_bucket": risk_review.get(
            "risk_model_review_bucket", "acceptable"
        ),
        "support_window_warning": support_review.get(
            "support_window_warning", "none"
        ),
        "holdout_review_recommended": holdout.get("recommended", False),
    }


# ---------------------------------------------------------------------------
# JudgePacketBuilder
# ---------------------------------------------------------------------------
class JudgePacketBuilder:
    """Build a judge packet from a batch of candidate results."""

    def build(
        self,
        batch_id: str,
        candidate_results: List[Dict[str, Any]],
        search_context: Optional[Dict[str, Any]] = None,
        sample_policy_version: str = "research_sample_v3",
        evaluation_profile_id: str = "research_eval_v1",
    ) -> Dict[str, Any]:
        """Assemble the judge packet.

        Parameters
        ----------
        batch_id:
            Batch identifier (e.g. ``"batch_042"``).
        candidate_results:
            List of per-candidate result dicts produced by the pipeline.
        search_context:
            Aggregated search context (validation exposure, per-logic
            and per-family attempt counts).
        sample_policy_version:
            Version tag for the sample policy in effect.
        evaluation_profile_id:
            Profile id for the evaluation profile in effect.

        Returns
        -------
        dict
            A judge packet conforming to the schema in
            ``research_execute.md`` section 12.3.
        """
        briefs = [_build_candidate_brief(r) for r in candidate_results]

        # Derive active logic ids from the briefs
        active_logic_ids = sorted(
            {b["logic_id"] for b in briefs if b.get("logic_id")}
        )

        # Derive aggregated support_window_warning
        warnings = [b.get("support_window_warning", "none") for b in briefs]
        if "repeated_sign_flip" in warnings:
            agg_warning = "repeated_sign_flip"
        elif "single_window_flip" in warnings:
            agg_warning = "single_window_flip"
        else:
            agg_warning = "none"

        packet: Dict[str, Any] = {
            "judge_packet": {
                "batch_id": batch_id,
                "sample_policy_version": sample_policy_version,
                "evaluation_profile_id": evaluation_profile_id,
                "active_logic_ids": active_logic_ids,
                "candidate_briefs": briefs,
                "policy_snapshot_ref": {
                    "implementation_policy": "policy/implementation_policy.yaml",
                    "forbidden": "memory/forbidden.yaml",
                },
                "search_context": search_context or {},
                "support_window_review": {
                    "support_window_warning": agg_warning,
                },
            }
        }
        return packet
