"""Tests for Layer 1: pairwise duplication detection."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.redundancy.pairwise import (
    compute_pairwise_redundancy,
    batch_dedup,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_multi_index(n_dates: int = 20, n_stocks: int = 50, seed: int = 0):
    """Create a (datetime, instrument) MultiIndex with random factor values."""
    dates = pd.bdate_range("2023-01-01", periods=n_dates)
    instruments = [f"SH60{i:04d}" for i in range(n_stocks)]
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    return idx, dates, instruments


def _make_signal(idx, values: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({"value": values}, index=idx)


def _synth_correlated_pair(corr: float, n_dates=20, n_stocks=50, seed=42):
    """Generate two signals with approx *corr* cross-sectional rank correlation."""
    rng = np.random.RandomState(seed)
    idx, _dates, _instruments = _make_multi_index(n_dates, n_stocks)
    n = len(idx)
    x = rng.randn(n)
    noise = rng.randn(n)
    # y = corr * x + sqrt(1-corr^2) * noise  =>  rank corr ~ corr
    y = corr * x + np.sqrt(max(1.0 - corr ** 2, 0.0)) * noise
    return _make_signal(idx, x), _make_signal(idx, y)


# ---------------------------------------------------------------------------
# Tests: compute_pairwise_redundancy
# ---------------------------------------------------------------------------

class TestPairwiseRedundancy:
    def test_empty_library(self):
        idx, _, _ = _make_multi_index(5, 10)
        cand = _make_signal(idx, np.random.randn(len(idx)))
        result = compute_pairwise_redundancy(cand, {})
        assert result["max_lib_corr"] == 0.0
        assert result["nearest_factor_id"] is None
        assert result["is_near_duplicate"] is False

    def test_identical_signal_detected(self):
        idx, _, _ = _make_multi_index(20, 50)
        values = np.random.RandomState(7).randn(len(idx))
        cand = _make_signal(idx, values)
        lib = {"F001": _make_signal(idx, values.copy())}
        result = compute_pairwise_redundancy(cand, lib)
        assert result["max_lib_corr"] > 0.99
        assert result["nearest_factor_id"] == "F001"
        assert result["is_near_duplicate"] is True

    def test_uncorrelated_signals(self):
        rng = np.random.RandomState(99)
        idx, _, _ = _make_multi_index(30, 100)
        cand = _make_signal(idx, rng.randn(len(idx)))
        lib = {"F001": _make_signal(idx, rng.randn(len(idx)))}
        result = compute_pairwise_redundancy(cand, lib)
        # Random signals: |corr| should be small.
        assert result["max_lib_corr"] < 0.15
        assert result["is_near_duplicate"] is False

    def test_moderate_correlation(self):
        cand, lib_sig = _synth_correlated_pair(0.6, n_dates=40, n_stocks=100)
        result = compute_pairwise_redundancy(cand, {"F001": lib_sig})
        # Should be roughly 0.6, within tolerance.
        assert 0.4 < result["max_lib_corr"] < 0.8
        assert result["is_near_duplicate"] is False

    def test_exceeds_threshold_flag(self):
        cand, lib_sig = _synth_correlated_pair(0.8, n_dates=30, n_stocks=80)
        result = compute_pairwise_redundancy(cand, {"F001": lib_sig}, threshold=0.7)
        assert result["exceeds_threshold"] is True

    def test_multiple_library_factors(self):
        rng = np.random.RandomState(10)
        idx, _, _ = _make_multi_index(20, 50)
        base = rng.randn(len(idx))
        cand = _make_signal(idx, base)
        lib = {
            "F001": _make_signal(idx, rng.randn(len(idx))),  # random
            "F002": _make_signal(idx, base + 0.1 * rng.randn(len(idx))),  # near duplicate
        }
        result = compute_pairwise_redundancy(cand, lib)
        assert result["nearest_factor_id"] == "F002"
        assert result["max_lib_corr"] > 0.8

    def test_all_correlations_returned(self):
        rng = np.random.RandomState(11)
        idx, _, _ = _make_multi_index(10, 30)
        cand = _make_signal(idx, rng.randn(len(idx)))
        lib = {
            "F001": _make_signal(idx, rng.randn(len(idx))),
            "F002": _make_signal(idx, rng.randn(len(idx))),
        }
        result = compute_pairwise_redundancy(cand, lib)
        assert set(result["all_correlations"].keys()) == {"F001", "F002"}


# ---------------------------------------------------------------------------
# Tests: batch_dedup
# ---------------------------------------------------------------------------

class TestBatchDedup:
    def test_no_duplicates(self):
        rng = np.random.RandomState(20)
        idx, _, _ = _make_multi_index(20, 50)
        signals = {
            f"C{i}": _make_signal(idx, rng.randn(len(idx)))
            for i in range(3)
        }
        pairs = batch_dedup(signals, threshold=0.9)
        assert pairs == []

    def test_duplicate_pair_found(self):
        idx, _, _ = _make_multi_index(20, 50)
        rng = np.random.RandomState(21)
        base = rng.randn(len(idx))
        signals = {
            "C0": _make_signal(idx, base),
            "C1": _make_signal(idx, base + 0.01 * rng.randn(len(idx))),
            "C2": _make_signal(idx, rng.randn(len(idx))),  # independent
        }
        pairs = batch_dedup(signals, threshold=0.9)
        assert len(pairs) == 1
        assert pairs[0][0] == "C0"
        assert pairs[0][1] == "C1"
        assert pairs[0][2] > 0.9

    def test_empty_batch(self):
        pairs = batch_dedup({})
        assert pairs == []
