"""Tests for research.execute.pipeline — the main orchestrator.

All sibling compute modules are mocked so these tests focus purely on
orchestration correctness:
- candidates flow through all steps in order
- failed prechecks skip evaluation
- execution gate classifies correctly
- batch result contains all expected keys
- judge packet is built and attached
"""

import pytest

from research.execute.pipeline import (
    ResearchExecutePipeline,
    _compute_support_window_review,
    _should_recommend_holdout,
)
from research.execute.execution_gate import GateResult


# ===================================================================
# Fixtures / helpers
# ===================================================================
def _dsl_candidate(cid="C001", expr="Rank($close)", **extra):
    base = {
        "candidate_id": cid,
        "logic_id": "L001",
        "route_id": "R001",
        "experiment_lineage_tag": "ELT_01",
        "family_id": "FM_test",
        "route_type": "genesis",
        "source_type": "dsl",
        "expression": expr,
    }
    base.update(extra)
    return base


def _bad_dsl_candidate(cid="C_BAD"):
    return _dsl_candidate(cid=cid, expr="Neg($vwap)")


def _make_custom_stat_evidence(ic_val=0.012, sign_ok=True, split="medium"):
    """Return a stat evidence callable that returns controllable values."""
    def _stat(signal, sample_policy):
        return {
            "ic_mean_train": 0.018,
            "ic_ir_train": 0.20,
            "ic_mean_validation": ic_val,
            "ic_ir_validation": 0.13,
            "ic_win_rate_validation": 0.55,
            "monotonicity_validation": 0.35,
            "sign_consistency": sign_ok,
            "train_validation_decay_ratio": 0.56 if sign_ok else -0.30,
            "split_stability": split,
            "regime_stability": "medium",
            "horizon_consistency": "medium",
            "expanding_window_ic_stability": 0.63,
            "expanding_window_sign_consistency": 0.71,
            "expanding_window_pass": True,
            "bootstrap_stability_score": 0.67,
            "bootstrap_sign_consistency": 0.81,
            "purged_walk_forward_score": None,
            "purged_walk_forward_status": None,
            "multiple_testing_risk_bucket": "medium",
            "search_adjusted_strength_bucket": "medium",
            "support_window_checks": [],
        }
    return _stat


# ===================================================================
# Single candidate execution
# ===================================================================
class TestExecuteCandidate:
    def test_passing_candidate_has_all_keys(self):
        pipeline = ResearchExecutePipeline()
        result = pipeline.execute_candidate(_dsl_candidate())

        required_keys = {
            "candidate_id", "logic_id", "route_id", "family_id",
            "source_type", "sample_policy", "precheck",
            "diagnostics", "evaluation", "similarity",
            "risk_review", "feasibility", "execution_gate",
            "support_window_review", "holdout_review",
        }
        assert required_keys.issubset(result.keys()), (
            f"Missing keys: {required_keys - result.keys()}"
        )

    def test_precheck_pass(self):
        pipeline = ResearchExecutePipeline()
        result = pipeline.execute_candidate(_dsl_candidate())
        assert result["precheck"]["status"] == "passed"

    def test_precheck_failed_skips_evaluation(self):
        pipeline = ResearchExecutePipeline()
        result = pipeline.execute_candidate(_bad_dsl_candidate())
        assert result["precheck"]["status"] == "failed"
        # Evaluation should be empty (skipped)
        assert result["evaluation"] == {}
        # But execution gate should still run and fail_technical
        assert result["execution_gate"]["status"] == "fail_technical"

    def test_custom_compute_signal_called(self):
        called = {"count": 0}
        def custom_compute(candidate, profile):
            called["count"] += 1
            return {
                "base_signal": "mock",
                "diagnostics": {
                    "base_valid_ratio": 0.85,
                    "base_variance": 1.2,
                    "base_outlier_ratio": 0.04,
                },
            }
        pipeline = ResearchExecutePipeline(compute_signal=custom_compute)
        result = pipeline.execute_candidate(_dsl_candidate())
        assert called["count"] == 1
        assert result["diagnostics"]["base_valid_ratio"] == 0.85

    def test_execution_gate_pass_with_stubs(self):
        """With default stubs, a valid DSL candidate should pass the gate."""
        pipeline = ResearchExecutePipeline()
        result = pipeline.execute_candidate(_dsl_candidate())
        assert result["execution_gate"]["status"] == "pass"

    def test_execution_gate_fail_when_sign_flips(self):
        stat_fn = _make_custom_stat_evidence(sign_ok=False)
        pipeline = ResearchExecutePipeline(compute_stat_evidence=stat_fn)
        result = pipeline.execute_candidate(_dsl_candidate())
        assert result["execution_gate"]["status"] == "fail_technical"
        assert "train_validation_sign_flip" in result["execution_gate"]["reason_codes"]

    def test_holdout_review_not_recommended_by_default(self):
        pipeline = ResearchExecutePipeline()
        result = pipeline.execute_candidate(_dsl_candidate())
        assert result["holdout_review"]["recommended"] is False


