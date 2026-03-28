"""Tests for ICAnalyzer -- new compute() interface with Pearson IC, t-test, ICIR."""
import pandas as pd
import numpy as np
import pytest
from report.analytics.ic import ICAnalyzer
from report.data_prep import merge_factor_price


def _make_data(n_dates=100, n_stocks=50, signal_strength=0.05):
    """Generate synthetic factor and price data with controllable signal.

    The factor predicts the *next-day* return, so merge_factor_price's
    future_return column will be positively correlated with value when
    signal_strength > 0.
    """
    np.random.seed(42)
    dates = pd.bdate_range("2023-01-01", periods=n_dates)
    stocks = [f"S{i:03d}" for i in range(n_stocks)]
    factor_rows, price_rows = [], []
    # Build prices as a random walk where the daily return has a signal component
    for s in stocks:
        # Pre-generate factor values for all dates
        fvals = np.random.randn(n_dates)
        close = 10.0
        for i, d in enumerate(dates):
            factor_rows.append({"time": d, "symbol": s, "value": fvals[i]})
            price_rows.append({"time": d, "symbol": s, "close": close})
            # Next day return = signal_strength * today's factor + noise
            daily_ret = signal_strength * fvals[i] * 0.01 + np.random.randn() * 0.02
            close = close * (1 + daily_ret)
    return pd.DataFrame(factor_rows), pd.DataFrame(price_rows)


class TestICAnalyzerCompute:
    def test_returns_both_rank_and_pearson(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer()
        result = analyzer.compute(merged, split_date="2023-04-01")
        assert "daily_rank_ic" in result
        assert "daily_pearson_ic" in result
        assert "summary" in result
        assert "is" in result["summary"]
        assert "oos" in result["summary"]

    def test_summary_has_required_fields(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer()
        result = analyzer.compute(merged, split_date="2023-04-01")
        for period in ["is", "oos"]:
            s = result["summary"][period]
            assert "rank_ic_mean" in s
            assert "rank_ic_std" in s
            assert "ic_mean" in s
            assert "icir" in s
            assert "win_rate" in s
            assert "significant_rate" in s
            assert "t_stat" in s
            assert "p_value" in s

    def test_positive_signal_has_positive_ic(self):
        fdf, pdf = _make_data(n_dates=200, signal_strength=0.1)
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        assert result["summary"]["is"]["rank_ic_mean"] > 0

    def test_annual_breakdown(self):
        fdf, pdf = _make_data(n_dates=200)
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        assert "annual" in result
        assert len(result["annual"]) > 0
        assert "year" in result["annual"][0]
        assert "rank_ic" in result["annual"][0]

    def test_monthly_heatmap(self):
        fdf, pdf = _make_data(n_dates=200)
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        assert "monthly_heatmap_data" in result
        if len(result["monthly_heatmap_data"]) > 0:
            assert len(result["monthly_heatmap_data"][0]) == 3

    def test_icir_separate_for_is_oos(self):
        fdf, pdf = _make_data(n_dates=200, signal_strength=0.1)
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        is_icir = result["summary"]["is"]["icir"]
        oos_icir = result["summary"]["oos"]["icir"]
        # Both should be numeric; IS should have positive ICIR given positive signal
        assert isinstance(is_icir, float)
        assert isinstance(oos_icir, float)
        assert is_icir > 0

    def test_ttest_significance(self):
        fdf, pdf = _make_data(n_dates=200, signal_strength=0.15)
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        # With strong signal, p-value should be low
        assert result["summary"]["is"]["p_value"] < 0.1

    def test_no_regime_lookup(self):
        """Ensure _REGIME_LOOKUP is removed."""
        import report.analytics.ic as ic_module
        assert not hasattr(ic_module, "_REGIME_LOOKUP")

    def test_daily_ic_series_types(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer()
        result = analyzer.compute(merged, split_date="2023-04-01")
        assert isinstance(result["daily_rank_ic"], pd.Series)
        assert isinstance(result["daily_pearson_ic"], pd.Series)


class TestICAnalyzerCharts:
    def test_all_charts_generated(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer()
        result = analyzer.compute(merged, split_date="2023-04-01")
        charts = analyzer.generate_charts(result)
        expected = ["ic_timeseries", "ic_distribution", "rolling_ic",
                    "cumulative_ic", "monthly_heatmap"]
        for name in expected:
            assert name in charts, f"Missing chart: {name}"

    def test_charts_are_figures(self):
        import plotly.graph_objects as go
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ICAnalyzer("test_factor")
        result = analyzer.compute(merged, split_date="2023-04-01")
        charts = analyzer.generate_charts(result)
        for name, fig in charts.items():
            assert isinstance(fig, go.Figure), f"{name} is not a Figure"


class TestICAnalyzerBackwardCompat:
    def test_compute_ic_returns_old_format(self):
        fdf, pdf = _make_data()
        analyzer = ICAnalyzer("test")
        result = analyzer.compute_ic(fdf, pdf, split_date="2023-04-01")
        assert "ic_all" in result
        assert "rolling_ic" in result
        assert "ic_train" in result
        assert "ic_test" in result
        assert isinstance(result["rolling_ic"], pd.DataFrame)
        assert "date" in result["rolling_ic"].columns
        assert "IC" in result["rolling_ic"].columns

    def test_compute_ic_with_no_split_date(self):
        fdf, pdf = _make_data()
        analyzer = ICAnalyzer("test")
        result = analyzer.compute_ic(fdf, pdf)
        assert "ic_all" in result
        assert "rolling_ic" in result

    def test_legacy_annual_breakdown(self):
        dates = pd.bdate_range("2020-01-02", "2022-12-30")
        np.random.seed(42)
        daily_ic = pd.DataFrame({
            "date": dates,
            "IC": np.random.randn(len(dates)) * 0.1 - 0.05,
        })
        ic = ICAnalyzer()
        result = ic.compute_annual_breakdown(daily_ic)
        assert len(result) >= 2
        first = result[0]
        assert "year" in first
        assert "ic_mean" in first
        assert "ic_ir" in first
        assert "win_rate" in first
        # regime key should NOT be present (removed)
        assert "regime" not in first

    def test_legacy_monthly_heatmap_data(self):
        dates = pd.bdate_range("2020-01-02", "2021-12-30")
        np.random.seed(42)
        daily_ic = pd.DataFrame({
            "date": dates,
            "IC": np.random.randn(len(dates)) * 0.1 - 0.05,
        })
        ic = ICAnalyzer()
        result = ic.compute_monthly_heatmap_data(daily_ic)
        assert len(result) > 0
        assert len(result[0]) == 3

    def test_legacy_ic_summary(self):
        dates = pd.bdate_range("2020-01-02", "2022-12-30")
        np.random.seed(42)
        daily_ic = pd.DataFrame({
            "date": dates,
            "IC": np.random.randn(len(dates)) * 0.1 - 0.05,
        })
        ic = ICAnalyzer()
        is_sum, oos_sum = ic.compute_ic_summary(daily_ic, split_date="2021-06-01")
        assert "ic_mean" in is_sum
        assert "ic_ir" in is_sum
        assert "n_days" in is_sum
        assert is_sum["n_days"] > 0
        assert oos_sum["n_days"] > 0
