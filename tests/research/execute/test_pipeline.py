"""Tests for research.execute.pipeline — the main orchestrator.

Tests focus on orchestration: candidates flow through steps in order,
prepare_batch is called, factor_flat propagates, batch summary is correct.
"""

import pytest
from unittest.mock import MagicMock, call

import pandas as pd

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


def _make_signal_result(with_flat=True):
    """Return a signal result dict with evaluation_ready_signal + factor_flat."""
    return {
        "evaluation_ready_signal": pd.DataFrame({"factor": [1.0]}) if with_flat else None,
        "factor_flat": pd.DataFrame({"time": [], "symbol": [], "value": []}) if with_flat else None,
    }


def _make_stat_evidence(ic_val=0.012, sign_ok=True):
    def _stat(signal, sample_policy):
        return {
            "ic_mean_train": 0.018,
            "ic_ir_train": 0.20,
            "ic_mean_validation": ic_val,
            "ic_ir_validation": 0.13,
            "ic_win_rate_validation": 0.55,
            "monotonicity_validation": 0.35,
            "sign_consistency": sign_ok,
            "train_validation_decay_ratio": 0.56,
            "split_stability": "medium",
            "regime_stability": "medium",
            "horizon_consistency": "medium",
            "expanding_window_ic_stability": 0.63,
            "expanding_window_sign_consistency": 0.71,
            "expanding_window_pass": True,
            "bootstrap_stability_score": None,
            "bootstrap_sign_consistency": None,
            "purged_walk_forward_score": None,
            "purged_walk_forward_status": None,
            "multiple_testing_risk_bucket": "low",
            "search_adjusted_strength_bucket": "medium",
            "support_window_checks": [],
        }
    return _stat


def _make_pipeline(**overrides):
    """Build a pipeline with mock callables."""
    defaults = {
        "compute_signal": lambda c, p: {"base_signal": pd.DataFrame({"f": [1.0]}), "diagnostics": {}},
        "preprocess_signal": lambda b, p: _make_signal_result(),
        "compute_stat_evidence": _make_stat_evidence(),
        "compute_redundancy": lambda s, c: {
            "max_lib_corr": 0.1, "nearest_factor_id": None, "is_near_duplicate": False,
            "family_overlap_score": 0.0, "subspace_redundancy_score": 0.0,
            "residual_incremental_ic": 0.0, "replacement_candidate_hint": False,
            "family_redundancy_view": {}, "subspace_redundancy_view": {},
        },
        "compute_feasibility": lambda s: {"turnover": 0.2, "coverage": 0.9, "half_life": 5.0,
                                           "holding_period_proxy": "medium",
                                           "liquidity_coverage_ratio": 0.9,
                                           "tail_trade_concentration": 0.15,
                                           "small_cap_concentration": 0.25,
                                           "rebalance_stress_proxy": "low"},
    }
    defaults.update(overrides)
    return ResearchExecutePipeline(**defaults)


# ===================================================================
# Single candidate execution
# ===================================================================

class TestExecuteCandidate:
    def test_passing_candidate_has_all_keys(self):
        pipeline = _make_pipeline()
        result = pipeline.execute_candidate(_dsl_candidate())
        expected_keys = {
            "candidate_id", "name", "expression", "direction",
            "logic_id", "route_id", "experiment_lineage_tag",
            "family_id", "route_type", "source_type",
            "precheck", "diagnostics", "evaluation", "similarity",
            "risk_review", "feasibility", "execution_gate",
            "support_window_review", "holdout_review",
        }
        assert expected_keys.issubset(result.keys())

    def test_failed_precheck_fills_empty_sections(self):
        pipeline = _make_pipeline()
        result = pipeline.execute_candidate(_bad_dsl_candidate())
        assert result["precheck"]["status"] == "failed"
        assert result["evaluation"] == {}
        assert result["similarity"] == {}

    def test_factor_flat_passed_to_risk_engine(self):
        """Risk engine receives factor_flat from preprocess step."""
        mock_risk = MagicMock()
        mock_risk.compute_risk_review.return_value = MagicMock(to_dict=lambda: {})

        pipeline = _make_pipeline(risk_engine=mock_risk)
        pipeline.execute_candidate(_dsl_candidate())

        mock_risk.compute_risk_review.assert_called_once()
        call_kwargs = mock_risk.compute_risk_review.call_args
        assert "factor_flat" in call_kwargs.kwargs


