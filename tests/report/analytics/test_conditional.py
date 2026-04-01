import pandas as pd
import numpy as np
import pytest
from report.analytics.conditional import ConditionalAnalyzer
from report.data_prep import merge_factor_price


def _make_data(n_dates=300, n_stocks=50):
    """Generate synthetic factor + price data with realistic market regimes.

    Prices follow a random walk with injected trends so that the rolling
    60-day cumulative return exceeds +/-10% thresholds, producing bull,
    bear, and range regimes.
    """
    np.random.seed(42)
    dates = pd.bdate_range("2022-01-01", periods=n_dates)

    # Build a market-level daily return series with trend phases
    # Phase 1: bull (+0.3% drift), Phase 2: bear (-0.3% drift), Phase 3: range
    n1 = n_dates // 3
    n2 = n_dates // 3
    n3 = n_dates - n1 - n2
    drift = np.concatenate([
        np.full(n1, 0.003),   # bull phase
        np.full(n2, -0.003),  # bear phase
        np.full(n3, 0.0),     # range phase
    ])
    market_ret = drift + np.random.randn(n_dates) * 0.005
    market_price = 10.0 * np.cumprod(1 + market_ret)

    factor_rows, price_rows = [], []
    for i, d in enumerate(dates):
        for s in [f"S{j:03d}" for j in range(n_stocks)]:
            fv = np.random.randn()
            # Each stock's close is market_price + idiosyncratic noise
            close = market_price[i] * (1 + 0.02 * fv + np.random.randn() * 0.01)
            factor_rows.append({"time": d, "symbol": s, "value": fv})
            price_rows.append({"time": d, "symbol": s, "close": abs(close)})
    return pd.DataFrame(factor_rows), pd.DataFrame(price_rows)


class TestConditionalAnalyzer:
    def test_returns_regime_ic(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ConditionalAnalyzer()
        result = analyzer.compute(merged, price_df=pdf)
        assert "regime_ic" in result
        for regime in ["bull", "bear", "range"]:
            assert regime in result["regime_ic"]
            assert "ic" in result["regime_ic"][regime]
            assert "icir" in result["regime_ic"][regime]

    def test_returns_vol_regime_ic(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ConditionalAnalyzer()
        result = analyzer.compute(merged, price_df=pdf)
        assert "vol_regime_ic" in result
        assert "high" in result["vol_regime_ic"]
        assert "low" in result["vol_regime_ic"]

    def test_regime_distribution_reasonable(self):
        fdf, pdf = _make_data(n_dates=500)
        merged = merge_factor_price(fdf, pdf)
        analyzer = ConditionalAnalyzer()
        result = analyzer.compute(merged, price_df=pdf)
        for regime in ["bull", "bear", "range"]:
            assert result["regime_ic"][regime]["n_days"] > 0

    def test_annual_ic(self):
        fdf, pdf = _make_data(n_dates=500)
        merged = merge_factor_price(fdf, pdf)
        analyzer = ConditionalAnalyzer()
        result = analyzer.compute(merged, price_df=pdf)
        assert "annual_ic" in result
        assert len(result["annual_ic"]) > 0
        assert "regime" in result["annual_ic"][0]

    def test_reserved_fields_null(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ConditionalAnalyzer()
        result = analyzer.compute(merged, price_df=pdf)
        assert result["size_ic"] is None
        assert result["industry_ic"] is None


class TestConditionalCharts:
    def test_all_charts(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ConditionalAnalyzer()
        result = analyzer.compute(merged, price_df=pdf)
        charts = analyzer.generate_charts(result)
        assert "conditional_ic" in charts
        assert "annual_ic" in charts
