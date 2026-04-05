"""Tests for Layer 3: local subspace redundancy."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.redundancy.subspace import (
    compute_subspace_redundancy,
    _ridge_regression_crosssection,
    _determine_confidence,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_multi_index(n_dates: int = 20, n_stocks: int = 50):
    dates = pd.bdate_range("2023-01-01", periods=n_dates)
    instruments = [f"SH60{i:04d}" for i in range(n_stocks)]
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    return idx


def _make_signal(idx, values: np.ndarray) -> pd.DataFrame:
    return pd.DataFrame({"value": values}, index=idx)


# ---------------------------------------------------------------------------
# Tests: _ridge_regression_crosssection
# ---------------------------------------------------------------------------

class TestRidgeRegression:
    def test_perfect_fit(self):
        """y = X @ [1, 2] should give R^2 = 1 (modulo ridge penalty)."""
        rng = np.random.RandomState(0)
        X = rng.randn(100, 2)
        beta_true = np.array([1.0, 2.0])
        y = X @ beta_true
        beta, residual, r2 = _ridge_regression_crosssection(y, X, alpha=0.0001)
        assert r2 > 0.999
        np.testing.assert_allclose(beta, beta_true, atol=0.01)

    def test_pure_noise(self):
        """Random y should give low R^2."""
        rng = np.random.RandomState(1)
        X = rng.randn(100, 2)
        y = rng.randn(100)
        _beta, _residual, r2 = _ridge_regression_crosssection(y, X, alpha=1.0)
        assert r2 < 0.15

    def test_residual_sum_property(self):
        """y_hat + residual = y."""
        rng = np.random.RandomState(2)
        X = rng.randn(80, 3)
        y = rng.randn(80)
        beta, residual, _r2 = _ridge_regression_crosssection(y, X, alpha=1.0)
        y_hat = X @ beta
        np.testing.assert_allclose(y_hat + residual, y, atol=1e-10)


# ---------------------------------------------------------------------------
# Tests: _determine_confidence
# ---------------------------------------------------------------------------

class TestDetermineConfidence:
    def test_insufficient_family_size(self):
        assert _determine_confidence(3, 1, 300) == "insufficient_family_size"

    def test_insufficient_basis(self):
        assert _determine_confidence(1, 5, 300) == "insufficient_basis"

    def test_low(self):
        assert _determine_confidence(2, 5, 120) == "low"
        assert _determine_confidence(2, 5, 200) == "low"

    def test_medium(self):
        assert _determine_confidence(3, 5, 250) == "medium"
        assert _determine_confidence(3, 10, 200) == "medium"

    def test_high(self):
        assert _determine_confidence(3, 6, 250) == "high"
        assert _determine_confidence(3, 10, 500) == "high"

    def test_basis_2_short_validation(self):
        # basis=2, validation < 120 -> insufficient_basis
        assert _determine_confidence(2, 5, 50) == "insufficient_basis"


# ---------------------------------------------------------------------------
# Tests: compute_subspace_redundancy
# ---------------------------------------------------------------------------

class TestSubspaceRedundancy:
    def test_candidate_is_linear_combo(self):
        """When candidate = sum of basis, R^2 should be near 1."""
        idx = _make_multi_index(30, 100)
        rng = np.random.RandomState(10)
        n = len(idx)
        b1 = rng.randn(n)
        b2 = rng.randn(n)
        cand_values = b1 + 2.0 * b2  # perfect linear combo

        cand = _make_signal(idx, cand_values)
        basis = {
            "F001": _make_signal(idx, b1),
            "F002": _make_signal(idx, b2),
        }
        fwd = _make_signal(idx, rng.randn(n))

        result = compute_subspace_redundancy(cand, basis, fwd, family_size=5)
        assert result["subspace_redundancy_score"] is not None
        assert result["subspace_redundancy_score"] > 0.95
        assert result["basis_factor_count"] == 2

    def test_independent_signals(self):
        """Independent candidate should have low R^2."""
        idx = _make_multi_index(30, 100)
        rng = np.random.RandomState(11)
        n = len(idx)

        cand = _make_signal(idx, rng.randn(n))
        basis = {
            "F001": _make_signal(idx, rng.randn(n)),
            "F002": _make_signal(idx, rng.randn(n)),
        }
        fwd = _make_signal(idx, rng.randn(n))

        result = compute_subspace_redundancy(cand, basis, fwd, family_size=5)
        assert result["subspace_redundancy_score"] is not None
        assert result["subspace_redundancy_score"] < 0.15

    def test_residual_ic_with_correlated_return(self):
        """When residual correlates with forward returns, IC should be nonzero."""
        idx = _make_multi_index(40, 80)
        rng = np.random.RandomState(12)
        n = len(idx)
        b1 = rng.randn(n)
        signal_part = rng.randn(n)
        cand_values = b1 + signal_part  # basis explains b1, residual ~ signal_part

        cand = _make_signal(idx, cand_values)
        basis = {"F001": _make_signal(idx, b1), "F002": _make_signal(idx, rng.randn(n))}
        # Forward return correlated with signal_part.
        fwd = _make_signal(idx, signal_part + 0.5 * rng.randn(n))

        result = compute_subspace_redundancy(cand, basis, fwd, family_size=5)
        assert result["residual_incremental_ic"] is not None
        assert result["residual_incremental_ic"] > 0.1

    def test_empty_basis(self):
        idx = _make_multi_index(10, 20)
        rng = np.random.RandomState(13)
        cand = _make_signal(idx, rng.randn(len(idx)))
        fwd = _make_signal(idx, rng.randn(len(idx)))
        # Only 1 basis: below the minimum of 2 for meaningful regression,
        # but the function still attempts computation.
        result = compute_subspace_redundancy(
            cand, {"F001": _make_signal(idx, rng.randn(len(idx)))}, fwd, family_size=0,
        )
        # Should still return results (1 basis works mechanically).
        assert result["basis_factor_count"] == 1

    def test_confidence_propagated(self):
        idx = _make_multi_index(30, 50)
        rng = np.random.RandomState(14)
        n = len(idx)
        cand = _make_signal(idx, rng.randn(n))
        basis = {
            "F001": _make_signal(idx, rng.randn(n)),
            "F002": _make_signal(idx, rng.randn(n)),
            "F003": _make_signal(idx, rng.randn(n)),
        }
        fwd = _make_signal(idx, rng.randn(n))
        result = compute_subspace_redundancy(cand, basis, fwd, family_size=10)
        # basis=3, family=10, validation_days=30 -> medium (days < 250)
        assert result["subspace_confidence"] == "medium"

    def test_validation_days_counted(self):
        idx = _make_multi_index(15, 30)
        rng = np.random.RandomState(15)
        n = len(idx)
        cand = _make_signal(idx, rng.randn(n))
        basis = {
            "F001": _make_signal(idx, rng.randn(n)),
            "F002": _make_signal(idx, rng.randn(n)),
        }
        fwd = _make_signal(idx, rng.randn(n))
        result = compute_subspace_redundancy(cand, basis, fwd, family_size=5)
        assert result["validation_days"] == 15