# ===================================================================
# Batch execution
# ===================================================================

class TestExecuteBatch:
    def test_prepare_batch_called_before_candidates(self):
        call_order = []
        mock_prepare = MagicMock(side_effect=lambda sp, re: call_order.append("prepare"))

        def mock_compute(c, p):
            call_order.append("compute")
            return {"base_signal": pd.DataFrame({"f": [1.0]}), "diagnostics": {}}

        pipeline = _make_pipeline(
            prepare_batch=mock_prepare,
            compute_signal=mock_compute,
        )
        pipeline.execute_batch("B001", [_dsl_candidate()])

        assert call_order[0] == "prepare"
        assert "compute" in call_order

    def test_batch_summary_counts(self):
        pipeline = _make_pipeline()
        result = pipeline.execute_batch(
            "B001",
            [_dsl_candidate("C1"), _dsl_candidate("C2"), _bad_dsl_candidate("C3")],
        )
        summary = result["summary"]
        assert summary["total_candidates"] == 3
        assert summary["precheck_failed"] == 1

    def test_batch_result_has_judge_packet(self):
        pipeline = _make_pipeline()
        result = pipeline.execute_batch("B001", [_dsl_candidate()])
        assert "judge_packet" in result


# ===================================================================
# Support window review
# ===================================================================

class TestSupportWindowReview:
    def test_no_flips(self):
        result = _compute_support_window_review({
            "support_window_checks": [
                {"sign_consistency_support": True},
                {"sign_consistency_support": True},
            ]
        })
        assert result["support_window_warning"] == "none"

    def test_single_flip(self):
        result = _compute_support_window_review({
            "support_window_checks": [
                {"sign_consistency_support": False},
                {"sign_consistency_support": True},
            ]
        })
        assert result["support_window_warning"] == "single_window_flip"

    def test_repeated_flips(self):
        result = _compute_support_window_review({
            "support_window_checks": [
                {"sign_consistency_support": False},
                {"sign_consistency_support": False},
            ]
        })
        assert result["support_window_warning"] == "repeated_sign_flip"


# ===================================================================
# Holdout review trigger
# ===================================================================

class TestHoldoutReview:
    def test_strong_and_low_redundancy_triggers(self):
        evaluation = {"ic_mean_validation": 0.02, "ic_ir_validation": 0.2,
                       "multiple_testing_risk_bucket": "low"}
        similarity = {"max_lib_corr": 0.1}
        gate = GateResult(status="pass", reason_codes=[])
        result = _should_recommend_holdout(evaluation, similarity, gate)
        assert result["recommended"] is True

    def test_fail_technical_blocks_holdout(self):
        evaluation = {"ic_mean_validation": 0.02, "ic_ir_validation": 0.2,
                       "multiple_testing_risk_bucket": "low"}
        similarity = {"max_lib_corr": 0.1}
        gate = GateResult(status="fail_technical", reason_codes=["bad"])
        result = _should_recommend_holdout(evaluation, similarity, gate)
        assert result["recommended"] is False

    def test_holdout_confirms_signal(self):
        evaluation = {
            "ic_mean_validation": 0.02, "ic_ir_validation": 0.2,
            "multiple_testing_risk_bucket": "low",
            "ic_mean_holdout": 0.015, "ic_ir_holdout": 0.12,
        }
        similarity = {"max_lib_corr": 0.1}
        gate = GateResult(status="pass", reason_codes=[])
        result = _should_recommend_holdout(evaluation, similarity, gate)
        assert "holdout_confirms_signal" in result["trigger_reason_codes"]

    def test_holdout_signal_vanished(self):
        evaluation = {
            "ic_mean_validation": 0.02, "ic_ir_validation": 0.2,
            "multiple_testing_risk_bucket": "low",
            "ic_mean_holdout": 0.003, "ic_ir_holdout": 0.02,
        }
        similarity = {"max_lib_corr": 0.1}
        gate = GateResult(status="pass", reason_codes=[])
        result = _should_recommend_holdout(evaluation, similarity, gate)
        assert "holdout_signal_vanished" in result["trigger_reason_codes"]
