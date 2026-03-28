"""Tests for DecayAnalyzer -- IC decay, autocorrelation, distribution, charts."""
import pandas as pd
import numpy as np
import pytest
from report.analytics.decay import DecayAnalyzer
from report.data_prep import merge_factor_price


def _make_data(n_dates=200, n_stocks=50):
    np.random.seed(42)
    dates = pd.bdate_range("2023-01-01", periods=n_dates)
    factor_rows, price_rows = [], []
    for d in dates:
        for s in [f"S{i:03d}" for i in range(n_stocks)]:
            fv = np.random.randn()
            close = 10 + 0.05 * fv + np.random.randn() * 0.3
            factor_rows.append({"time": d, "symbol": s, "value": fv})
            price_rows.append({"time": d, "symbol": s, "close": abs(close)})
    return pd.DataFrame(factor_rows), pd.DataFrame(price_rows)


class TestDecayCompute:
    def test_returns_required_keys(self):
        fdf, pdf = _make_data()
        analyzer = DecayAnalyzer()
        result = analyzer.compute(fdf, pdf)
        assert "ic_by_period" in result
        assert "half_life_days" in result
        assert "optimal_rebalance_days" in result
        assert "autocorrelation" in result
        assert "distribution" in result

    def test_includes_2d_period(self):
        fdf, pdf = _make_data()
        analyzer = DecayAnalyzer()
        result = analyzer.compute(fdf, pdf)
        periods = [r["days"] for r in result["ic_by_period"]]
        assert 2 in periods

    def test_six_periods_default(self):
        fdf, pdf = _make_data()
        analyzer = DecayAnalyzer()
        result = analyzer.compute(fdf, pdf)
        assert len(result["ic_by_period"]) == 6  # [1, 2, 5, 10, 20, 60]

    def test_distribution_with_split(self):
        fdf, pdf = _make_data()
        analyzer = DecayAnalyzer()
        result = analyzer.compute(fdf, pdf, split_date="2023-07-01")
        dist = result["distribution"]
        assert "stats_is" in dist
        assert "stats_oos" in dist
        for key in ["mean", "std", "skew", "kurtosis", "coverage", "nan_ratio"]:
            assert key in dist["stats_is"]

    def test_distribution_without_split(self):
        fdf, pdf = _make_data()
        analyzer = DecayAnalyzer()
        result = analyzer.compute(fdf, pdf)
        dist = result["distribution"]
        assert "stats_all" in dist

    def test_optimal_rebalance(self):
        fdf, pdf = _make_data()
        analyzer = DecayAnalyzer()
        result = analyzer.compute(fdf, pdf)
        assert isinstance(result["optimal_rebalance_days"], int)
        assert result["optimal_rebalance_days"] > 0

    def test_autocorrelation_lags(self):
        fdf, pdf = _make_data()
        analyzer = DecayAnalyzer()
        result = analyzer.compute(fdf, pdf)
        lags = [r["lag"] for r in result["autocorrelation"]]
        assert 1 in lags
        assert 5 in lags
        assert 20 in lags


class TestDecayCharts:
    def test_all_charts(self):
        fdf, pdf = _make_data()
        analyzer = DecayAnalyzer()
        result = analyzer.compute(fdf, pdf, split_date="2023-07-01")
        charts = analyzer.generate_charts(result)
        expected = ["ic_decay", "autocorrelation", "distribution", "coverage"]
        for name in expected:
            assert name in charts, f"Missing chart: {name}"
