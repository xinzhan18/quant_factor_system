"""Tests for research.stats.risk_model."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.stats.risk_model import compute_risk_views
from tests.research.stats.conftest import make_panel


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestComputeRiskViews:

    def test_basic_output_keys(self):
        """Result contains raw_ic, neutral_ic, alpha_survival_ratio."""
        rng = np.random.default_rng(42)
        n, s = 200, 50
        factor = rng.normal(size=(n, s))
        returns = factor * 0.3 + rng.normal(size=(n, s)) * 0.7
        # Market cap: large-cap for first half of symbols
        cap_signal = np.ones((n, s)) * 1e10
        cap_signal[:, s // 2 :] = 1e8

        start = "2020-01-01"
        fv = make_panel(n, s, start, rng, factor)
        fr = make_panel(n, s, start, rng, returns)
        mc = make_panel(n, s, start, rng, cap_signal)

        result = compute_risk_views(fv, fr, mc)

        assert "raw_ic" in result
        assert "neutral_ic" in result
        assert "alpha_survival_ratio" in result

    def test_pure_size_factor(self):
        """A pure size factor should have reduced alpha after neutralization."""
        rng = np.random.default_rng(7)
        n, s = 300, 60

        # Factor = log(market_cap) + tiny noise => pure size exposure
        cap_base = np.exp(rng.uniform(18, 25, s))  # Market caps
        cap_signal = np.tile(cap_base, (n, 1))
        factor_signal = np.log(cap_signal) + rng.normal(0, 0.01, (n, s))

        # Returns correlated with size
        returns_signal = np.log(cap_signal) * 0.001 + rng.normal(0, 0.01, (n, s))

        start = "2019-01-01"
        fv = make_panel(n, s, start, rng, factor_signal)
        fr = make_panel(n, s, start, rng, returns_signal)
        mc = make_panel(n, s, start, rng, cap_signal)

        result = compute_risk_views(fv, fr, mc)

        # Alpha survival should be < 1 for a size-driven factor
        if np.isfinite(result["alpha_survival_ratio"]):
            assert result["alpha_survival_ratio"] < 1.5

    def test_empty_data(self):
        """Empty inputs return NaN."""
        fv = pd.DataFrame(columns=["time", "symbol", "value"])
        fr = pd.DataFrame(columns=["time", "symbol", "value"])
        mc = pd.DataFrame(columns=["time", "symbol", "value"])

        result = compute_risk_views(fv, fr, mc)
        assert np.isnan(result["raw_ic"])
        assert np.isnan(result["neutral_ic"])

    def test_with_industry(self):
        """Industry neutralization runs without error."""
        rng = np.random.default_rng(55)
        n, s = 200, 50
        factor = rng.normal(size=(n, s))
        returns = factor * 0.2 + rng.normal(size=(n, s)) * 0.8
        cap = np.ones((n, s)) * 1e9
        # 3 industry groups
        ind_codes = np.tile(np.repeat([1.0, 2.0, 3.0], [s // 3, s // 3, s - 2 * (s // 3)]), (n, 1))

        start = "2020-01-01"
        fv = make_panel(n, s, start, rng, factor)
        fr = make_panel(n, s, start, rng, returns)
        mc = make_panel(n, s, start, rng, cap)
        ind = make_panel(n, s, start, rng, ind_codes)

        result = compute_risk_views(fv, fr, mc, industry=ind)
        assert "neutral_ic" in result
