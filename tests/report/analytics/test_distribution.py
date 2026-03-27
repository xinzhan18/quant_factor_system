"""Tests for DistributionAnalyzer."""
import numpy as np
import pandas as pd

from report.analytics.distribution import DistributionAnalyzer


class TestDistributionStats:
    def test_compute_stats(self):
        dates = pd.bdate_range("2020-01-02", periods=500)
        symbols = [f"SH60000{i}" for i in range(50)]
        idx = pd.MultiIndex.from_product([dates, symbols], names=["datetime", "instrument"])
        np.random.seed(42)
        values = np.random.randn(len(idx)) * 0.02 + 0.03
        df = pd.DataFrame({"factor": values}, index=idx)

        dist = DistributionAnalyzer()
        stats = dist.compute_stats(df)
        assert "mean" in stats
        assert "std" in stats
        assert "skewness" in stats
        assert "kurtosis" in stats
        assert "coverage" in stats
        assert "nan_ratio" in stats
        assert 0 <= stats["coverage"] <= 1

    def test_distribution_with_nans(self):
        dates = pd.bdate_range("2020-01-02", periods=10)
        symbols = ["A", "B"]
        idx = pd.MultiIndex.from_product([dates, symbols], names=["datetime", "instrument"])
        values = [1.0, 2.0, np.nan, 3.0] * 5
        df = pd.DataFrame({"factor": values}, index=idx)

        dist = DistributionAnalyzer()
        stats = dist.compute_stats(df)
        assert stats["nan_ratio"] > 0
        assert stats["coverage"] < 1.0
