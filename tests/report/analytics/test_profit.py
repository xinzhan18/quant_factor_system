import pandas as pd
import numpy as np
import pytest
from report.analytics.profit import ProfitAnalyzer
from report.data_prep import merge_factor_price


def _make_data(n_dates=200, n_stocks=50, signal_strength=0.05):
    np.random.seed(42)
    dates = pd.bdate_range("2023-01-01", periods=n_dates)
    factor_rows, price_rows = [], []
    for d in dates:
        for s in [f"S{i:03d}" for i in range(n_stocks)]:
            fv = np.random.randn()
            close = 10 + signal_strength * fv + np.random.randn() * 0.3
            factor_rows.append({"time": d, "symbol": s, "value": fv})
            price_rows.append({"time": d, "symbol": s, "close": abs(close)})
    return pd.DataFrame(factor_rows), pd.DataFrame(price_rows)


class TestProfitAnalyzerCompute:
    def test_returns_required_keys(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ProfitAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        assert "stats" in result
        assert "ls_stats" in result
        assert "monotonicity" in result
        assert "page_test_pvalue" in result
        assert "annual_group_returns" in result

    def test_stats_has_new_metrics(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ProfitAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        q1 = result["stats"][0]
        assert "sortino" in q1
        assert "calmar" in q1
        assert "max_dd_duration" in q1

    def test_five_groups(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ProfitAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        assert len(result["stats"]) == 5

    def test_page_trend_test(self):
        fdf, pdf = _make_data(signal_strength=0.2)
        merged = merge_factor_price(fdf, pdf)
        analyzer = ProfitAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        assert isinstance(result["page_test_pvalue"], float)
        assert 0 <= result["page_test_pvalue"] <= 1

    def test_long_short_contribution(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ProfitAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        assert "long_contribution" in result
        assert "short_contribution" in result

    def test_annual_group_returns(self):
        fdf, pdf = _make_data(n_dates=300)
        merged = merge_factor_price(fdf, pdf)
        analyzer = ProfitAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        annual = result["annual_group_returns"]
        assert len(annual) > 0
        assert "year" in annual[0]


class TestProfitAnalyzerCharts:
    def test_all_charts_generated(self):
        fdf, pdf = _make_data()
        merged = merge_factor_price(fdf, pdf)
        analyzer = ProfitAnalyzer()
        result = analyzer.compute(merged, split_date="2023-07-01")
        charts = analyzer.generate_charts(result)
        expected = ["quintile_bar", "cumulative_returns", "long_short", "annual_group_returns"]
        for name in expected:
            assert name in charts, f"Missing chart: {name}"
