"""Tests for OpsAdapter — pandas-based operator wrappers for panel DataFrames.

All ops accept pd.Series with (datetime, instrument) MultiIndex.
Time-series ops compute per instrument (groupby instrument).
Cross-sectional ops compute per date (groupby datetime).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mining.ops_adapter import OpsAdapter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def panel_series() -> pd.Series:
    """30 business days × 3 instruments, random close prices, seed=42."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2024-01-01", periods=30)
    instruments = ["A", "B", "C"]

    index = pd.MultiIndex.from_product(
        [dates, instruments], names=["datetime", "instrument"]
    )
    data = 100 + rng.standard_normal(len(index)).cumsum()
    return pd.Series(data, index=index, name="close")


@pytest.fixture(scope="module")
def panel_returns(panel_series) -> pd.Series:
    """Log returns computed per instrument (no NaN leakage across instruments)."""
    def _log_ret(s):
        return np.log(s).diff()
    return panel_series.groupby(level="instrument").transform(_log_ret)


@pytest.fixture(scope="module")
def ops() -> OpsAdapter:
    return OpsAdapter()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_series(result: pd.Series, reference: pd.Series) -> None:
    """Assert result is a pd.Series with same index as reference."""
    assert isinstance(result, pd.Series), f"Expected pd.Series, got {type(result)}"
    pd.testing.assert_index_equal(result.index, reference.index)


# ---------------------------------------------------------------------------
# Time-series ops
# ---------------------------------------------------------------------------

class TestStd:
    def test_return_type_and_index(self, ops, panel_series):
        result = ops.std(panel_series, 5)
        _check_series(result, panel_series)

    def test_nan_for_initial_window(self, ops, panel_series):
        result = ops.std(panel_series, 10)
        # First 9 rows of each instrument should be NaN (window-1)
        for inst in ["A", "B", "C"]:
            inst_vals = result.xs(inst, level="instrument")
            assert inst_vals.iloc[:9].isna().all(), (
                f"Expected NaN for first 9 rows of instrument {inst}"
            )
            assert inst_vals.iloc[9:].notna().all(), (
                f"Expected non-NaN after window for instrument {inst}"
            )

    def test_instruments_independent(self, ops, panel_series):
        """Each instrument's rolling window is computed independently."""
        result = ops.std(panel_series, 5)
        a = result.xs("A", level="instrument")
        b = result.xs("B", level="instrument")
        assert not a.equals(b)


class TestMean:
    def test_return_type_and_index(self, ops, panel_series):
        result = ops.mean(panel_series, 5)
        _check_series(result, panel_series)

    def test_nan_for_initial_window(self, ops, panel_series):
        result = ops.mean(panel_series, 10)
        for inst in ["A", "B", "C"]:
            inst_vals = result.xs(inst, level="instrument")
            assert inst_vals.iloc[:9].isna().all()
            assert inst_vals.iloc[9:].notna().all()

    def test_single_period_equals_value(self, ops, panel_series):
        """mean with window=1 should return the original series."""
        result = ops.mean(panel_series, 1)
        pd.testing.assert_series_equal(result, panel_series, check_names=False)


class TestTsDecay:
    def test_return_type_and_index(self, ops, panel_series):
        result = ops.ts_decay(panel_series, 5)
        _check_series(result, panel_series)

    def test_nan_for_initial_window(self, ops, panel_series):
        result = ops.ts_decay(panel_series, 10)
        for inst in ["A", "B", "C"]:
            inst_vals = result.xs(inst, level="instrument")
            assert inst_vals.iloc[:9].isna().all()

    def test_recency_weighted(self, ops):
        """WMA with ascending values should exceed simple mean."""
        dates = pd.bdate_range("2024-01-01", periods=5)
        idx = pd.MultiIndex.from_product([dates, ["X"]], names=["datetime", "instrument"])
        s = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0], index=idx)
        result = ops.ts_decay(s, 5)
        val = result.xs("X", level="instrument").iloc[-1]
        simple_mean = 3.0
        assert val > simple_mean, f"WMA {val} should exceed simple mean {simple_mean}"


class TestTsAutoCorr:
    def test_return_type_and_index(self, ops, panel_series):
        result = ops.ts_auto_corr(panel_series, 10, lag=1)
        _check_series(result, panel_series)

    def test_nan_for_initial_window(self, ops, panel_series):
        result = ops.ts_auto_corr(panel_series, 10, lag=1)
        for inst in ["A", "B", "C"]:
            inst_vals = result.xs(inst, level="instrument")
            # First (window-1) values should be NaN
            assert inst_vals.iloc[:9].isna().all()

    def test_bounded(self, ops, panel_series):
        result = ops.ts_auto_corr(panel_series, 10, lag=1)
        valid = result.dropna()
        assert (valid.abs() <= 1.0 + 1e-9).all(), "Autocorrelation must be in [-1, 1]"


