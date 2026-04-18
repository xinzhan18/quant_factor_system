"""Tests for core.metrics shared primitives."""
import math

import numpy as np
import pandas as pd
import pytest

from core.metrics import (
    annualize_return,
    annualize_volatility,
    sharpe_ratio,
    max_drawdown,
    calmar_ratio,
)
from core.constants import TRADING_DAYS_PER_YEAR


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
