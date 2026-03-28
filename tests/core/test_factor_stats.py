"""Tests for core.factor_stats shared statistical functions."""
import numpy as np
import pandas as pd
import pytest
from scipy.stats import spearmanr

from core.factor_stats import (
    daily_cross_sectional_ic,
    distribution_stats,
    estimate_half_life,
    factor_autocorrelation,
    ic_by_year,
    ic_summary,
    incremental_ic,
    monotonicity,
    multiindex_to_flat,
    pairwise_cross_sectional_corr,
    quintile_returns,
)


# ──────────────────── Fixtures ────────────────────


def _make_flat(n_dates=50, n_symbols=100, seed=42):
    """Create a flat factor DataFrame with [time, symbol, value]."""
    rng = np.random.RandomState(seed)
    dates = pd.bdate_range("2024-01-01", periods=n_dates)
    symbols = [f"S{i:04d}" for i in range(n_symbols)]
    rows = []
    for d in dates:
        for s in symbols:
            rows.append({"time": d, "symbol": s, "value": rng.randn()})
    return pd.DataFrame(rows)


def _make_returns(factor_df, ic_target=0.05, seed=99):
    """Create returns correlated with factor values at target IC level."""
    rng = np.random.RandomState(seed)
    ret = factor_df.copy()
    noise = rng.randn(len(ret))
    ret["value"] = factor_df["value"] * ic_target + noise * (1 - abs(ic_target))
    return ret


def _make_multiindex(n_dates=10, n_symbols=20, seed=42):
    """Create a Qlib-style MultiIndex DataFrame."""
    rng = np.random.RandomState(seed)
    dates = pd.bdate_range("2024-01-01", periods=n_dates)
    instruments = [f"S{i:04d}" for i in range(n_symbols)]
    idx = pd.MultiIndex.from_product(
        [dates, instruments], names=["datetime", "instrument"]
    )
    return pd.DataFrame({"alpha_expr": rng.randn(len(idx))}, index=idx)


# ──────────────────── multiindex_to_flat ────────────────────


class TestMultiindexToFlat:
    def test_basic_conversion(self):
        mi = _make_multiindex()
        flat = multiindex_to_flat(mi)
        assert list(flat.columns) == ["time", "symbol", "value"]
        assert len(flat) == 10 * 20

    def test_empty_dataframe(self):
        mi = pd.DataFrame(columns=["x"], index=pd.MultiIndex.from_tuples(
            [], names=["datetime", "instrument"]
        ))
        flat = multiindex_to_flat(mi)
        assert list(flat.columns) == ["time", "symbol", "value"]
        assert len(flat) == 0

    def test_values_preserved(self):
        mi = _make_multiindex(n_dates=2, n_symbols=3, seed=7)
        flat = multiindex_to_flat(mi)
        assert len(flat) == 6
        # Values should be identical (just restructured)
        mi_vals = sorted(mi.iloc[:, 0].values)
        flat_vals = sorted(flat["value"].values)
        np.testing.assert_array_almost_equal(mi_vals, flat_vals)


# ──────────────────── daily_cross_sectional_ic ────────────────────


class TestDailyCrossSectionalIC:
    def test_basic_ic(self):
        factor_df = _make_flat()
        returns_df = _make_returns(factor_df, ic_target=0.3)
        ics = daily_cross_sectional_ic(factor_df, returns_df, min_obs=30)
        assert len(ics) > 0
        assert ics.mean() > 0  # Positive correlation expected

    def test_min_obs_filter(self):
        factor_df = _make_flat(n_symbols=5)  # Very few symbols
        returns_df = _make_returns(factor_df)
        ics = daily_cross_sectional_ic(factor_df, returns_df, min_obs=30)
        assert len(ics) == 0  # All dates filtered out

    def test_empty_input(self):
        empty = pd.DataFrame(columns=["time", "symbol", "value"])
        ics = daily_cross_sectional_ic(empty, empty)
        assert len(ics) == 0

    def test_pearson_method(self):
        factor_df = _make_flat()
        returns_df = _make_returns(factor_df, ic_target=0.3)
        ics = daily_cross_sectional_ic(
            factor_df, returns_df, method="pearson", min_obs=30
        )
        assert len(ics) > 0

    def test_returns_series_index(self):
        factor_df = _make_flat()
        returns_df = _make_returns(factor_df, ic_target=0.3)
        ics = daily_cross_sectional_ic(factor_df, returns_df)
        assert isinstance(ics.index, pd.DatetimeIndex)


