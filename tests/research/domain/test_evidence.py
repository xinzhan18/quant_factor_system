"""Tests for research.domain.evidence."""

from datetime import date

import pytest

from research.domain.evidence import (
    BatchExecuteResult,
    BootstrapStabilityResult,
    CandidateExecuteResult,
    EffectStrengthEvidence,
    ExpandingWindowResult,
    FamilyRedundancyView,
    FeasibilityEvidence,
    MechanismAlignmentResult,
    MultipleTestingView,
    PairwiseRedundancy,
    ProbeResult,
    RedundancyEvidence,
    RegimeStabilityResult,
    SearchAdjustedStrength,
    SplitStabilityResult,
    SubspaceRedundancyView,
    SupportWindowCheck,
)


class TestEffectStrengthEvidence:
    def test_construction(self):
        ev = EffectStrengthEvidence(
            ic_mean_is=0.015,
            ic_mean_oos=0.012,
            icir_is=0.20,
            icir_oos=0.18,
            ls_tstat=5.5,
            ls_sharpe=1.2,
            monotonicity_is=0.9,
            monotonicity_oos=0.8,
            long_contribution=0.6,
        )
        assert ev.ic_mean_oos == 0.012
        assert ev.long_contribution == 0.6

    def test_frozen(self):
        ev = EffectStrengthEvidence(
            ic_mean_is=0.01, ic_mean_oos=0.01, icir_is=0.1,
            icir_oos=0.1, ls_tstat=2.0, ls_sharpe=0.5,
            monotonicity_is=0.5, monotonicity_oos=0.5,
        )
        with pytest.raises(AttributeError):
            ev.ic_mean_oos = 0.999


class TestSplitStabilityResult:
    def test_construction(self):
        res = SplitStabilityResult(
            ic_seg_a=0.015,
            ic_seg_b=0.012,
            seg_a_range=(date(2019, 1, 1), date(2021, 12, 31)),
            seg_b_range=(date(2022, 1, 1), date(2023, 12, 31)),
            sign_consistent=True,
            ratio=0.8,
        )
        assert res.sign_consistent is True
        assert res.ratio == 0.8


class TestRegimeStabilityResult:
    def test_construction(self):
        res = RegimeStabilityResult(
            regime_label="bull",
            ic_mean=0.020,
            ls_sharpe=1.5,
            n_days=250,
        )
        assert res.regime_label == "bull"


class TestBootstrapStabilityResult:
    def test_construction(self):
        res = BootstrapStabilityResult(
            n_bootstrap=1000,
            ic_mean=0.013,
            ic_std=0.005,
            ci_lower=0.004,
            ci_upper=0.022,
            pct_positive=0.85,
        )
        assert res.pct_positive == 0.85
        assert res.ci_lower < res.ci_upper


class TestRedundancyEvidence:
    def test_construction(self):
        pw = PairwiseRedundancy(
            factor_id_a="F001",
            factor_id_b="F002",
            correlation=0.65,
        )
        ev = RedundancyEvidence(
            max_correlation=0.65,
            most_correlated_factor_id="F002",
            pairwise=[pw],
            incremental_ic=0.008,
        )
        assert len(ev.pairwise) == 1
        assert ev.max_correlation == 0.65


class TestFeasibilityEvidence:
    def test_construction(self):
        ev = FeasibilityEvidence(
            coverage=0.92,
            turnover_mean=0.15,
            compute_seconds=2.3,
            data_fields_used=("$close", "$volume"),
        )
        assert ev.coverage == 0.92
        assert "$close" in ev.data_fields_used


class TestProbeResult:
    def test_pass_probe(self):
        res = ProbeResult(
            route_id="R001_01",
            expression="Rank(Std($close, 10))",
            computable=True,
            valid_ratio=0.95,
            variance_ok=True,
            ic_mean_full=0.015,
            ic_mean_seg_a=0.018,
            ic_mean_seg_b=0.012,
        )
        assert res.computable is True
        assert res.forbidden_hit is False

    def test_fail_probe(self):
        res = ProbeResult(
            route_id="R001_02",
            expression="BadExpr()",
            computable=False,
            valid_ratio=0.0,
            variance_ok=False,
        )
        assert res.computable is False


class TestCandidateExecuteResult:
    def test_gate_failed(self):
        res = CandidateExecuteResult(
            candidate_id="C001",
            expression="Rank($close)",
            execution_gate_passed=False,
            gate_failure_reasons=("STRENGTH_IC_TOO_LOW",),
        )
        assert res.execution_gate_passed is False
        assert res.effect is None

    def test_gate_passed_with_evidence(self):
        effect = EffectStrengthEvidence(
            ic_mean_is=0.02, ic_mean_oos=0.015, icir_is=0.25,
            icir_oos=0.20, ls_tstat=6.0, ls_sharpe=1.5,
            monotonicity_is=0.9, monotonicity_oos=0.8,
        )
        feasibility = FeasibilityEvidence(coverage=0.93)
        res = CandidateExecuteResult(
            candidate_id="C002",
            expression="Rank(Std($close, 10))",
            execution_gate_passed=True,
            effect=effect,
            feasibility=feasibility,
        )
        assert res.execution_gate_passed is True
        assert res.effect.ic_mean_oos == 0.015


class TestBatchExecuteResult:
    def test_empty_batch(self):
        res = BatchExecuteResult(
            batch_id="batch_042",
            evaluation_profile_id="standard_eval_v2",
        )
        assert res.total_candidates == 0
        assert res.candidates == ()

    def test_with_candidates(self):
        c1 = CandidateExecuteResult(
            candidate_id="C001",
            expression="Rank($close)",
            execution_gate_passed=True,
        )
        c2 = CandidateExecuteResult(
            candidate_id="C002",
            expression="Std($close, 20)",
            execution_gate_passed=False,
        )
        res = BatchExecuteResult(
            batch_id="batch_042",
            evaluation_profile_id="standard_eval_v2",
            candidates=(c1, c2),
            total_candidates=2,
            gate_passed_count=1,
        )
        assert res.total_candidates == 2
        assert res.gate_passed_count == 1


class TestMechanismAlignmentResult:
    def test_construction(self):
        res = MechanismAlignmentResult(
            logic_id="L021",
            alignment_score=0.85,
            size_proxy_risk=False,
            style_repackaging_risk=False,
            explanation="Good alignment with breakout thesis",
        )
        assert res.alignment_score == 0.85
        assert res.size_proxy_risk is False


class TestSupportWindowCheck:
    def test_construction(self):
        res = SupportWindowCheck(
            window_id="support_2023",
            ic_mean=0.011,
            ic_positive_ratio=0.55,
            monotonicity=0.7,
            consistent_with_primary=True,
        )
        assert res.consistent_with_primary is True
