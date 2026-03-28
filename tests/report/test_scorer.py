# tests/report/test_scorer.py
"""Tests for 7-dimension S-curve CompositeScorer."""
import math
import pytest
from report.scorer import CompositeScorer, s_curve_score, robustness_score


class TestSCurveScore:
    def test_midpoint_gives_50(self):
        assert abs(s_curve_score(0.03, midpoint=0.03, k=92) - 50) < 1

    def test_high_value_near_100(self):
        score = s_curve_score(0.08, midpoint=0.03, k=92)
        assert score > 98

    def test_zero_value_near_0(self):
        score = s_curve_score(0.0, midpoint=0.03, k=92)
        assert score < 10

    def test_negative_input(self):
        score = s_curve_score(-0.05, midpoint=0.03, k=92)
        assert score < 1


class TestRobustnessScore:
    def test_no_drift(self):
        assert robustness_score(0.05, 0.05) == 100.0

    def test_50_percent_drift(self):
        score = robustness_score(0.06, 0.03)
        assert abs(score - 50) < 1

    def test_100_percent_drift(self):
        score = robustness_score(0.05, 0.0)
        assert score == 0

    def test_ic_is_near_zero_returns_neutral(self):
        score = robustness_score(0.005, 0.03)
        assert score == 50.0  # |IC_IS| < 0.01 -> neutral


class TestCompositeScorer:
    def test_seven_dimensions(self):
        scorer = CompositeScorer()
        result = scorer.compute(
            rank_ic_oos=0.05,
            icir_oos=0.4,
            ls_sharpe=0.8,
            monotonicity=0.8,
            ic_is=0.05,
            ic_oos=0.04,
            max_corr=0.3,
            ic_1d=0.05,
            ic_20d=0.04,
        )
        assert len(result["dimensions"]) == 7
        assert "composite_score" in result
        assert "composite_grade" in result

    def test_grade_scale(self):
        scorer = CompositeScorer()
        assert scorer.score_to_grade(95) == "S"
        assert scorer.score_to_grade(80) == "A"
        assert scorer.score_to_grade(65) == "B"
        assert scorer.score_to_grade(50) == "C"
        assert scorer.score_to_grade(30) == "D"

    def test_missing_data_uses_neutral(self):
        scorer = CompositeScorer()
        result = scorer.compute(
            rank_ic_oos=0.05,
            icir_oos=0.4,
            ls_sharpe=0.8,
            monotonicity=0.8,
            ic_is=0.05,
            ic_oos=0.04,
            max_corr=None,  # data missing
            ic_1d=0.05,
            ic_20d=0.04,
        )
        # Uniqueness dimension should use score 50
        uniqueness_dim = [d for d in result["dimensions"] if d["name"] == "Uniqueness"][0]
        assert uniqueness_dim["score"] == 50
        assert uniqueness_dim["data_available"] is False

    def test_radar_chart(self):
        scorer = CompositeScorer()
        result = scorer.compute(
            rank_ic_oos=0.05, icir_oos=0.4, ls_sharpe=0.8,
            monotonicity=0.8, ic_is=0.05, ic_oos=0.04,
            max_corr=0.3, ic_1d=0.05, ic_20d=0.04,
        )
        charts = scorer.generate_charts(result)
        assert "radar" in charts

    def test_weights_sum_to_1(self):
        scorer = CompositeScorer()
        total = sum(w for _, w in scorer.WEIGHTS)
        assert abs(total - 1.0) < 0.001

    def test_all_none_returns_neutral(self):
        scorer = CompositeScorer()
        result = scorer.compute(
            rank_ic_oos=None, icir_oos=None, ls_sharpe=None,
            monotonicity=None, ic_is=None, ic_oos=None,
            max_corr=None, ic_1d=None, ic_20d=None,
        )
        assert all(d["score"] == 50 for d in result["dimensions"])
        assert result["composite_score"] == 50.0
        assert result["composite_grade"] == "C"
