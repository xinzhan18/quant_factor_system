"""Tests for core.metrics shared primitives."""
import math

import numpy as np
import pandas as pd
import pytest

from core.metrics import (
    ic_summary_from_series,
    annualize_return,
    annualize_volatility,
    sharpe_ratio,
    max_drawdown,
    calmar_ratio,
    win_rate,
)
from core.constants import TRADING_DAYS_PER_YEAR


# ── ic_summary_from_series ──


class TestICSummary:
    def test_normal(self):
        ics = pd.Series([0.05, -0.02, 0.03, 0.01, -0.01])
        result = ic_summary_from_series(ics)
        assert result["ic_mean"] == pytest.approx(0.012, abs=1e-6)
        assert result["ic_std"] > 0
        assert result["ic_ir"] == pytest.approx(result["ic_mean"] / result["ic_std"])
        assert result["ic_win_rate"] == pytest.approx(3 / 5)

    def test_empty(self):
        result = ic_summary_from_series(pd.Series(dtype=float))
        assert math.isnan(result["ic_mean"])
        assert math.isnan(result["ic_std"])
        assert math.isnan(result["ic_ir"])
        assert math.isnan(result["ic_win_rate"])

    def test_all_nan(self):
        result = ic_summary_from_series(pd.Series([np.nan, np.nan]))
        assert math.isnan(result["ic_mean"])

    def test_single_value(self):
        result = ic_summary_from_series(pd.Series([0.05]))
        assert result["ic_mean"] == pytest.approx(0.05)
        assert math.isnan(result["ic_std"])  # ddof=1 with n=1

    def test_zero_std(self):
        result = ic_summary_from_series(pd.Series([0.0, 0.0, 0.0]))
        assert result["ic_mean"] == 0.0
        assert result["ic_std"] == 0.0
        assert math.isnan(result["ic_ir"])
        assert result["ic_win_rate"] == 0.0


# ── annualize_return ──


class TestAnnualizeReturn:
    def test_normal(self):
        daily = pd.Series([0.001] * 100)
        assert annualize_return(daily) == pytest.approx(0.001 * TRADING_DAYS_PER_YEAR)

    def test_empty(self):
        assert math.isnan(annualize_return(pd.Series(dtype=float)))


# ── annualize_volatility ──


class TestAnnualizeVolatility:
    def test_normal(self):
        daily = pd.Series([0.01, -0.01, 0.01, -0.01])
        expected = daily.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        assert annualize_volatility(daily) == pytest.approx(expected)

    def test_empty(self):
        assert math.isnan(annualize_volatility(pd.Series(dtype=float)))

    def test_zero_volatility(self):
        daily = pd.Series([0.01, 0.01, 0.01])
        assert annualize_volatility(daily) == 0.0


# ── sharpe_ratio ──


class TestSharpeRatio:
    def test_normal(self):
        daily = pd.Series([0.01, -0.005, 0.008, -0.002, 0.003])
        expected = annualize_return(daily) / annualize_volatility(daily)
        assert sharpe_ratio(daily) == pytest.approx(expected)

    def test_empty(self):
        assert math.isnan(sharpe_ratio(pd.Series(dtype=float)))

    def test_zero_vol(self):
        daily = pd.Series([0.01, 0.01, 0.01])
        assert math.isnan(sharpe_ratio(daily))


# ── max_drawdown ──


class TestMaxDrawdown:
    def test_normal(self):
        cum = pd.Series([1.0, 1.1, 1.05, 0.9, 1.0])
        dd = max_drawdown(cum)
        # Peak at 1.1, trough at 0.9 → dd = 0.9 - 1.1 = -0.2
        assert dd == pytest.approx(-0.2)

    def test_monotonic_up(self):
        cum = pd.Series([1.0, 1.1, 1.2, 1.3])
        assert max_drawdown(cum) == 0.0

    def test_empty(self):
        assert math.isnan(max_drawdown(pd.Series(dtype=float)))


# ── calmar_ratio ──


class TestCalmarRatio:
    def test_normal(self):
        assert calmar_ratio(0.15, -0.05) == pytest.approx(3.0)

    def test_zero_dd(self):
        assert math.isnan(calmar_ratio(0.1, 0.0))

    def test_nan_inputs(self):
        assert math.isnan(calmar_ratio(np.nan, -0.1))
        assert math.isnan(calmar_ratio(0.1, np.nan))


# ── win_rate ──


class TestWinRate:
    def test_normal(self):
        s = pd.Series([0.01, -0.02, 0.03, 0.0, -0.01])
        assert win_rate(s) == pytest.approx(2 / 5)

    def test_empty(self):
        assert math.isnan(win_rate(pd.Series(dtype=float)))

    def test_all_nan(self):
        assert math.isnan(win_rate(pd.Series([np.nan, np.nan])))

    def test_all_positive(self):
        assert win_rate(pd.Series([0.01, 0.02, 0.03])) == pytest.approx(1.0)


# ── sortino_ratio ──

from core.metrics import sortino_ratio, max_drawdown_duration


class TestSortinoRatio:
    def test_all_positive_returns(self):
        daily = pd.Series([0.01, 0.02, 0.01, 0.005, 0.015])
        result = sortino_ratio(daily)
        assert result > 0

    def test_with_negative_returns(self):
        daily = pd.Series([0.01, -0.02, 0.03, -0.01, 0.02])
        result = sortino_ratio(daily)
        assert isinstance(result, float)

    def test_no_negative_returns(self):
        daily = pd.Series([0.01, 0.02, 0.03])
        result = sortino_ratio(daily)
        assert result == float("inf") or result > 100


# ── max_drawdown_duration ──


class TestMaxDrawdownDuration:
    def test_basic_drawdown(self):
        cumulative = pd.Series([1.0, 1.1, 1.05, 0.9, 0.95, 1.0, 1.1])
        duration = max_drawdown_duration(cumulative)
        assert duration > 0
        assert isinstance(duration, int)

    def test_no_drawdown(self):
        cumulative = pd.Series([1.0, 1.1, 1.2, 1.3])
        duration = max_drawdown_duration(cumulative)
        assert duration == 0

    def test_unrecovered_drawdown(self):
        cumulative = pd.Series([1.0, 1.1, 0.9, 0.85, 0.9])
        duration = max_drawdown_duration(cumulative)
        assert duration >= 3
