"""Tests for ICAnalyzer — annual breakdown and monthly heatmap."""
import numpy as np
import pandas as pd

from report.analytics.ic import ICAnalyzer


class TestAnnualICBreakdown:
    def test_annual_breakdown_structure(self):
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
        assert "regime" in first
        assert first["regime"] in ("bull", "bear", "sideways")


class TestMonthlyHeatmap:
    def test_monthly_heatmap_data(self):
        dates = pd.bdate_range("2020-01-02", "2021-12-30")
        np.random.seed(42)
        daily_ic = pd.DataFrame({
            "date": dates,
            "IC": np.random.randn(len(dates)) * 0.1 - 0.05,
        })
        ic = ICAnalyzer()
        result = ic.compute_monthly_heatmap_data(daily_ic)
        assert len(result) > 0
        assert len(result[0]) == 3  # [year, month, ic_mean]


class TestImports:
    def test_report_imports(self):
        from report.analytics.ic import ICAnalyzer
        from report.analytics.groups import GroupReturnsAnalyzer
        from report.analytics.decay import DecayAnalyzer
        from report.analytics.distribution import DistributionAnalyzer
        from report.scorer import CompositeScorer
        from report.renderer import ReportRenderer
        assert ICAnalyzer is not None
        assert GroupReturnsAnalyzer is not None
        assert DecayAnalyzer is not None
        assert DistributionAnalyzer is not None
        assert CompositeScorer is not None
        assert ReportRenderer is not None