class TestRealizedVol:
    def test_return_type_and_index(self, ops, panel_returns):
        result = ops.realized_vol(panel_returns, 10)
        _check_series(result, panel_returns)

    def test_non_negative(self, ops, panel_returns):
        result = ops.realized_vol(panel_returns, 10)
        valid = result.dropna()
        assert (valid >= 0).all(), "Realized vol must be non-negative"

    def test_annualized(self, ops):
        """RMS-based annualized vol of constant 1% daily returns = sqrt(252)*0.01."""
        dates = pd.bdate_range("2024-01-01", periods=20)
        idx = pd.MultiIndex.from_product([dates, ["X"]], names=["datetime", "instrument"])
        s = pd.Series([0.01] * 20, index=idx)
        result = ops.realized_vol(s, 20)
        val = result.xs("X", level="instrument").iloc[-1]
        # RMS of constant 0.01 series is 0.01; annualized = 0.01 * sqrt(252)
        expected = 0.01 * np.sqrt(252)
        assert abs(val - expected) < 1e-10, f"Expected {expected:.6f}, got {val:.6f}"


class TestEwm:
    def test_return_type_and_index(self, ops, panel_series):
        result = ops.ewm(panel_series, span=10)
        _check_series(result, panel_series)

    def test_no_nan_after_first(self, ops, panel_series):
        """EWM should not produce NaN except where input is NaN."""
        result = ops.ewm(panel_series, span=10)
        assert result.isna().sum() == 0

    def test_instruments_independent(self, ops, panel_series):
        result = ops.ewm(panel_series, span=10)
        a = result.xs("A", level="instrument")
        b = result.xs("B", level="instrument")
        assert not a.equals(b)


class TestHHI:
    def test_return_type_and_index(self, ops, panel_series):
        result = ops.hhi(panel_series.abs(), 5)
        _check_series(result, panel_series)

    def test_nan_for_initial_window(self, ops, panel_series):
        result = ops.hhi(panel_series.abs(), 10)
        for inst in ["A", "B", "C"]:
            inst_vals = result.xs(inst, level="instrument")
            assert inst_vals.iloc[:9].isna().all()

    def test_bounded(self, ops, panel_series):
        """HHI must be in (0, 1]."""
        result = ops.hhi(panel_series.abs(), 5)
        valid = result.dropna()
        assert (valid > 0).all(), "HHI must be positive"
        assert (valid <= 1.0 + 1e-9).all(), "HHI must be <= 1"


class TestDelta:
    def test_return_type_and_index(self, ops, panel_series):
        result = ops.delta(panel_series, 1)
        _check_series(result, panel_series)

    def test_nan_for_initial_period(self, ops, panel_series):
        result = ops.delta(panel_series, 1)
        for inst in ["A", "B", "C"]:
            inst_vals = result.xs(inst, level="instrument")
            assert np.isnan(inst_vals.iloc[0]), "First value should be NaN"
            assert inst_vals.iloc[1:].notna().all()

    def test_diff_correctness(self, ops):
        """delta with period=1 should equal consecutive differences."""
        dates = pd.bdate_range("2024-01-01", periods=5)
        idx = pd.MultiIndex.from_product([dates, ["X"]], names=["datetime", "instrument"])
        s = pd.Series([1.0, 3.0, 6.0, 10.0, 15.0], index=idx)
        result = ops.delta(s, 1)
        vals = result.xs("X", level="instrument")
        np.testing.assert_allclose(vals.iloc[1:].values, [2.0, 3.0, 4.0, 5.0])


class TestTsArgmax:
    def test_return_type_and_index(self, ops, panel_series):
        result = ops.ts_argmax(panel_series, 5)
        _check_series(result, panel_series)

    def test_nan_for_initial_window(self, ops, panel_series):
        result = ops.ts_argmax(panel_series, 10)
        for inst in ["A", "B", "C"]:
            inst_vals = result.xs(inst, level="instrument")
            assert inst_vals.iloc[:9].isna().all()

    def test_range(self, ops, panel_series):
        """Argmax result (position of max within window) must be in [0, window-1]."""
        window = 5
        result = ops.ts_argmax(panel_series, window)
        valid = result.dropna()
        assert (valid >= 0).all()
        assert (valid < window).all()


