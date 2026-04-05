"""Tests for risk/schema.py."""

from research.risk.schema import RiskReview, compute_risk_bucket


class TestComputeRiskBucket:
    def test_poor_low_survival(self):
        assert compute_risk_bucket(0.2, "low") == "poor"

    def test_poor_high_crowding(self):
        assert compute_risk_bucket(0.8, "high") == "poor"

    def test_borderline_medium_survival(self):
        assert compute_risk_bucket(0.5, "low") == "borderline"

    def test_borderline_medium_crowding(self):
        assert compute_risk_bucket(0.8, "medium") == "borderline"

    def test_acceptable(self):
        assert compute_risk_bucket(0.8, "low") == "acceptable"

    def test_none_survival_acceptable(self):
        assert compute_risk_bucket(None, "low") == "acceptable"

    def test_nan_survival_acceptable(self):
        assert compute_risk_bucket(float("nan"), "low") == "acceptable"

    def test_none_survival_high_crowding_poor(self):
        assert compute_risk_bucket(None, "high") == "poor"


class TestRiskReview:
    def test_stub_has_acceptable_bucket(self):
        stub = RiskReview.stub()
        assert stub.risk_model_review_bucket == "acceptable"
        assert stub.style_crowding_risk == "low"
        assert stub.raw_view_ic is None

    def test_to_dict_keys(self):
        review = RiskReview.stub()
        d = review.to_dict()
        expected_keys = {
            "raw_view_ic", "cap_industry_neutral_ic", "barra_residual_ic",
            "barra_residual_icir", "alpha_survival_ratio",
            "dominant_style_exposure", "style_crowding_risk",
            "style_r_squared", "style_exposures", "risk_model_review_bucket",
        }
        assert set(d.keys()) == expected_keys

    def test_frozen(self):
        review = RiskReview.stub()
        try:
            review.raw_view_ic = 0.5  # type: ignore
            assert False, "Should be frozen"
        except AttributeError:
            pass
