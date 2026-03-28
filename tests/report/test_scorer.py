"""Tests for CompositeScorer."""
import pytest
from report.scorer import CompositeScorer


class TestScoreToGrade:
    def test_grade_a(self):
        assert CompositeScorer.score_to_grade(95) == "A"

    def test_grade_a_minus(self):
        assert CompositeScorer.score_to_grade(85) == "A-"

    def test_grade_b_plus(self):
        assert CompositeScorer.score_to_grade(77) == "B+"

    def test_grade_b(self):
        assert CompositeScorer.score_to_grade(70) == "B"

    def test_grade_c(self):
        assert CompositeScorer.score_to_grade(50) == "C"

    def test_grade_d(self):
        assert CompositeScorer.score_to_grade(20) == "D"

    def test_grade_boundary_90(self):
        assert CompositeScorer.score_to_grade(90) == "A"

    def test_grade_boundary_0(self):
        assert CompositeScorer.score_to_grade(0) == "D"


class TestDimensionScoring:
    def test_predictive_power_high_ic(self):
        s = CompositeScorer()
        score = s._score_predictive_power(0.10)
        assert score >= 80  # A range

    def test_predictive_power_low_ic(self):
        s = CompositeScorer()
        score = s._score_predictive_power(0.02)
        assert score < 35  # D range

    def test_predictive_power_medium_ic(self):
        s = CompositeScorer()
        score = s._score_predictive_power(0.058)
        assert 55 <= score <= 79  # B range

    def test_monotonicity_strong(self):
        s = CompositeScorer()
        score = s._score_monotonicity(-0.9)
        assert score >= 80  # A range

    def test_stability_consistent(self):
        s = CompositeScorer()
        score = s._score_stability(ic_is=-0.058, ic_oos=-0.057)
        assert score >= 80  # A range (delta < 10%)

    def test_stability_divergent(self):
        s = CompositeScorer()
        score = s._score_stability(ic_is=-0.058, ic_oos=-0.01)
        assert score < 35  # D range (delta > 50%)

    def test_decay_resistance_good(self):
        s = CompositeScorer()
        score = s._score_decay_resistance(ic_1d=-0.058, ic_20d=-0.045)
        assert score >= 80  # A range (ratio ~0.776, which is >= 0.7 threshold)

    def test_capacity_high(self):
        s = CompositeScorer()
        score = s._score_capacity(0.97)
        assert score >= 80  # A range

    def test_uniqueness_low_corr(self):
        s = CompositeScorer()
        score = s._score_uniqueness(0.2)
        assert score >= 80  # A range

    def test_uniqueness_high_corr(self):
        s = CompositeScorer()
        score = s._score_uniqueness(0.8)
        assert score < 35  # D range


class TestCompositeScore:
    def test_compute_returns_all_dimensions(self):
        s = CompositeScorer()
        result = s.compute(
            ic_mean=0.058,
            monotonicity=-0.9,
            ic_is=-0.058,
            ic_oos=-0.057,
            ic_1d=-0.058,
            ic_20d=-0.031,
            coverage=0.962,
            max_library_corr=0.0,
        )
        assert "dimensions" in result
        assert "composite" in result
        assert len(result["dimensions"]) == 6
        assert "score" in result["composite"]
        assert "grade" in result["composite"]

    def test_composite_is_average(self):
        s = CompositeScorer()
        result = s.compute(
            ic_mean=0.058,
            monotonicity=-0.9,
            ic_is=-0.058,
            ic_oos=-0.057,
            ic_1d=-0.058,
            ic_20d=-0.031,
            coverage=0.962,
            max_library_corr=0.0,
        )
        dim_scores = [d["score"] for d in result["dimensions"]]
        expected_avg = sum(dim_scores) / len(dim_scores)
        assert result["composite"]["score"] == pytest.approx(expected_avg, abs=0.5)
