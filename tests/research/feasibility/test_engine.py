"""Tests for research.feasibility.engine (FeasibilityEngine)."""

import numpy as np
import pandas as pd
import pytest

from research.feasibility.engine import FeasibilityEngine


def _make_data(n_dates=60, n_instruments=50, seed=42):
    """Build synthetic signal, market_cap, amount, tradable_mask."""
    dates = pd.bdate_range("2023-01-02", periods=n_dates)
    instruments = [f"SH60{i:04d}" for i in range(n_instruments)]
    idx = pd.MultiIndex.from_product(
        [dates, instruments], names=["datetime", "instrument"]
    )
    rng = np.random.RandomState(seed)

    signal = pd.DataFrame({"signal": rng.randn(len(idx))}, index=idx)
    market_cap = pd.DataFrame(
        {"market_cap": rng.exponential(1e10, len(idx))}, index=idx
    )
    amount = pd.DataFrame(
        {"amount": rng.exponential(1e7, len(idx))}, index=idx
    )
    tradable_mask = pd.DataFrame({"tradable": True}, index=idx)
    return signal, market_cap, amount, tradable_mask


class TestFeasibilityEngine:
    def test_analyze_returns_all_keys(self):
        signal, mcap, amt, mask = _make_data()
        engine = FeasibilityEngine()
        result = engine.analyze(signal, mcap, amt, mask)

        expected_keys = {
            "turnover",
            "coverage",
            "half_life",
            "holding_period_proxy",
            "liquidity_coverage_ratio",
            "tail_trade_concentration",
            "small_cap_concentration",
            "rebalance_stress_proxy",
            "rebalance_stress_bucket",
        }
        assert expected_keys == set(result.keys())

    def test_all_values_are_scalar(self):
        signal, mcap, amt, mask = _make_data()
        engine = FeasibilityEngine()
        result = engine.analyze(signal, mcap, amt, mask)
        for k, v in result.items():
            assert isinstance(v, (int, float, str)), f"{k} is {type(v)}"

    def test_coverage_is_one_when_all_valid(self):
        signal, mcap, amt, mask = _make_data(n_dates=10, n_instruments=10)
        engine = FeasibilityEngine()
        result = engine.analyze(signal, mcap, amt, mask)
        np.testing.assert_allclose(result["coverage"], 1.0, atol=1e-10)

    def test_holding_period_is_valid_bucket(self):
        signal, mcap, amt, mask = _make_data()
        engine = FeasibilityEngine()
        result = engine.analyze(signal, mcap, amt, mask)
        assert result["holding_period_proxy"] in {"short", "medium", "long"}

    def test_stress_bucket_is_valid(self):
        signal, mcap, amt, mask = _make_data()
        engine = FeasibilityEngine()
        result = engine.analyze(signal, mcap, amt, mask)
        assert result["rebalance_stress_bucket"] in {"low", "medium", "high"}

    def test_metrics_in_expected_range(self):
        signal, mcap, amt, mask = _make_data()
        engine = FeasibilityEngine()
        result = engine.analyze(signal, mcap, amt, mask)
        assert 0.0 <= result["liquidity_coverage_ratio"] <= 1.0
        assert 0.0 <= result["tail_trade_concentration"] <= 1.0
        assert 0.0 <= result["small_cap_concentration"] <= 1.0
        assert result["turnover"] >= 0.0
        assert result["half_life"] >= 1.0
        assert result["rebalance_stress_proxy"] >= 0.0

    def test_custom_parameters(self):
        signal, mcap, amt, mask = _make_data(n_dates=30, n_instruments=20)
        engine = FeasibilityEngine(
            long_pct=0.10,
            short_pct=0.10,
            tail_top_k=5,
            small_cap_pct=0.20,
        )
        result = engine.analyze(signal, mcap, amt, mask)
        assert set(result.keys()) == {
            "turnover",
            "coverage",
            "half_life",
            "holding_period_proxy",
            "liquidity_coverage_ratio",
            "tail_trade_concentration",
            "small_cap_concentration",
            "rebalance_stress_proxy",
            "rebalance_stress_bucket",
        }

    def test_partial_signal_coverage(self):
        """When some tradable stocks have NaN signal, coverage should drop."""
        signal, mcap, amt, mask = _make_data(n_dates=10, n_instruments=20)
        # Set signal to NaN for half the instruments
        sig_vals = signal["signal"].copy()
        for i, (dt, inst) in enumerate(signal.index):
            if int(inst[-4:]) >= 10:
                sig_vals.iloc[i] = np.nan
        signal = pd.DataFrame({"signal": sig_vals}, index=signal.index)

        engine = FeasibilityEngine()
        result = engine.analyze(signal, mcap, amt, mask)
        # All 20 stocks tradable but only 10 have valid signal => coverage ~ 0.5
        assert result["coverage"] < 0.55