class TestTsArgmin:
    def test_return_type_and_index(self, ops, panel_series):
        result = ops.ts_argmin(panel_series, 5)
        _check_series(result, panel_series)

    def test_nan_for_initial_window(self, ops, panel_series):
        result = ops.ts_argmin(panel_series, 10)
        for inst in ["A", "B", "C"]:
            inst_vals = result.xs(inst, level="instrument")
            assert inst_vals.iloc[:9].isna().all()

    def test_range(self, ops, panel_series):
        window = 5
        result = ops.ts_argmin(panel_series, window)
        valid = result.dropna()
        assert (valid >= 0).all()
        assert (valid < window).all()


class TestTsCorr:
    def test_return_type_and_index(self, ops, panel_series, panel_returns):
        result = ops.ts_corr(panel_series, panel_returns, 10)
        _check_series(result, panel_series)

    def test_nan_for_initial_window(self, ops, panel_series, panel_returns):
        result = ops.ts_corr(panel_series, panel_returns, 10)
        for inst in ["A", "B", "C"]:
            inst_vals = result.xs(inst, level="instrument")
            assert inst_vals.iloc[:9].isna().all()

    def test_bounded(self, ops, panel_series, panel_returns):
        result = ops.ts_corr(panel_series, panel_returns, 10)
        valid = result.dropna()
        assert (valid.abs() <= 1.0 + 1e-9).all()


class TestTsCov:
    def test_return_type_and_index(self, ops, panel_series, panel_returns):
        result = ops.ts_cov(panel_series, panel_returns, 10)
        _check_series(result, panel_series)

    def test_nan_for_initial_window(self, ops, panel_series, panel_returns):
        result = ops.ts_cov(panel_series, panel_returns, 10)
        for inst in ["A", "B", "C"]:
            inst_vals = result.xs(inst, level="instrument")
            assert inst_vals.iloc[:9].isna().all()


# ---------------------------------------------------------------------------
# Cross-sectional ops
# ---------------------------------------------------------------------------

class TestCsRank:
    def test_return_type_and_index(self, ops, panel_series):
        result = ops.cs_rank(panel_series)
        _check_series(result, panel_series)

    def test_range(self, ops, panel_series):
        """Rank must be in [0, 1]."""
        result = ops.cs_rank(panel_series)
        assert (result >= 0).all()
        assert (result <= 1).all()

    def test_per_date(self, ops, panel_series):
        """With 3 instruments, ranks should span [0, 0.5, 1] per date."""
        result = ops.cs_rank(panel_series)
        for dt in panel_series.index.get_level_values("datetime").unique():
            day_vals = result.xs(dt, level="datetime").sort_values()
            np.testing.assert_allclose(
                day_vals.values, [0.0, 0.5, 1.0],
                err_msg=f"Date {dt}: expected ranks [0, 0.5, 1], got {day_vals.values}"
            )

    def test_no_nan(self, ops, panel_series):
        result = ops.cs_rank(panel_series)
        assert result.isna().sum() == 0


class TestCsZscore:
    def test_return_type_and_index(self, ops, panel_series):
        result = ops.cs_zscore(panel_series)
        _check_series(result, panel_series)

    def test_mean_approximately_zero(self, ops, panel_series):
        """Cross-sectional mean should be ~0 for each date."""
        result = ops.cs_zscore(panel_series)
        for dt in panel_series.index.get_level_values("datetime").unique():
            day_mean = result.xs(dt, level="datetime").mean()
            assert abs(day_mean) < 1e-10, f"Date {dt}: cross-sectional mean = {day_mean}"

    def test_no_nan(self, ops, panel_series):
        result = ops.cs_zscore(panel_series)
        assert result.isna().sum() == 0


# ---------------------------------------------------------------------------
# Element-wise transforms
# ---------------------------------------------------------------------------

class TestSignedPower:
    def test_return_type_and_index(self, ops, panel_series):
        result = ops.signed_power(panel_series, 0.5)
        _check_series(result, panel_series)

    def test_preserves_sign(self, ops):
        dates = pd.bdate_range("2024-01-01", periods=4)
        idx = pd.MultiIndex.from_product([dates, ["X"]], names=["datetime", "instrument"])
        s = pd.Series([4.0, -4.0, 9.0, -9.0], index=idx)
        result = ops.signed_power(s, 0.5)
        vals = result.xs("X", level="instrument").values
        np.testing.assert_allclose(vals, [2.0, -2.0, 3.0, -3.0])

    def test_zero_input(self, ops):
        dates = pd.bdate_range("2024-01-01", periods=1)
        idx = pd.MultiIndex.from_product([dates, ["X"]], names=["datetime", "instrument"])
        s = pd.Series([0.0], index=idx)
        result = ops.signed_power(s, 2.0)
        assert result.xs("X", level="instrument").iloc[0] == 0.0