# ===================================================================
# Batch execution
# ===================================================================
class TestExecuteBatch:
    def test_batch_result_structure(self):
        pipeline = ResearchExecutePipeline()
        candidates = [_dsl_candidate("C001"), _dsl_candidate("C002")]
        batch_result = pipeline.execute_batch("batch_test", candidates)

        assert batch_result["batch_id"] == "batch_test"
        assert len(batch_result["candidate_results"]) == 2
        assert "judge_packet" in batch_result
        assert "summary" in batch_result

    def test_batch_summary_counts(self):
        pipeline = ResearchExecutePipeline()
        candidates = [
            _dsl_candidate("C001"),
            _bad_dsl_candidate("C002"),
            _dsl_candidate("C003"),
        ]
        batch_result = pipeline.execute_batch("batch_test", candidates)
        summary = batch_result["summary"]
        assert summary["total_candidates"] == 3
        assert summary["precheck_failed"] == 1
        # C002 fails precheck -> fail_technical; C001, C003 pass
        assert summary["gate_fail_technical"] == 1

    def test_judge_packet_built_from_results(self):
        pipeline = ResearchExecutePipeline()
        candidates = [_dsl_candidate("C001")]
        batch_result = pipeline.execute_batch("batch_test", candidates)
        packet = batch_result["judge_packet"]
        jp = packet["judge_packet"]
        assert jp["batch_id"] == "batch_test"
        assert len(jp["candidate_briefs"]) == 1
        assert jp["candidate_briefs"][0]["candidate_id"] == "C001"

    def test_search_context_attached_to_results(self):
        pipeline = ResearchExecutePipeline()
        ctx = {"validation_window_id": "val_2022_2023"}
        batch_result = pipeline.execute_batch("batch_test", [_dsl_candidate()], search_context=ctx)
        assert batch_result["candidate_results"][0]["search_context"] == ctx

    def test_empty_batch(self):
        pipeline = ResearchExecutePipeline()
        batch_result = pipeline.execute_batch("batch_empty", [])
        assert batch_result["summary"]["total_candidates"] == 0
        assert batch_result["candidate_results"] == []

    def test_mixed_pass_and_fail(self):
        """Mix of passing and failing candidates in one batch."""
        pipeline = ResearchExecutePipeline()
        candidates = [
            _dsl_candidate("C001"),
            _bad_dsl_candidate("C002"),
        ]
        batch_result = pipeline.execute_batch("batch_mixed", candidates)
        statuses = [
            r["execution_gate"]["status"]
            for r in batch_result["candidate_results"]
        ]
        assert "pass" in statuses
        assert "fail_technical" in statuses


# ===================================================================
# Helpers
# ===================================================================
class TestSupportWindowReview:
    def test_no_flips(self):
        eval_ = {"support_window_checks": [
            {"sign_consistency_support": True},
            {"sign_consistency_support": True},
        ]}
        assert _compute_support_window_review(eval_)["support_window_warning"] == "none"

    def test_single_flip(self):
        eval_ = {"support_window_checks": [
            {"sign_consistency_support": True},
            {"sign_consistency_support": False},
        ]}
        assert _compute_support_window_review(eval_)["support_window_warning"] == "single_window_flip"

    def test_repeated_flip(self):
        eval_ = {"support_window_checks": [
            {"sign_consistency_support": False},
            {"sign_consistency_support": False},
        ]}
        assert _compute_support_window_review(eval_)["support_window_warning"] == "repeated_sign_flip"

    def test_empty_checks(self):
        assert _compute_support_window_review({})["support_window_warning"] == "none"


class TestHoldoutReviewTrigger:
    def test_not_recommended_by_default(self):
        eval_ = {"ic_mean_validation": 0.005, "ic_ir_validation": 0.05, "multiple_testing_risk_bucket": "low"}
        sim = {"max_lib_corr": 0.80}
        gate = GateResult(status="pass")
        result = _should_recommend_holdout(eval_, sim, gate)
        assert result["recommended"] is False

    def test_high_confidence_triggers(self):
        eval_ = {"ic_mean_validation": 0.020, "ic_ir_validation": 0.20, "multiple_testing_risk_bucket": "low"}
        sim = {"max_lib_corr": 0.20}
        gate = GateResult(status="pass")
        result = _should_recommend_holdout(eval_, sim, gate)
        assert result["recommended"] is True
        assert "high_confidence_candidate" in result["trigger_reason_codes"]

    def test_high_mining_risk_plus_strong_triggers(self):
        eval_ = {"ic_mean_validation": 0.020, "ic_ir_validation": 0.20, "multiple_testing_risk_bucket": "high"}
        sim = {"max_lib_corr": 0.20}
        gate = GateResult(status="pass")
        result = _should_recommend_holdout(eval_, sim, gate)
        assert result["recommended"] is True
        assert "high_mining_risk_but_strong_validation" in result["trigger_reason_codes"]

    def test_fail_technical_suppresses_holdout(self):
        eval_ = {"ic_mean_validation": 0.020, "ic_ir_validation": 0.20, "multiple_testing_risk_bucket": "low"}
        sim = {"max_lib_corr": 0.20}
        gate = GateResult(status="fail_technical")
        result = _should_recommend_holdout(eval_, sim, gate)
        assert result["recommended"] is False
