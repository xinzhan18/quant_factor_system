"""Tests for risk/normalization.py."""

import numpy as np
import pandas as pd
import pytest

from research.risk.normalization import cross_sectional_normalize


def _make_series(n_dates=50, n_stocks=100, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2022-01-01", periods=n_dates)
    stocks = [f"S{i:03d}" for i in range(n_stocks)]
    idx = pd.MultiIndex.from_product([dates, stocks], names=["datetime", "instrument"])
    values = rng.normal(10, 5, size=len(idx))
    return pd.Series(values, index=idx, name="value")


class TestCrossSectionalNormalize:
    def test_output_shape(self):
        s = _make_series()
        result = cross_sectional_normalize(s)
        assert len(result) == len(s)

    def test_mean_near_zero(self):
        s = _make_series()
        result = cross_sectional_normalize(s)
        for date in result.index.get_level_values(0).unique()[:10]:
            day_vals = result.loc[date].dropna()
            assert abs(day_vals.mean()) < 0.01

    def test_std_near_one(self):
        s = _make_series()
        result = cross_sectional_normalize(s)
        for date in result.index.get_level_values(0).unique()[:10]:
            day_vals = result.loc[date].dropna()
            assert abs(day_vals.std() - 1.0) < 0.15

    def test_outliers_clipped(self):
        s = _make_series()
        s.iloc[0] = 1e6  # extreme outlier
        result = cross_sectional_normalize(s, sigma=3.0)
        # After winsorize + z-score, extreme outlier should be bounded
        # The exact value depends on the distribution, but should be finite and bounded
        assert np.isfinite(result.iloc[0])
        assert abs(result.iloc[0]) < 4  # within ~4 std after re-normalization

    def test_empty_series(self):
        s = pd.Series(dtype=float)
        result = cross_sectional_normalize(s)
        assert result.empty

    def test_nan_preserved(self):
        s = _make_series(n_dates=5, n_stocks=10)
        s.iloc[3] = np.nan
        result = cross_sectional_normalize(s)
        assert pd.isna(result.iloc[3])
