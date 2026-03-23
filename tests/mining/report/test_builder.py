"""Tests for ReportDataBuilder — core data loading and IC computation."""
import json
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from mining.report.builder import ReportDataBuilder


@pytest.fixture
def sample_factor_values():
    """Create sample factor values with MultiIndex (datetime, instrument)."""
    dates = pd.bdate_range("2020-01-02", periods=500)
    symbols = [f"SH60000{i}" for i in range(50)]
    idx = pd.MultiIndex.from_product([dates, symbols], names=["datetime", "instrument"])
    np.random.seed(42)
    values = np.random.randn(len(idx)) * 0.02 + 0.03
    return pd.DataFrame({"factor": values}, index=idx)


@pytest.fixture
def sample_price_df(sample_factor_values):
    """Create matching price data as flat DataFrame."""
    idx = sample_factor_values.index
    dates = idx.get_level_values("datetime")
    symbols = idx.get_level_values("instrument")
    np.random.seed(123)
    close = 10.0 + np.cumsum(np.random.randn(len(idx)) * 0.02)
    return pd.DataFrame({
        "time": dates,
        "symbol": symbols,
        "close": close,
    })


class TestDistributionStats:
    def test_compute_distribution_stats(self, sample_factor_values):
        builder = ReportDataBuilder.__new__(ReportDataBuilder)
        stats = builder._compute_distribution_stats(sample_factor_values)
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
        builder = ReportDataBuilder.__new__(ReportDataBuilder)
        stats = builder._compute_distribution_stats(df)
        assert stats["nan_ratio"] > 0
        assert stats["coverage"] < 1.0


class TestAnnualICBreakdown:
    def test_annual_breakdown_structure(self):
        """Annual breakdown should return list of dicts with year, ic_mean, ic_ir, win_rate, regime."""
        dates = pd.bdate_range("2020-01-02", "2022-12-30")
        np.random.seed(42)
        daily_ic = pd.DataFrame({
            "date": dates,
            "IC": np.random.randn(len(dates)) * 0.1 - 0.05,
        })
        builder = ReportDataBuilder.__new__(ReportDataBuilder)
        result = builder._compute_annual_breakdown(daily_ic)
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
        builder = ReportDataBuilder.__new__(ReportDataBuilder)
        result = builder._compute_monthly_heatmap_data(daily_ic)
        assert len(result) > 0
        assert len(result[0]) == 3  # [year, month, ic_mean]