class TestTanh:
    def test_return_type_and_index(self, ops, panel_series):
        result = ops.tanh(panel_series)
        _check_series(result, panel_series)

    def test_bounded(self, ops, panel_series):
        """tanh must be in [-1, 1] (large inputs saturate to ±1 in float64)."""
        result = ops.tanh(panel_series)
        assert (result >= -1.0).all()
        assert (result <= 1.0).all()

    def test_zero_maps_to_zero(self, ops):
        dates = pd.bdate_range("2024-01-01", periods=1)
        idx = pd.MultiIndex.from_product([dates, ["X"]], names=["datetime", "instrument"])
        s = pd.Series([0.0], index=idx)
        result = ops.tanh(s)
        assert result.xs("X", level="instrument").iloc[0] == pytest.approx(0.0)

    def test_large_positive_approaches_one(self, ops):
        dates = pd.bdate_range("2024-01-01", periods=1)
        idx = pd.MultiIndex.from_product([dates, ["X"]], names=["datetime", "instrument"])
        s = pd.Series([1000.0], index=idx)
        result = ops.tanh(s)
        assert result.xs("X", level="instrument").iloc[0] == pytest.approx(1.0, abs=1e-6)


class TestSafeDiv:
    def test_return_type_and_index(self, ops, panel_series):
        result = ops.safe_div(panel_series, panel_series)
        _check_series(result, panel_series)

    def test_normal_division(self, ops):
        dates = pd.bdate_range("2024-01-01", periods=3)
        idx = pd.MultiIndex.from_product([dates, ["X"]], names=["datetime", "instrument"])
        x = pd.Series([4.0, 9.0, 16.0], index=idx)
        y = pd.Series([2.0, 3.0, 4.0], index=idx)
        result = ops.safe_div(x, y)
        np.testing.assert_allclose(
            result.xs("X", level="instrument").values, [2.0, 3.0, 4.0]
        )

    def test_zero_denominator_returns_zero(self, ops):
        dates = pd.bdate_range("2024-01-01", periods=3)
        idx = pd.MultiIndex.from_product([dates, ["X"]], names=["datetime", "instrument"])
        x = pd.Series([4.0, 9.0, 0.0], index=idx)
        y = pd.Series([2.0, 0.0, 0.0], index=idx)
        result = ops.safe_div(x, y)
        vals = result.xs("X", level="instrument").values
        assert vals[0] == pytest.approx(2.0)
        assert vals[1] == pytest.approx(0.0), "Division by zero should give 0"
        assert vals[2] == pytest.approx(0.0), "0/0 should give 0"

    def test_no_inf_in_result(self, ops, panel_series):
        result = ops.safe_div(panel_series, panel_series * 0)
        assert not np.isinf(result).any(), "safe_div should never produce inf"


class TestLog1pAbs:
    def test_return_type_and_index(self, ops, panel_series):
        result = ops.log1p_abs(panel_series)
        _check_series(result, panel_series)

    def test_preserves_sign(self, ops):
        dates = pd.bdate_range("2024-01-01", periods=4)
        idx = pd.MultiIndex.from_product([dates, ["X"]], names=["datetime", "instrument"])
        s = pd.Series([1.0, -1.0, 2.0, -2.0], index=idx)
        result = ops.log1p_abs(s)
        vals = result.xs("X", level="instrument").values
        assert vals[0] > 0
        assert vals[1] < 0
        assert vals[2] > 0
        assert vals[3] < 0

    def test_zero_maps_to_zero(self, ops):
        dates = pd.bdate_range("2024-01-01", periods=1)
        idx = pd.MultiIndex.from_product([dates, ["X"]], names=["datetime", "instrument"])
        s = pd.Series([0.0], index=idx)
        result = ops.log1p_abs(s)
        assert result.xs("X", level="instrument").iloc[0] == pytest.approx(0.0)

    def test_symmetry(self, ops):
        """log1p_abs(-x) == -log1p_abs(x)."""
        dates = pd.bdate_range("2024-01-01", periods=3)
        idx = pd.MultiIndex.from_product([dates, ["X"]], names=["datetime", "instrument"])
        s = pd.Series([1.0, 5.0, 10.0], index=idx)
        pos = ops.log1p_abs(s)
        neg = ops.log1p_abs(-s)
        np.testing.assert_allclose(pos.values, -neg.values)
