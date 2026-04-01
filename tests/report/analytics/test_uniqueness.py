import pandas as pd
import numpy as np
import pytest
from report.analytics.uniqueness import UniquenessAnalyzer


def _make_factor_values(n_dates=100, n_stocks=50, n_factors=5):
    np.random.seed(42)
    dates = pd.bdate_range("2023-01-01", periods=n_dates)
    target_rows = []
    lib_factors = {}
    base_signal = {}
    for d in dates:
        for s in [f"S{i:03d}" for i in range(n_stocks)]:
            v = np.random.randn()
            target_rows.append({"time": d, "symbol": s, "value": v})
            base_signal[(d, s)] = v
    target_df = pd.DataFrame(target_rows)

    for fid in range(n_factors):
        rows = []
        for d in dates:
            for s in [f"S{i:03d}" for i in range(n_stocks)]:
                if fid == 0:
                    v = base_signal[(d, s)] * 0.9 + np.random.randn() * 0.1
                else:
                    v = np.random.randn()
                rows.append({"time": d, "symbol": s, "value": v})
        lib_factors[f"F{fid:03d}"] = pd.DataFrame(rows)
    return target_df, lib_factors


class TestUniquenessCompute:
    def test_returns_required_keys(self):
        target, lib = _make_factor_values()
        analyzer = UniquenessAnalyzer()
        result = analyzer.compute(target, lib)
        assert "max_corr" in result
        assert "max_corr_factor" in result
        assert "top5_correlated" in result

    def test_high_correlation_detected(self):
        target, lib = _make_factor_values()
        analyzer = UniquenessAnalyzer()
        result = analyzer.compute(target, lib)
        assert result["max_corr"] > 0.5
        assert result["max_corr_factor"] == "F000"

    def test_empty_library(self):
        target, _ = _make_factor_values()
        analyzer = UniquenessAnalyzer()
        result = analyzer.compute(target, {})
        assert result["max_corr"] == 0.0
        assert result["top5_correlated"] == []

    def test_top5_sorted(self):
        target, lib = _make_factor_values(n_factors=10)
        analyzer = UniquenessAnalyzer()
        result = analyzer.compute(target, lib)
        corrs = [x["corr"] for x in result["top5_correlated"]]
        assert corrs == sorted(corrs, reverse=True)
        assert len(result["top5_correlated"]) <= 5


class TestUniquenessCharts:
    def test_correlation_bar(self):
        target, lib = _make_factor_values()
        analyzer = UniquenessAnalyzer()
        result = analyzer.compute(target, lib)
        charts = analyzer.generate_charts(result)
        assert "correlation_bar" in charts

    def test_empty_library_chart(self):
        target, _ = _make_factor_values()
        analyzer = UniquenessAnalyzer()
        result = analyzer.compute(target, {})
        charts = analyzer.generate_charts(result)
        assert "correlation_bar" in charts
