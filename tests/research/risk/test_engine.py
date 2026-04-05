"""Tests for risk/engine.py — RiskEngine orchestrator."""

import numpy as np
import pandas as pd
from unittest.mock import MagicMock, patch

from research.risk.engine import RiskEngine, _extend_start, _trim_to_range
from research.risk.schema import RiskReview


def _mock_provider(n_dates=100, n_stocks=50, seed=42):
    """Create a mock DataProvider that returns synthetic data."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2022-01-01", periods=n_dates)
    stocks = [f"S{i:03d}" for i in range(n_stocks)]
    idx = pd.MultiIndex.from_product([dates, stocks], names=["datetime", "instrument"])
    n = len(idx)

    provider = MagicMock()
    provider.universe = MagicMock()
    provider.universe.name = "csi1000"

    def mock_returns(start, end, horizon=1):
        return pd.DataFrame(
            {"return_1d": rng.normal(0, 0.02, n)}, index=idx
        )

    def mock_market_data(fields, start, end):
        data = {}
        for f in fields:
            data[f] = rng.lognormal(4, 1, n) if "cap" in f else rng.uniform(0.5, 20, n)
        return pd.DataFrame(data, index=idx)

    provider.get_returns = MagicMock(side_effect=mock_returns)
    provider.get_market_data = MagicMock(side_effect=mock_market_data)
    return provider


class TestRiskEngine:
    def test_stub_returns_acceptable(self):
        stub = RiskEngine.stub()
        review = stub.compute_risk_review(
            pd.DataFrame(), {}, {}
        )
        assert isinstance(review, RiskReview)
        assert review.risk_model_review_bucket == "acceptable"

    def test_compute_returns_risk_review(self):
        provider = _mock_provider()
        engine = RiskEngine(data_provider=provider)

        rng = np.random.default_rng(99)
        dates = pd.bdate_range("2022-01-01", periods=100)
        stocks = [f"S{i:03d}" for i in range(50)]
        idx = pd.MultiIndex.from_product([dates, stocks], names=["datetime", "instrument"])
        signal = pd.DataFrame({"factor": rng.normal(size=len(idx))}, index=idx)

        sample_policy = {"active_validation_range": ["2022-01-01", "2022-12-31"]}
        profile = {"holding_horizon": 5}

        review = engine.compute_risk_review(signal, sample_policy, profile)
        assert isinstance(review, RiskReview)
        assert review.risk_model_review_bucket in ("acceptable", "borderline", "poor")

    def test_empty_signal_returns_stub(self):
        provider = _mock_provider()
        engine = RiskEngine(data_provider=provider)
        signal = pd.DataFrame()
        review = engine.compute_risk_review(signal, {"active_validation_range": []}, {})
        assert review.risk_model_review_bucket == "acceptable"
        assert review.raw_view_ic is None


class TestHelpers:
    def test_extend_start(self):
        result = _extend_start("2022-01-01", 400)
        assert result == "2020-11-27"

    def test_trim_to_range(self):
        df = pd.DataFrame({
            "time": pd.bdate_range("2022-01-01", periods=50),
            "symbol": "S001",
            "value": range(50),
        })
        trimmed = _trim_to_range(df, "2022-01-10", "2022-02-10")
        assert trimmed["time"].min() >= pd.Timestamp("2022-01-10")
        assert trimmed["time"].max() <= pd.Timestamp("2022-02-10")