# ──────────────────── ic_summary ────────────────────


class TestICSummary:
    def test_basic(self):
        ics = pd.Series([0.03, 0.05, -0.01, 0.02, 0.04])
        result = ic_summary(ics)
        assert "ic_mean" in result
        assert "ic_std" in result
        assert "ic_ir" in result
        assert "ic_win_rate" in result
        assert abs(result["ic_mean"] - ics.mean()) < 1e-8

    def test_empty(self):
        result = ic_summary(pd.Series(dtype=float))
        assert np.isnan(result["ic_mean"])

    def test_win_rate(self):
        ics = pd.Series([0.01, 0.02, -0.01, 0.03])
        result = ic_summary(ics)
        assert result["ic_win_rate"] == 0.75


# ──────────────────── ic_by_year ────────────────────


class TestICByYear:
    def test_basic(self):
        dates = pd.date_range("2020-01-01", "2022-12-31", freq="B")
        ics = pd.Series(np.random.randn(len(dates)) * 0.03, index=dates)
        result = ic_by_year(ics)
        assert set(result.keys()) == {2020, 2021, 2022}

    def test_empty(self):
        result = ic_by_year(pd.Series(dtype=float))
        assert result == {}


# ──────────────────── pairwise_cross_sectional_corr ────────────────────


class TestPairwiseCrossSectionalCorr:
    def test_identical_factors(self):
        df = _make_flat(n_dates=30)
        corr = pairwise_cross_sectional_corr(df, df, min_obs=30)
        assert corr is not None
        assert abs(corr - 1.0) < 0.01

    def test_independent_factors(self):
        df_a = _make_flat(seed=1)
        df_b = _make_flat(seed=999)
        corr = pairwise_cross_sectional_corr(df_a, df_b, min_obs=30)
        if corr is not None:
            assert abs(corr) < 0.2  # Should be near zero

    def test_insufficient_data(self):
        df_a = _make_flat(n_dates=2, n_symbols=5)
        df_b = _make_flat(n_dates=2, n_symbols=5, seed=99)
        corr = pairwise_cross_sectional_corr(df_a, df_b, min_obs=30)
        assert corr is None


# ──────────────────── quintile_returns ────────────────────


class TestQuintileReturns:
    def test_basic(self):
        factor_df = _make_flat(n_dates=50, n_symbols=200)
        returns_df = _make_returns(factor_df, ic_target=0.5)
        q_rets, ls_rets = quintile_returns(factor_df, returns_df)
        assert len(q_rets) == 5
        assert "q1" in q_rets and "q5" in q_rets
        assert len(ls_rets) > 0

    def test_empty(self):
        empty = pd.DataFrame(columns=["time", "symbol", "value"])
        q_rets, ls_rets = quintile_returns(empty, empty)
        assert len(q_rets) == 5
        assert all(np.isnan(v) for v in q_rets.values())

    def test_custom_quantiles(self):
        factor_df = _make_flat(n_dates=50, n_symbols=200)
        returns_df = _make_returns(factor_df)
        q_rets, ls_rets = quintile_returns(
            factor_df, returns_df, n_quantiles=10
        )
        assert len(q_rets) == 10

    def test_monotonic_with_strong_signal(self):
        """With strong positive IC, Q5 should beat Q1."""
        factor_df = _make_flat(n_dates=50, n_symbols=200)
        returns_df = _make_returns(factor_df, ic_target=2.0, seed=42)
        q_rets, _ = quintile_returns(factor_df, returns_df)
        # With very strong signal, expect Q5 > Q1
        assert q_rets["q5"] > q_rets["q1"]


# ──────────────────── monotonicity ────────────────────


class TestMonotonicity:
    def test_perfect_increasing(self):
        q_rets = {"q1": 0.01, "q2": 0.02, "q3": 0.03, "q4": 0.04, "q5": 0.05}
        result = monotonicity(q_rets)
        assert abs(result - 1.0) < 1e-8

    def test_perfect_decreasing(self):
        q_rets = {"q1": 0.05, "q2": 0.04, "q3": 0.03, "q4": 0.02, "q5": 0.01}
        result = monotonicity(q_rets)
        assert abs(result - (-1.0)) < 1e-8

    def test_with_nan(self):
        q_rets = {"q1": 0.01, "q2": np.nan, "q3": 0.03, "q4": 0.04, "q5": 0.05}
        result = monotonicity(q_rets)
        assert not np.isnan(result)

    def test_too_few_values(self):
        q_rets = {"q1": 0.01, "q2": np.nan, "q3": np.nan, "q4": np.nan, "q5": np.nan}
        result = monotonicity(q_rets)
        assert np.isnan(result)


