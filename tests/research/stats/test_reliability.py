"""Tests for research.stats.reliability."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.stats.reliability import (
    compute_expanding_window_ic,
    compute_bootstrap_stability,
    compute_purged_walk_forward,
)
from tests.research.stats.conftest import make_panel


# ---------------------------------------------------------------------------
# Expanding window IC
# ---------------------------------------------------------------------------


class TestExpandingWindowIC:

    def test_positive_signal_passes(self):
        """A factor with stable positive IC should pass expanding window."""
        rng = np.random.default_rng(42)
        n, s = 600, 80
        factor = rng.normal(size=(n, s))
        returns = factor * 0.3 + rng.normal(size=(n, s)) * 0.7

        start = "2017-01-01"
        fv = make_panel(n, s, start, rng, factor)
        fr = make_panel(n, s, start, rng, returns)

        result = compute_expanding_window_ic(fv, fr, start=start, step_months=6)

        assert len(result["path"]) >= 2
        assert result["pass"] is True
        assert result["sign_consistency"] >= 0.6

    def test_empty_data(self):
        fv = pd.DataFrame(columns=["time", "symbol", "value"])
        fr = pd.DataFrame(columns=["time", "symbol", "value"])
        result = compute_expanding_window_ic(fv, fr, start="2020-01-01")
        assert result["pass"] is False

    def test_short_data(self):
        """Data shorter than one step yields no pass."""
        rng = np.random.default_rng(10)
        fv = make_panel(30, 50, "2022-01-01", rng)
        fr = make_panel(30, 50, "2022-01-01", rng)
        result = compute_expanding_window_ic(fv, fr, start="2022-01-01", step_months=6)
        assert result["pass"] is False


# ---------------------------------------------------------------------------
# Bootstrap stability
# ---------------------------------------------------------------------------


class TestBootstrapStability:

    def test_good_status(self):
        """Strong positive IC series should yield good status."""
        rng = np.random.default_rng(42)
        ic = pd.Series(rng.normal(0.015, 0.03, 500))
        result = compute_bootstrap_stability(ic, B=200, seed=42)
        assert result["status"] == "good"
        assert result["sign_consistency"] > 0.7

    def test_low_power(self):
        """Short series should return low_power."""
        ic = pd.Series(np.random.default_rng(1).normal(0.01, 0.05, 50))
        result = compute_bootstrap_stability(ic)
        assert result["status"] == "low_power"

    def test_weak_signal_lower_score(self):
        """Near-zero IC should produce a lower score than a strong signal."""
        rng = np.random.default_rng(99)
        weak_ic = pd.Series(rng.normal(0.0, 0.05, 300))
        strong_ic = pd.Series(np.random.default_rng(42).normal(0.015, 0.03, 300))

        weak_result = compute_bootstrap_stability(weak_ic, B=200, seed=99)
        strong_result = compute_bootstrap_stability(strong_ic, B=200, seed=42)

        assert weak_result["score"] <= strong_result["score"]

    def test_reproducibility(self):
        """Same seed should give same result."""
        ic = pd.Series(np.random.default_rng(7).normal(0.01, 0.04, 200))
        r1 = compute_bootstrap_stability(ic, seed=123)
        r2 = compute_bootstrap_stability(ic, seed=123)
        assert r1["score"] == r2["score"]


# ---------------------------------------------------------------------------
# Purged walk-forward
# ---------------------------------------------------------------------------


class TestPurgedWalkForward:

    def test_positive_signal(self):
        """Factor with consistent signal should pass walk-forward."""
        rng = np.random.default_rng(42)
        n, s = 800, 80
        factor = rng.normal(size=(n, s))
        returns = factor * 0.3 + rng.normal(size=(n, s)) * 0.7

        fv = make_panel(n, s, "2016-01-01", rng, factor)
        fr = make_panel(n, s, "2016-01-01", rng, returns)

        result = compute_purged_walk_forward(fv, fr, purge_days=5, n_splits=5)
        assert result["status"] == "sufficient"
        assert len(result["fold_results"]) >= 2

    def test_insufficient_data(self):
        """Very short data -> low_power."""
        rng = np.random.default_rng(5)
        fv = make_panel(50, 40, "2022-01-01", rng)
        fr = make_panel(50, 40, "2022-01-01", rng)
        result = compute_purged_walk_forward(fv, fr)
        assert result["status"] == "low_power"
        assert result["pass"] is False
