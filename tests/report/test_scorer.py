"""Tests for CompositeScorer (7-dimension S-curve scoring)."""
import pytest
from report.scorer import CompositeScorer, s_curve_score, robustness_score


class TestScoreToGrade:
    def test_grade_s(self):
        assert CompositeScorer.score_to_grade(95) == "S"

    def test_grade_a(self):
        assert CompositeScorer.score_to_grade(80) == "A"

    def test_grade_b(self):
        assert CompositeScorer.score_to_grade(65) == "B"

    def test_grade_c(self):
        assert CompositeScorer.score_to_grade(50) == "C"

    def test_grade_d(self):
        assert CompositeScorer.score_to_grade(20) == "D"

    def test_grade_boundary_90(self):
        assert CompositeScorer.score_to_grade(90) == "S"

    def test_grade_boundary_75(self):
        assert CompositeScorer.score_to_grade(75) == "A"

    def test_grade_boundary_0(self):
        assert CompositeScorer.score_to_grade(0) == "D"


class TestSCurveScore:
    def test_at_midpoint_returns_50(self):
        score = s_curve_score(0.03, midpoint=0.03, k=92)
        assert score == pytest.approx(50, abs=0.1)

    def test_above_midpoint_above_50(self):
        score = s_curve_score(0.06, midpoint=0.03, k=92)
        assert score > 50

    def test_below_midpoint_below_50(self):
        score = s_curve_score(0.01, midpoint=0.03, k=92)
        assert score < 50


class TestRobustnessScore:
    def test_no_drift(self):
        score = robustness_score(ic_is=-0.05, ic_oos=-0.05)
        assert score == pytest.approx(100.0)

    def test_full_drift(self):
        score = robustness_score(ic_is=-0.05, ic_oos=0.0)
        assert score == pytest.approx(0.0)

    def test_near_zero_is(self):
        score = robustness_score(ic_is=0.005, ic_oos=0.001)
        assert score == 50.0


class TestCompositeScore:
    def test_compute_returns_7_dimensions(self):
        s = CompositeScorer()
        result = s.compute(
            rank_ic_oos=-0.058,
            icir_oos=-0.5,
            ls_sharpe=0.8,
            monotonicity=-0.9,
            ic_is=-0.058,
            ic_oos=-0.057,
            max_corr=0.2,
            ic_1d=-0.058,
            ic_20d=-0.031,
        )
        assert "dimensions" in result
        assert len(result["dimensions"]) == 7
        assert "composite_score" in result
        assert "composite_grade" in result
        assert "library_rank" in result
        assert "library_total" in result

    def test_dimension_names(self):
        s = CompositeScorer()
        result = s.compute(
            rank_ic_oos=-0.05,
            icir_oos=-0.4,
            ls_sharpe=0.6,
            monotonicity=-0.8,
            ic_is=-0.05,
            ic_oos=-0.04,
            max_corr=0.3,
            ic_1d=-0.05,
            ic_20d=-0.03,
        )
        names = [d["name"] for d in result["dimensions"]]
        assert names == [
            "Predictive Power", "Signal Stability", "Profitability",
            "Monotonicity", "OOS Robustness", "Uniqueness", "Decay Resistance",
        ]

    def test_composite_is_weighted(self):
        s = CompositeScorer()
        result = s.compute(
            rank_ic_oos=-0.058,
            icir_oos=-0.5,
            ls_sharpe=0.8,
            monotonicity=-0.9,
            ic_is=-0.058,
            ic_oos=-0.057,
            max_corr=0.2,
            ic_1d=-0.058,
            ic_20d=-0.031,
        )
        dims = result["dimensions"]
        expected = sum(
            d["score"] * w
            for d, (_, w) in zip(dims, CompositeScorer.WEIGHTS)
        )
        assert result["composite_score"] == pytest.approx(expected, abs=0.5)

    def test_none_inputs_default_to_50(self):
        s = CompositeScorer()
        result = s.compute(
            rank_ic_oos=None,
            icir_oos=None,
            ls_sharpe=None,
            monotonicity=None,
            ic_is=None,
            ic_oos=None,
            max_corr=None,
            ic_1d=None,
            ic_20d=None,
        )
        for d in result["dimensions"]:
            assert d["score"] == 50.0
            assert d["data_available"] is False

    def test_library_rank_initially_none(self):
        s = CompositeScorer()
        result = s.compute(
            rank_ic_oos=-0.05,
            icir_oos=-0.3,
            ls_sharpe=0.5,
            monotonicity=-0.7,
            ic_is=-0.05,
            ic_oos=-0.04,
            max_corr=0.3,
            ic_1d=-0.05,
            ic_20d=-0.03,
        )
        assert result["library_rank"] is None
        assert result["library_total"] is None

    def test_generate_charts_returns_radar(self):
        s = CompositeScorer()
        result = s.compute(
            rank_ic_oos=-0.05,
            icir_oos=-0.3,
            ls_sharpe=0.5,
            monotonicity=-0.7,
            ic_is=-0.05,
            ic_oos=-0.04,
            max_corr=0.3,
            ic_1d=-0.05,
            ic_20d=-0.03,
        )
        charts = s.generate_charts(result)
        assert "radar" in charts
