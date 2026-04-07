"""Tests for judge_charts -- judge evidence visualization."""
import pytest
from report.analytics import judge_charts


def _make_judge_data(*, include_holdout=True, include_reason_codes=True):
    """Build a realistic judge_data dict for testing."""
    data = {
        "candidate_verdict": {
            "verdict": "admit",
            "reason_codes": [
                {"code": "strong_validation_effect", "severity": "info"},
                {"code": "good_split_stability", "severity": "info"},
                {"code": "moderate_style_exposure", "severity": "medium"},
            ] if include_reason_codes else [],
            "evidence_summary": {
                "mechanism_alignment": "aligned",
                "statistical_strength": "strong",
                "stability": "good",
                "redundancy": "low",
                "feasibility": "ok",
                "risk_model_review": "acceptable",
            },
            "holdout_review_required": False,
        },
        "candidate_brief": {
            "validation_effect_bucket": "strong",
            "stability_bucket": "good",
            "redundancy_bucket": "low",
            "feasibility_bucket": "good",
            "risk_model_review_bucket": "acceptable",
            "holdout_ic_mean": -0.025 if include_holdout else None,
            "holdout_ic_ir": -0.30 if include_holdout else None,
            "holdout_monotonicity": -0.8 if include_holdout else None,
            "holdout_decay_ratio": 0.85 if include_holdout else None,
        },
        "validation_metrics": {
            "ic_mean_validation": -0.030,
            "ic_ir_validation": -0.35,
        },
    }
    return data


class TestGenerateCharts:
    def test_full_data_returns_all_charts(self):
        data = _make_judge_data()
        charts = judge_charts.generate_charts(data)
        assert "verdict_radar_6d" in charts
        assert "reason_code_bar" in charts
        assert "holdout_comparison" in charts

    def test_empty_dict_returns_empty(self):
        assert judge_charts.generate_charts({}) == {}

    def test_no_holdout_skips_comparison(self):
        data = _make_judge_data(include_holdout=False)
        charts = judge_charts.generate_charts(data)
        assert "verdict_radar_6d" in charts
        assert "holdout_comparison" not in charts

    def test_no_reason_codes_skips_bar(self):
        data = _make_judge_data(include_reason_codes=False)
        charts = judge_charts.generate_charts(data)
        assert "reason_code_bar" not in charts

    def test_minimal_dims_skips_radar(self):
        data = {
            "candidate_verdict": {"verdict": "reject", "evidence_summary": {}},
            "candidate_brief": {},
        }
        charts = judge_charts.generate_charts(data)
        assert "verdict_radar_6d" not in charts


class TestVerdictBadge:
    def test_returns_structure(self):
        data = _make_judge_data()
        badge = judge_charts.verdict_badge(data)
        assert badge is not None
        assert badge["verdict"] == "admit"
        assert isinstance(badge["reason_summary"], str)
        assert isinstance(badge["holdout_review"], bool)

    def test_empty_returns_none(self):
        assert judge_charts.verdict_badge({}) is None

    def test_no_verdict_returns_none(self):
        data = {"candidate_verdict": {}}
        assert judge_charts.verdict_badge(data) is None

    def test_fatal_codes_prioritized(self):
        data = {
            "candidate_verdict": {
                "verdict": "reject",
                "reason_codes": [
                    {"code": "info_code", "severity": "info"},
                    {"code": "fatal_flaw", "severity": "fatal"},
                ],
            },
        }
        badge = judge_charts.verdict_badge(data)
        assert "fatal_flaw" in badge["reason_summary"]
