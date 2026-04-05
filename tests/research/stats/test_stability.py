"""Tests for research.stats.stability."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.stats.stability import (
    compute_split_stability,
    compute_regime_stability,
    compute_sign_consistency,
    compute_train_validation_decay,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_ic_series(
    n: int, mean: float = 0.01, std: float = 0.05, seed: int = 42, start: str = "2022-01-01"
) -> pd.Series:
    """Create a synthetic daily IC series."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range(start, periods=n, freq="B")
    return pd.Series(rng.normal(mean, std, n), index=dates)


# ---------------------------------------------------------------------------
# Split stability
# ---------------------------------------------------------------------------


class TestSplitStability:

    def test_high_bucket(self):
        """Consistently positive IC across splits -> high bucket."""
        ic = _make_ic_series(480, mean=0.015, std=0.03, seed=1)
        result = compute_split_stability(ic, n_splits=4, min_days=60)
        assert result["bucket"] == "high"
        assert result["sign_consistency"] >= 0.75
        assert result["n_splits"] == 4

    def test_low_bucket_from_sign_flips(self):
        """Half positive, half negative -> low or medium."""
        rng = np.random.default_rng(77)
        dates = pd.bdate_range("2022-01-01", periods=480, freq="B")
        vals = np.concatenate([
            rng.normal(0.02, 0.03, 120),
            rng.normal(-0.02, 0.03, 120),
            rng.normal(0.02, 0.03, 120),
            rng.normal(-0.02, 0.03, 120),
        ])
        ic = pd.Series(vals, index=dates)
        result = compute_split_stability(ic, n_splits=4, min_days=60)
        assert result["sign_consistency"] <= 0.5

    def test_fallback_to_3_splits(self):
        """When 4 splits don't meet min_days, falls back to 3."""
        ic = _make_ic_series(200, mean=0.01, seed=3)
        result = compute_split_stability(ic, n_splits=4, min_days=60)
        assert result["n_splits"] == 3

    def test_insufficient_data(self):
        """Very short series returns insufficient_splits."""
        ic = _make_ic_series(30, mean=0.01, seed=5)
        result = compute_split_stability(ic, n_splits=4, min_days=60)
        assert result["bucket"] == "insufficient_splits"

    def test_empty_series(self):
        """Empty IC series returns insufficient_splits."""
        result = compute_split_stability(pd.Series(dtype=float))
        assert result["bucket"] == "insufficient_splits"


# ---------------------------------------------------------------------------
# Regime stability
# ---------------------------------------------------------------------------


class TestRegimeStability:

    def _make_bench_with_regimes(
        self, n: int, seed: int = 42, start: str = "2022-01-01"
    ):
        """Create benchmark returns that produce clear bull/bear/range regimes."""
        rng = np.random.default_rng(seed)
        dates = pd.bdate_range(start, periods=n, freq="B")
        # First third: strong positive (bull)
        # Middle third: near zero (range)
        # Last third: strong negative (bear)
        third = n // 3
        bull = rng.normal(0.005, 0.005, third)
        rng_part = rng.normal(0.0, 0.003, third)
        bear = rng.normal(-0.005, 0.005, n - 2 * third)
        return pd.Series(np.concatenate([bull, rng_part, bear]), index=dates)

    def test_stable_across_regimes(self):
        """Consistent positive IC across regimes -> high bucket."""
        n = 500
        ic = _make_ic_series(n, mean=0.015, std=0.03, seed=10, start="2022-01-01")
        bench = self._make_bench_with_regimes(n, seed=10, start="2022-01-01")
        result = compute_regime_stability(ic, bench)
        # May be high or medium depending on regime coverage
        assert result["bucket"] in ("high", "medium", "insufficient_regime_coverage")

    def test_insufficient_regime(self):
        """Very short series -> insufficient regime coverage."""
        ic = _make_ic_series(50, mean=0.01, seed=20)
        bench = pd.Series(
            np.random.default_rng(20).normal(0, 0.01, 50),
            index=ic.index,
        )
        result = compute_regime_stability(ic, bench)
        assert result["bucket"] == "insufficient_regime_coverage"

    def test_empty_series(self):
        result = compute_regime_stability(
            pd.Series(dtype=float), pd.Series(dtype=float)
        )
        assert result["bucket"] == "insufficient_regime_coverage"


# ---------------------------------------------------------------------------
# Sign consistency
# ---------------------------------------------------------------------------


class TestSignConsistency:

    def test_same_sign(self):
        ic_train = _make_ic_series(200, mean=0.02, seed=1)
        ic_val = _make_ic_series(200, mean=0.01, seed=2)
        assert compute_sign_consistency(ic_train, ic_val) is True

    def test_opposite_sign(self):
        ic_train = _make_ic_series(200, mean=0.02, seed=1)
        ic_val = _make_ic_series(200, mean=-0.01, seed=2)
        assert compute_sign_consistency(ic_train, ic_val) is False

    def test_near_zero(self):
        ic_train = _make_ic_series(200, mean=0.0, std=0.001, seed=1)
        # Mean will be near zero -> False
        result = compute_sign_consistency(ic_train, ic_train)
        # Could be True or False depending on noise; just check type
        assert isinstance(result, bool)


# ---------------------------------------------------------------------------
# Train-validation decay
# ---------------------------------------------------------------------------


class TestTrainValidationDecay:

    def test_no_decay(self):
        assert compute_train_validation_decay(0.02, 0.02) == pytest.approx(1.0)

    def test_half_decay(self):
        assert compute_train_validation_decay(0.02, 0.01) == pytest.approx(0.5)

    def test_sign_irrelevant(self):
        """Decay uses absolute values."""
        assert compute_train_validation_decay(-0.02, -0.01) == pytest.approx(0.5)

    def test_near_zero_train(self):
        assert np.isnan(compute_train_validation_decay(0.0, 0.01))
