"""Tests for research.feasibility.concentration."""

import numpy as np
import pandas as pd
import pytest

from research.feasibility.concentration import (
    compute_small_cap_concentration,
    compute_tail_concentration,
)


def _make_index(n_dates=5, n_instruments=20):
    dates = pd.bdate_range("2023-01-02", periods=n_dates)
    instruments = [f"SH60{i:04d}" for i in range(n_instruments)]
    return pd.MultiIndex.from_product(
        [dates, instruments], names=["datetime", "instrument"]
    )


class TestTailConcentration:
    def test_equal_weight_expected(self):
        """With equal weights, top-10 out of 20 = 0.5."""
        idx = _make_index(n_dates=5, n_instruments=20)
        weights = pd.DataFrame({"weight": 1.0 / 20}, index=idx)
        result = compute_tail_concentration(weights, top_k=10)
        np.testing.assert_allclose(result, 0.5, atol=1e-10)

    def test_concentrated_portfolio(self):
        """If all weight on one stock, tail concentration = 1."""
        idx = _make_index(n_dates=3, n_instruments=10)
        w_vals = np.zeros(len(idx))
        for i, (dt, inst) in enumerate(idx):
            if inst == "SH600000":
                w_vals[i] = 1.0
        weights = pd.DataFrame({"weight": w_vals}, index=idx)
        result = compute_tail_concentration(weights, top_k=10)
        np.testing.assert_allclose(result, 1.0, atol=1e-10)

    def test_result_range(self):
        idx = _make_index()
        rng = np.random.RandomState(42)
        weights = pd.DataFrame(
            {"weight": np.abs(rng.randn(len(idx)))}, index=idx
        )
        result = compute_tail_concentration(weights)
        assert 0.0 <= result <= 1.0


class TestSmallCapConcentration:
    def test_all_in_large_cap(self):
        """Weights entirely in large-cap stocks => small_cap_conc ~ 0."""
        idx = _make_index(n_dates=5, n_instruments=20)
        # Market cap: first 6 small, rest large
        cap_vals = np.zeros(len(idx))
        w_vals = np.zeros(len(idx))
        for i, (dt, inst) in enumerate(idx):
            inst_num = int(inst[-4:])
            if inst_num < 6:
                cap_vals[i] = 1e8   # small
            else:
                cap_vals[i] = 1e11  # large
                w_vals[i] = 1.0 / 14  # weight only on large-cap

        market_cap = pd.DataFrame({"cap": cap_vals}, index=idx)
        weights = pd.DataFrame({"weight": w_vals}, index=idx)
        result = compute_small_cap_concentration(weights, market_cap)
        assert result < 0.01

    def test_all_in_small_cap(self):
        """Weights entirely in small-cap stocks => small_cap_conc ~ 1."""
        idx = _make_index(n_dates=5, n_instruments=20)
        cap_vals = np.zeros(len(idx))
        w_vals = np.zeros(len(idx))
        for i, (dt, inst) in enumerate(idx):
            inst_num = int(inst[-4:])
            if inst_num < 6:
                cap_vals[i] = 1e8   # small
                w_vals[i] = 1.0 / 6  # weight only on small-cap
            else:
                cap_vals[i] = 1e11  # large

        market_cap = pd.DataFrame({"cap": cap_vals}, index=idx)
        weights = pd.DataFrame({"weight": w_vals}, index=idx)
        result = compute_small_cap_concentration(weights, market_cap)
        assert result > 0.95

    def test_result_range(self):
        idx = _make_index()
        rng = np.random.RandomState(42)
        market_cap = pd.DataFrame(
            {"cap": rng.exponential(1e10, len(idx))}, index=idx
        )
        weights = pd.DataFrame(
            {"weight": np.abs(rng.randn(len(idx)))}, index=idx
        )
        result = compute_small_cap_concentration(weights, market_cap)
        assert 0.0 <= result <= 1.0
