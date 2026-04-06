"""Tests for research.execute.judge_packet_builder — compression into JudgePacket."""

import pytest

from research.execute.judge_packet_builder import (
    JudgePacketBuilder,
    _build_candidate_brief,
    _effect_bucket,
    _stability_bucket,
    _redundancy_bucket,
    _feasibility_bucket,
    _holdout_effect_bucket,
)


# ===================================================================
# Bucket helpers
# ===================================================================
class TestEffectBucket:
    def test_strong(self):
        assert _effect_bucket({"ic_mean_validation": 0.020, "ic_ir_validation": 0.20, "monotonicity_validation": 0.40}) == "strong"

    def test_weak_low_ic(self):
        assert _effect_bucket({"ic_mean_validation": 0.005, "ic_ir_validation": 0.10, "monotonicity_validation": 0.30}) == "weak"

    def test_weak_low_ir(self):
        assert _effect_bucket({"ic_mean_validation": 0.015, "ic_ir_validation": 0.03, "monotonicity_validation": 0.40}) == "weak"

    def test_borderline(self):
        assert _effect_bucket({"ic_mean_validation": 0.010, "ic_ir_validation": 0.10, "monotonicity_validation": 0.20}) == "borderline"

    def test_missing_values_default_weak(self):
        assert _effect_bucket({}) == "weak"

    def test_negative_ic_treated_as_abs(self):
        assert _effect_bucket({"ic_mean_validation": -0.020, "ic_ir_validation": -0.20, "monotonicity_validation": -0.40}) == "strong"


class TestStabilityBucket:
    def test_good(self):
        assert _stability_bucket({"split_stability": "high", "regime_stability": "high", "expanding_window_pass": True}) == "good"

    def test_poor_due_to_split(self):
        assert _stability_bucket({"split_stability": "low", "regime_stability": "high", "expanding_window_pass": True}) == "poor"

    def test_poor_due_to_ew_fail(self):
        assert _stability_bucket({"split_stability": "high", "regime_stability": "high", "expanding_window_pass": False}) == "poor"

    def test_medium_default(self):
        assert _stability_bucket({"split_stability": "medium", "regime_stability": "medium", "expanding_window_pass": True}) == "medium"


class TestRedundancyBucket:
    def test_high_due_to_corr(self):
        assert _redundancy_bucket({"max_lib_corr": 0.90}) == "high"

    def test_high_due_to_family(self):
        sim = {"max_lib_corr": 0.50, "family_redundancy_view": {"family_overlap_bucket": "high"}}
        assert _redundancy_bucket(sim) == "high"

    def test_medium(self):
        assert _redundancy_bucket({"max_lib_corr": 0.65}) == "medium"

    def test_low(self):
        assert _redundancy_bucket({"max_lib_corr": 0.30}) == "low"

    def test_empty(self):
        assert _redundancy_bucket({}) == "low"


class TestFeasibilityBucket:
    def test_good(self):
        assert _feasibility_bucket({"rebalance_stress_proxy": "low", "liquidity_coverage_ratio": 0.80, "turnover": 0.30}) == "good"

    def test_poor_high_stress(self):
        assert _feasibility_bucket({"rebalance_stress_proxy": "high"}) == "poor"

    def test_poor_low_liquidity(self):
        assert _feasibility_bucket({"rebalance_stress_proxy": "low", "liquidity_coverage_ratio": 0.20}) == "poor"

    def test_acceptable_medium_stress(self):
        assert _feasibility_bucket({"rebalance_stress_proxy": "medium"}) == "acceptable"

    def test_acceptable_high_turnover(self):
        assert _feasibility_bucket({"rebalance_stress_proxy": "low", "liquidity_coverage_ratio": 0.80, "turnover": 2.0}) == "acceptable"


class TestHoldoutEffectBucket:
    def test_strong(self):
        assert _holdout_effect_bucket({"ic_mean_holdout": 0.020, "ic_ir_holdout": 0.20, "monotonicity_holdout": 0.40}) == "strong"

    def test_none_when_missing(self):
        assert _holdout_effect_bucket({}) is None

    def test_weak(self):
        assert _holdout_effect_bucket({"ic_mean_holdout": 0.005, "ic_ir_holdout": 0.03, "monotonicity_holdout": 0.10}) == "weak"

    def test_borderline(self):
        assert _holdout_effect_bucket({"ic_mean_holdout": 0.010, "ic_ir_holdout": 0.10, "monotonicity_holdout": 0.20}) == "borderline"


