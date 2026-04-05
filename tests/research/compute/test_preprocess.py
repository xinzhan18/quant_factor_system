"""Tests for Preprocessor -- vectorized cross-sectional preprocessing."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.compute.preprocess import Preprocessor


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


def _make_factor_df(n_dates=10, n_stocks=5, seed=42):
    """Build a factor DataFrame with (datetime, instrument) MultiIndex."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2024-01-01", periods=n_dates)
    stocks = [f"SH60000{i}" for i in range(n_stocks)]
    idx = pd.MultiIndex.from_product(
        [dates, stocks], names=["datetime", "instrument"]
    )
    values = rng.standard_normal(len(idx))
    return pd.DataFrame({"factor": values}, index=idx)


def _make_market_df(n_dates=10, n_stocks=5, seed=42):
    """Build a market DataFrame with $close and $volume columns."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2024-01-01", periods=n_dates)
    stocks = [f"SH60000{i}" for i in range(n_stocks)]
    idx = pd.MultiIndex.from_product(
        [dates, stocks], names=["datetime", "instrument"]
    )
    n = len(idx)
    return pd.DataFrame(
        {
            "$close": 100 + rng.standard_normal(n).cumsum(),
            "$volume": rng.integers(1_000_000, 10_000_000, size=n).astype(float),
        },
        index=idx,
    )


@pytest.fixture
def factor_df():
    return _make_factor_df()


@pytest.fixture
def market_df():
    return _make_market_df()


# -----------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------


class TestPreprocessor:
    def test_run_returns_same_shape(self, factor_df):
        pp = Preprocessor()
        result = pp.run(factor_df, tradability_check=False)
        assert result.shape == factor_df.shape
        assert result.index.equals(factor_df.index)

    def test_winsorize_clips_outliers(self):
        """Extreme outliers should be clipped after winsorization."""
        dates = pd.bdate_range("2024-01-01", periods=1)
        stocks = [f"S{i}" for i in range(100)]
        idx = pd.MultiIndex.from_product(
            [dates, stocks], names=["datetime", "instrument"]
        )
        # Normal values plus one extreme outlier
        rng = np.random.default_rng(42)
        values = rng.standard_normal(100)
        values[0] = 100.0  # extreme outlier
        df = pd.DataFrame({"factor": values}, index=idx)

        pp = Preprocessor(sigma=3.0)
        # Test winsorize step only (before zscore which rescales)
        winsorized = pp._winsorize(df)

        # The outlier should have been clipped well below 100
        assert winsorized["factor"].max() < 50.0
        # And the clipped value should be near the 3-sigma bound
        # pandas .std() uses ddof=1 by default
        s = pd.Series(values)
        expected_upper = s.mean() + 3.0 * s.std()
        assert winsorized["factor"].max() <= expected_upper + 0.01

    def test_zscore_per_date(self, factor_df):
        """After zscore, each date cross-section should have ~0 mean and ~1 std."""
        pp = Preprocessor()
        result = pp.run(factor_df, tradability_check=False)

        for date, group in result.groupby(level="datetime"):
            vals = group["factor"].dropna()
            if len(vals) > 1:
                assert abs(vals.mean()) < 1e-10, f"Mean not ~0 on {date}"
                assert abs(vals.std() - 1.0) < 0.2, f"Std not ~1 on {date}"

    def test_tradability_masks_zero_volume(self, factor_df, market_df):
        """Stocks with zero volume should have NaN factor values."""
        # Set volume to zero for one stock on all dates
        market_mod = market_df.copy()
        mask = market_mod.index.get_level_values("instrument") == "SH600000"
        market_mod.loc[mask, "$volume"] = 0.0

        pp = Preprocessor()
        result = pp.run(factor_df, market_df=market_mod, tradability_check=True)

        zero_vol = result.loc[mask, "factor"]
        assert zero_vol.isna().all(), "Zero-volume stocks should be NaN"

    def test_tradability_masks_nan_close(self, factor_df, market_df):
        """Stocks with NaN close should have NaN factor values."""
        market_mod = market_df.copy()
        mask = market_mod.index.get_level_values("instrument") == "SH600001"
        market_mod.loc[mask, "$close"] = np.nan

        pp = Preprocessor()
        result = pp.run(factor_df, market_df=market_mod, tradability_check=True)

        nan_close = result.loc[mask, "factor"]
        assert nan_close.isna().all(), "NaN-close stocks should be NaN"

    def test_neutralize_by_group(self):
        """After neutralization, group means per date should be ~0."""
        dates = pd.bdate_range("2024-01-01", periods=5)
        stocks = [f"S{i}" for i in range(6)]
        idx = pd.MultiIndex.from_product(
            [dates, stocks], names=["datetime", "instrument"]
        )
        rng = np.random.default_rng(42)
        factor_df = pd.DataFrame(
            {"factor": rng.standard_normal(len(idx))}, index=idx
        )
        # Group assignment: first 3 stocks in group A, last 3 in group B
        groups = ["A", "A", "A", "B", "B", "B"] * 5
        market_df = pd.DataFrame({"industry": groups}, index=idx)

        pp = Preprocessor(neutralize_col="industry")
        result = pp.run(factor_df, market_df=market_df, tradability_check=False)

        # Check group means are approximately zero per date
        combined = result.copy()
        combined["industry"] = groups
        for (date, ind), grp in combined.groupby(
            [combined.index.get_level_values("datetime"), "industry"]
        ):
            vals = grp["factor"].dropna()
            if len(vals) > 0:
                assert abs(vals.mean()) < 1e-10, f"Group mean not ~0 for {date}/{ind}"

    def test_no_tradability_without_market_df(self, factor_df):
        """Tradability check without market_df should be a no-op."""
        pp = Preprocessor()
        result = pp.run(factor_df, market_df=None, tradability_check=True)
        # Should not crash -- tradability skipped
        assert result.shape == factor_df.shape

    def test_custom_sigma(self):
        """Different sigma values should change winsorization bounds."""
        dates = pd.bdate_range("2024-01-01", periods=1)
        stocks = [f"S{i}" for i in range(50)]
        idx = pd.MultiIndex.from_product(
            [dates, stocks], names=["datetime", "instrument"]
        )
        rng = np.random.default_rng(42)
        values = rng.standard_normal(50)
        values[0] = 50.0  # outlier
        df = pd.DataFrame({"factor": values}, index=idx)

        pp_tight = Preprocessor(sigma=1.0)
        pp_loose = Preprocessor(sigma=5.0)

        result_tight = pp_tight._winsorize(df)
        result_loose = pp_loose._winsorize(df)

        # Tight sigma should clip more aggressively
        assert result_tight["factor"].max() < result_loose["factor"].max()
