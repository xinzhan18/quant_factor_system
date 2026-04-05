"""Tests for research.feasibility.liquidity."""

import numpy as np
import pandas as pd
import pytest

from research.feasibility.liquidity import compute_liquidity_coverage


def _make_index(n_dates=30, n_instruments=20):
    dates = pd.bdate_range("2023-01-02", periods=n_dates)
    instruments = [f"SH60{i:04d}" for i in range(n_instruments)]
    return pd.MultiIndex.from_product(
        [dates, instruments], names=["datetime", "instrument"]
    )


class TestLiquidityCoverage:
    def test_all_liquid_returns_one(self):
        """When all stocks have equal high amount, coverage should be ~1."""
        idx = _make_index(n_dates=30, n_instruments=20)
        # Uniform high amount
        amount = pd.DataFrame({"amount": 1e8}, index=idx)
        # Uniform weights
        weights = pd.DataFrame({"weight": 1.0 / 20}, index=idx)
        result = compute_liquidity_coverage(weights, amount, window=5)
        assert result >= 0.99

    def test_all_illiquid_returns_zero(self):
        """When the portfolio is entirely in the bottom quantile, coverage ~ 0."""
        idx = _make_index(n_dates=30, n_instruments=20)
        rng = np.random.RandomState(7)
        # Create amount where first 6 instruments (30%) have low amount
        amounts = np.zeros(len(idx))
        for i, (dt, inst) in enumerate(idx):
            inst_num = int(inst[-4:])
            if inst_num < 6:
                amounts[i] = 100  # very low
            else:
                amounts[i] = 1e8  # high
        amount = pd.DataFrame({"amount": amounts}, index=idx)

        # Put ALL weight on illiquid stocks only
        weight_vals = np.zeros(len(idx))
        for i, (dt, inst) in enumerate(idx):
            inst_num = int(inst[-4:])
            if inst_num < 6:
                weight_vals[i] = 1.0 / 6
        weights = pd.DataFrame({"weight": weight_vals}, index=idx)

        result = compute_liquidity_coverage(weights, amount, window=5)
        assert result < 0.05

    def test_result_between_zero_and_one(self):
        idx = _make_index()
        rng = np.random.RandomState(42)
        amount = pd.DataFrame(
            {"amount": rng.exponential(1e7, len(idx))}, index=idx
        )
        weights = pd.DataFrame(
            {"weight": np.abs(rng.randn(len(idx)))}, index=idx
        )
        result = compute_liquidity_coverage(weights, amount)
        assert 0.0 <= result <= 1.0

    def test_empty_returns_zero(self):
        idx = _make_index(n_dates=1, n_instruments=1)
        amount = pd.DataFrame({"amount": [0.0]}, index=idx)
        weights = pd.DataFrame({"weight": [0.0]}, index=idx)
        result = compute_liquidity_coverage(weights, amount)
        assert result == 0.0