# ===================================================================
# Candidate brief
# ===================================================================
class TestBuildCandidateBrief:
    def test_basic_brief(self):
        result = {
            "candidate_id": "C042_01",
            "logic_id": "L021",
            "route_id": "R021_01",
            "route_type": "genesis",
            "family_id": "FM_breakout",
            "experiment_lineage_tag": "ELT_01",
            "evaluation": {
                "ic_mean_validation": 0.020,
                "ic_ir_validation": 0.20,
                "monotonicity_validation": 0.40,
                "split_stability": "high",
                "regime_stability": "high",
                "expanding_window_pass": True,
            },
            "similarity": {"max_lib_corr": 0.30},
            "feasibility": {"rebalance_stress_proxy": "low", "liquidity_coverage_ratio": 0.80, "turnover": 0.30},
            "execution_gate": {"status": "pass"},
            "holdout_review": {"recommended": False},
            "support_window_review": {"support_window_warning": "none"},
        }
        brief = _build_candidate_brief(result)
        assert brief["candidate_id"] == "C042_01"
        assert brief["validation_effect_bucket"] == "strong"
        assert brief["stability_bucket"] == "good"
        assert brief["redundancy_bucket"] == "low"
        assert brief["feasibility_bucket"] == "good"
        assert brief["execution_gate_status"] == "pass"
        assert brief["holdout_review_recommended"] is False
        assert brief["holdout_effect_bucket"] is None  # no holdout data in evaluation
        assert brief["support_window_warning"] == "none"

    def test_brief_with_holdout_data(self):
        result = {
            "candidate_id": "C042_02",
            "logic_id": "L021",
            "route_id": "R021_02",
            "route_type": "genesis",
            "family_id": "FM_breakout",
            "experiment_lineage_tag": "ELT_01",
            "evaluation": {
                "ic_mean_validation": 0.020,
                "ic_ir_validation": 0.20,
                "monotonicity_validation": 0.40,
                "split_stability": "high",
                "regime_stability": "high",
                "expanding_window_pass": True,
                "ic_mean_holdout": 0.018,
                "ic_ir_holdout": 0.16,
                "monotonicity_holdout": 0.35,
                "validation_holdout_decay_ratio": 0.90,
            },
            "similarity": {"max_lib_corr": 0.30},
            "feasibility": {"rebalance_stress_proxy": "low", "liquidity_coverage_ratio": 0.80, "turnover": 0.30},
            "execution_gate": {"status": "pass"},
            "holdout_review": {"recommended": True},
            "support_window_review": {"support_window_warning": "none"},
        }
        brief = _build_candidate_brief(result)
        assert brief["holdout_effect_bucket"] == "strong"
        assert brief["holdout_ic_mean"] == 0.018
        assert brief["holdout_ic_ir"] == 0.16
        assert brief["holdout_monotonicity"] == 0.35
        assert brief["holdout_decay_ratio"] == 0.90

    def test_minimal_result_no_crash(self):
        brief = _build_candidate_brief({})
        assert brief["candidate_id"] is None
        assert brief["validation_effect_bucket"] == "weak"
        assert brief["holdout_effect_bucket"] is None


# ===================================================================
# JudgePacketBuilder
# ===================================================================
class TestJudgePacketBuilder:
    def setup_method(self):
        self.builder = JudgePacketBuilder()

    def _make_result(self, cid="C001", logic_id="L001", gate_status="pass",
                     support_warning="none"):
        return {
            "candidate_id": cid,
            "logic_id": logic_id,
            "route_id": "R001",
            "route_type": "genesis",
            "family_id": "FM_test",
            "experiment_lineage_tag": "ELT_01",
            "evaluation": {
                "ic_mean_validation": 0.012,
                "ic_ir_validation": 0.10,
                "monotonicity_validation": 0.25,
                "split_stability": "medium",
                "regime_stability": "medium",
                "expanding_window_pass": True,
            },
            "similarity": {"max_lib_corr": 0.40},
            "feasibility": {"rebalance_stress_proxy": "low", "liquidity_coverage_ratio": 0.80, "turnover": 0.30},
            "execution_gate": {"status": gate_status},
            "holdout_review": {"recommended": False},
            "support_window_review": {"support_window_warning": support_warning},
        }

    def test_basic_packet_structure(self):
        results = [self._make_result("C001"), self._make_result("C002")]
        packet = self.builder.build("batch_001", results)

        jp = packet["judge_packet"]
        assert jp["batch_id"] == "batch_001"
        assert len(jp["candidate_briefs"]) == 2
        assert "L001" in jp["active_logic_ids"]
        assert jp["support_window_review"]["support_window_warning"] == "none"

    def test_search_context_passthrough(self):
        ctx = {"validation_window_id": "val_2022_2023"}
        packet = self.builder.build("batch_001", [self._make_result()], search_context=ctx)
        assert packet["judge_packet"]["search_context"] == ctx

    def test_aggregated_support_warning_repeated(self):
        r1 = self._make_result("C001", support_warning="single_window_flip")
        r2 = self._make_result("C002", support_warning="repeated_sign_flip")
        packet = self.builder.build("batch_001", [r1, r2])
        assert packet["judge_packet"]["support_window_review"]["support_window_warning"] == "repeated_sign_flip"

    def test_aggregated_support_warning_single(self):
        r1 = self._make_result("C001", support_warning="none")
        r2 = self._make_result("C002", support_warning="single_window_flip")
        packet = self.builder.build("batch_001", [r1, r2])
        assert packet["judge_packet"]["support_window_review"]["support_window_warning"] == "single_window_flip"

    def test_multiple_logic_ids(self):
        r1 = self._make_result("C001", logic_id="L001")
        r2 = self._make_result("C002", logic_id="L002")
        packet = self.builder.build("batch_001", [r1, r2])
        assert sorted(packet["judge_packet"]["active_logic_ids"]) == ["L001", "L002"]

    def test_empty_batch(self):
        packet = self.builder.build("batch_001", [])
        assert len(packet["judge_packet"]["candidate_briefs"]) == 0
        assert packet["judge_packet"]["active_logic_ids"] == []

    def test_no_policy_snapshot_ref(self):
        packet = self.builder.build("batch_001", [self._make_result()])
        assert "policy_snapshot_ref" not in packet["judge_packet"]
