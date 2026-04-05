"""Tests for Layer 2: family-level redundancy detection."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.redundancy.family import compute_family_overlap


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
# Tests
# ---------------------------------------------------------------------------

class TestFamilyOverlap:
    def test_empty_family(self):
        idx = _make_multi_index(10, 20)
        cand = _make_signal(idx, np.random.randn(len(idx)))
        result = compute_family_overlap(
            cand, {}, {"structure_template": "gated"}, {"structure_template": "gated"},
        )
        assert result["family_overlap_score"] == 0.0
        assert result["family_overlap_bucket"] == "low"
        assert result["family_size"] == 0
        assert result["family_history_status"] == "insufficient"

    def test_identical_family_member(self):
        idx = _make_multi_index(20, 50)
        rng = np.random.RandomState(1)
        values = rng.randn(len(idx))
        cand = _make_signal(idx, values)
        family = {"F001": _make_signal(idx, values.copy())}
        result = compute_family_overlap(
            cand,
            family,
            {"structure_template": "gated", "conditioning_type": "volume", "horizon_bucket": "short"},
            {"structure_template": "gated", "conditioning_type": "volume", "horizon_bucket": "short"},
        )
        # corr_p90 ~ 1.0, structure_overlap = 1.0, residual ~ 0.0
        # score = 0.5*1.0 + 0.3*1.0 + 0.2*(1-0) = 1.0
        assert result["family_overlap_score"] > 0.9
        assert result["family_overlap_bucket"] == "high"
        assert result["same_family_corr_p90"] > 0.95
        assert result["structure_overlap_score"] == 1.0

    def test_uncorrelated_family(self):
        idx = _make_multi_index(30, 80)
        rng = np.random.RandomState(2)
        cand = _make_signal(idx, rng.randn(len(idx)))
        family = {
            "F001": _make_signal(idx, rng.randn(len(idx))),
            "F002": _make_signal(idx, rng.randn(len(idx))),
        }
        result = compute_family_overlap(
            cand,
            family,
            {"structure_template": "linear", "conditioning_type": "price", "horizon_bucket": "long"},
            {"structure_template": "gated", "conditioning_type": "volume", "horizon_bucket": "short"},
        )
        # corr_p90 small, structure_overlap = 0, residual ~ 1
        # score should be low
        assert result["family_overlap_score"] < 0.3
        assert result["family_overlap_bucket"] == "low"
        assert result["structure_overlap_score"] == 0.0

    def test_partial_structure_match(self):
        idx = _make_multi_index(20, 50)
        rng = np.random.RandomState(3)
        cand = _make_signal(idx, rng.randn(len(idx)))
        family = {"F001": _make_signal(idx, rng.randn(len(idx)))}
        result = compute_family_overlap(
            cand,
            family,
            {"structure_template": "gated", "conditioning_type": "volume", "horizon_bucket": "long"},
            {"structure_template": "gated", "conditioning_type": "volume", "horizon_bucket": "short"},
        )
        # 2 out of 3 match -> structure_overlap = 2/3
        assert abs(result["structure_overlap_score"] - 2 / 3) < 0.01

    def test_bucket_boundaries(self):
        idx = _make_multi_index(10, 20)
        rng = np.random.RandomState(4)
        cand = _make_signal(idx, rng.randn(len(idx)))
        # With empty family, score = 0 -> low
        result = compute_family_overlap(cand, {}, {}, {})
        assert result["family_overlap_bucket"] == "low"

    def test_family_history_status(self):
        idx = _make_multi_index(10, 20)
        rng = np.random.RandomState(5)
        cand = _make_signal(idx, rng.randn(len(idx)))
        # One member -> insufficient
        family = {"F001": _make_signal(idx, rng.randn(len(idx)))}
        result = compute_family_overlap(cand, family, {}, {})
        assert result["family_history_status"] == "insufficient"

        # Two members -> sufficient
        family["F002"] = _make_signal(idx, rng.randn(len(idx)))
        result = compute_family_overlap(cand, family, {}, {})
        assert result["family_history_status"] == "sufficient"

    def test_score_formula_components(self):
        """Verify the formula: 0.50*corr_p90 + 0.30*struct + 0.20*(1-residual)."""
        idx = _make_multi_index(30, 60)
        rng = np.random.RandomState(6)
        base = rng.randn(len(idx))
        # Create a moderately correlated member.
        noise = rng.randn(len(idx))
        member_values = 0.7 * base + 0.3 * noise
        cand = _make_signal(idx, base)
        family = {"F001": _make_signal(idx, member_values)}

        cand_struct = {"structure_template": "gated", "conditioning_type": "volume", "horizon_bucket": "short"}
        reg = {"structure_template": "gated", "conditioning_type": "price", "horizon_bucket": "short"}

        result = compute_family_overlap(cand, family, cand_struct, reg)

        # Manual check: reconstruct from components
        expected = (
            0.50 * result["same_family_corr_p90"]
            + 0.30 * result["structure_overlap_score"]
            + 0.20 * (1.0 - max(0.0, min(1.0, result["residual_survival_ratio"])))
        )
        assert abs(result["family_overlap_score"] - round(expected, 4)) < 0.001