# ──────────────────── estimate_half_life ────────────────────


class TestEstimateHalfLife:
    def test_basic(self):
        ic_decay = {1: 0.05, 5: 0.03, 10: 0.02, 20: 0.01}
        hl = estimate_half_life(ic_decay)
        assert not np.isnan(hl)
        assert 1 < hl < 20

    def test_exact_half(self):
        ic_decay = {1: 0.10, 5: 0.05}  # Exact half at day 5
        hl = estimate_half_life(ic_decay)
        assert abs(hl - 5.0) < 1e-8

    def test_no_decay(self):
        ic_decay = {1: 0.05, 5: 0.05, 10: 0.05}
        hl = estimate_half_life(ic_decay)
        assert np.isnan(hl)

    def test_single_point(self):
        ic_decay = {1: 0.05}
        hl = estimate_half_life(ic_decay)
        assert np.isnan(hl)


# ──────────────────── factor_autocorrelation ────────────────────


class TestFactorAutocorrelation:
    def test_basic(self):
        factor_df = _make_flat(n_dates=30)
        result = factor_autocorrelation(factor_df, lags=[1, 5])
        assert len(result) > 0
        assert all("lag" in r and "corr" in r for r in result)

    def test_lag1_near_zero_for_random(self):
        factor_df = _make_flat(n_dates=30, seed=123)
        result = factor_autocorrelation(factor_df, lags=[1])
        if result:
            # Random factor should have near-zero autocorrelation
            assert abs(result[0]["corr"]) < 0.5

    def test_custom_lags(self):
        factor_df = _make_flat(n_dates=50)
        result = factor_autocorrelation(factor_df, lags=[1, 2, 3])
        lags_returned = [r["lag"] for r in result]
        assert all(l in [1, 2, 3] for l in lags_returned)


# ──────────────────── distribution_stats ────────────────────


class TestDistributionStats:
    def test_basic(self):
        df = _make_flat()
        result = distribution_stats(df)
        assert "mean" in result
        assert "std" in result
        assert "skew" in result
        assert "kurtosis" in result
        assert "coverage" in result
        assert result["coverage"] > 0

    def test_with_nans(self):
        df = _make_flat()
        df.loc[df.index[:100], "value"] = np.nan
        result = distribution_stats(df)
        assert result["nan_ratio"] > 0
        assert result["coverage"] < 1.0

    def test_too_few_observations(self):
        df = pd.DataFrame({
            "time": [pd.Timestamp("2024-01-01")] * 5,
            "symbol": [f"S{i}" for i in range(5)],
            "value": [1.0, 2.0, np.nan, np.nan, np.nan],
        })
        result = distribution_stats(df)
        assert result["coverage"] == 0.0  # Less than 10 non-nan


# ──────────────────── incremental_ic ────────────────────


class TestIncrementalIC:
    def test_no_library(self):
        factor_df = _make_flat()
        returns_df = _make_returns(factor_df)
        result_ic, result_icir = incremental_ic(factor_df, returns_df, {})
        assert result_ic is None

    def test_with_library(self):
        factor_df = _make_flat(n_dates=30, n_symbols=100)
        returns_df = _make_returns(factor_df, ic_target=0.5)
        lib = {"f001": _make_flat(n_dates=30, n_symbols=100, seed=77)}
        result_ic, result_icir = incremental_ic(
            factor_df, returns_df, lib, min_obs=30
        )
        # Should return some value with sufficient data
        if result_ic is not None:
            assert isinstance(result_ic, float)

    def test_insufficient_data(self):
        factor_df = _make_flat(n_dates=5, n_symbols=10)
        returns_df = _make_returns(factor_df)
        lib = {"f001": _make_flat(n_dates=5, n_symbols=10, seed=77)}
        result_ic, result_icir = incremental_ic(
            factor_df, returns_df, lib, min_obs=30
        )
        assert result_ic is None
