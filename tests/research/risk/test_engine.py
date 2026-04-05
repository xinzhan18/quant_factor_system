"""Tests for risk/engine.py — RiskEngine orchestrator."""

import numpy as np
import pandas as pd
from unittest.mock import MagicMock

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


def _make_signal(n_dates=100, n_stocks=50, seed=99):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2022-01-01", periods=n_dates)
    stocks = [f"S{i:03d}" for i in range(n_stocks)]
    idx = pd.MultiIndex.from_product([dates, stocks], names=["datetime", "instrument"])
    return pd.DataFrame({"factor": rng.normal(size=len(idx))}, index=idx)


class TestRiskEngine:
    def test_stub_returns_acceptable(self):
        stub = RiskEngine.stub()
        review = stub.compute_risk_review(pd.DataFrame(), {}, {})
        assert isinstance(review, RiskReview)
        assert review.risk_model_review_bucket == "acceptable"

    def test_compute_returns_risk_review(self):
        provider = _mock_provider()
        engine = RiskEngine(data_provider=provider)

        signal = _make_signal()
        sample_policy = {"active_validation_range": ["2022-01-01", "2022-12-31"]}
        profile = {"holding_horizon": 5}

        review = engine.compute_risk_review(signal, sample_policy, profile)
        assert isinstance(review, RiskReview)
        assert review.risk_model_review_bucket in ("acceptable", "borderline", "poor")

    def test_empty_signal_returns_stub(self):
        provider = _mock_provider()
        engine = RiskEngine(data_provider=provider)
        review = engine.compute_risk_review(
            pd.DataFrame(), {"active_validation_range": []}, {}
        )
        assert review.risk_model_review_bucket == "acceptable"
        assert review.raw_view_ic is None

    def test_factor_flat_param_skips_conversion(self):
        """When factor_flat is provided, engine uses it directly."""
        from core.factor_stats import multiindex_to_flat
        provider = _mock_provider()
        engine = RiskEngine(data_provider=provider)

        signal = _make_signal()
        factor_flat = multiindex_to_flat(signal)
        sample_policy = {"active_validation_range": ["2022-01-01", "2022-12-31"]}
        profile = {"holding_horizon": 5}

        review = engine.compute_risk_review(
            signal, sample_policy, profile, factor_flat=factor_flat
        )
        assert isinstance(review, RiskReview)

    def test_prepare_batch_uses_cached_returns(self):
        """After prepare_batch, engine doesn't call provider.get_returns."""
        from core.factor_stats import multiindex_to_flat
        provider = _mock_provider()
        engine = RiskEngine(data_provider=provider)

        signal = _make_signal()
        factor_flat = multiindex_to_flat(signal)
        sample_policy = {"active_validation_range": ["2022-01-01", "2022-12-31"]}
        profile = {"holding_horizon": 5}

        # Pre-fetch returns
        ret_mi = provider.get_returns("2022-01-01", "2022-12-31", horizon=5)
        returns_flat = multiindex_to_flat(ret_mi)
        shared_returns = {("2022-01-01", "2022-12-31", 5): returns_flat}
        shared_cap = provider.get_market_data(["$circ_market_cap"], "2022-01-01", "2022-12-31")

        # Reset call counts
        provider.get_returns.reset_mock()
        provider.get_market_data.reset_mock()

        engine.prepare_batch(shared_returns, shared_cap)
        engine.compute_risk_review(signal, sample_policy, profile, factor_flat=factor_flat)

        # Provider should NOT be called for returns or cap
        provider.get_returns.assert_not_called()
        # get_market_data may still be called for style matrix (different fields)
        # but NOT for $circ_market_cap alone
        for c in provider.get_market_data.call_args_list:
            assert c[0][0] != ["$circ_market_cap"]

    def test_stub_engine_has_prepare_batch(self):
        stub = RiskEngine.stub()
        stub.prepare_batch({}, None)  # should not raise


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
