"""Tests for RedundancyEngine: orchestrates all 3 redundancy layers."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.redundancy.engine import (
    RedundancyEngine,
    _get_family_status,
    _filter_family_members,
    _select_basis,
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
# Tests: helper functions
# ---------------------------------------------------------------------------

class TestGetFamilyStatus:
    def test_unknown_when_empty(self):
        assert _get_family_status("", {}) == "unknown"
        assert _get_family_status("FM_unknown", {}) == "unknown"

    def test_unknown_when_not_in_registry(self):
        assert _get_family_status("FM_foo", {}) == "unknown"

    def test_registered_default(self):
        reg = {"FM_breakout": {"status": "registered"}}
        assert _get_family_status("FM_breakout", reg) == "registered"

    def test_provisional(self):
        reg = {"FM_new": {"status": "provisional"}}
        assert _get_family_status("FM_new", reg) == "provisional"

    def test_no_status_key_defaults_to_registered(self):
        reg = {"FM_x": {}}
        assert _get_family_status("FM_x", reg) == "registered"


class TestFilterFamilyMembers:
    def test_filters_by_family_id(self):
        lib_signals = {"F001": "sig1", "F002": "sig2", "F003": "sig3"}
        lib_meta = {
            "F001": {"family_id": "FM_a"},
            "F002": {"family_id": "FM_b"},
            "F003": {"family_id": "FM_a"},
        }
        result = _filter_family_members(lib_signals, lib_meta, "FM_a")
        assert set(result.keys()) == {"F001", "F003"}

    def test_empty_when_no_match(self):
        result = _filter_family_members(
            {"F001": "sig1"}, {"F001": {"family_id": "FM_x"}}, "FM_y",
        )
        assert result == {}


class TestSelectBasis:
    def test_prefers_same_family(self):
        lib_signals = {"F001": "s1", "F002": "s2", "F003": "s3", "F004": "s4"}
        lib_meta = {
            "F001": {"family_id": "FM_a", "logic_id": "L1"},
            "F002": {"family_id": "FM_a", "logic_id": "L1"},
            "F003": {"family_id": "FM_b", "logic_id": "L1"},
            "F004": {"family_id": "FM_a", "logic_id": "L1"},
        }
        basis = _select_basis(
            {"family_id": "FM_a", "logic_id": "L1"},
            lib_signals, lib_meta, "FM_a", k=3,
        )
        # Should pick F001, F002, F004 (all FM_a)
        assert set(basis.keys()) == {"F001", "F002", "F004"}

    def test_fills_with_same_logic(self):
        lib_signals = {"F001": "s1", "F002": "s2", "F003": "s3"}
        lib_meta = {
            "F001": {"family_id": "FM_a", "logic_id": "L1"},
            "F002": {"family_id": "FM_b", "logic_id": "L1"},
            "F003": {"family_id": "FM_c", "logic_id": "L2"},
        }
        corrs = {"F002": 0.5, "F003": 0.3}
        basis = _select_basis(
            {"family_id": "FM_a", "logic_id": "L1"},
            lib_signals, lib_meta, "FM_a",
            pairwise_corrs=corrs, k=3,
        )
        # F001 from family, F002 from same logic
        assert "F001" in basis
        assert "F002" in basis
        assert "F003" not in basis  # different logic_id

    def test_respects_k_limit(self):
        lib_signals = {f"F{i:03d}": f"s{i}" for i in range(10)}
        lib_meta = {f"F{i:03d}": {"family_id": "FM_a"} for i in range(10)}
        basis = _select_basis({}, lib_signals, lib_meta, "FM_a", k=3)
        assert len(basis) == 3


# ---------------------------------------------------------------------------
# Tests: RedundancyEngine.analyze
# ---------------------------------------------------------------------------

class TestRedundancyEngine:
    def setup_method(self):
        self.engine = RedundancyEngine()
        self.idx = _make_multi_index(20, 50)
        self.n = len(self.idx)
        self.rng = np.random.RandomState(42)

    def test_full_analysis_registered_family(self):
        """Full 3-layer analysis with registered family."""
        cand = _make_signal(self.idx, self.rng.randn(self.n))
        lib_signals = {
            "F001": _make_signal(self.idx, self.rng.randn(self.n)),
            "F002": _make_signal(self.idx, self.rng.randn(self.n)),
            "F003": _make_signal(self.idx, self.rng.randn(self.n)),
        }
        lib_meta = {
            "F001": {"family_id": "FM_vol", "logic_id": "L1"},
            "F002": {"family_id": "FM_vol", "logic_id": "L1"},
            "F003": {"family_id": "FM_mom", "logic_id": "L2"},
        }
        family_registry = {
            "FM_vol": {
                "status": "registered",
                "structure_template": "gated",
                "conditioning_type": "volume",
                "horizon_bucket": "short",
            },
        }
        fwd = _make_signal(self.idx, self.rng.randn(self.n))

        result = self.engine.analyze(
            cand,
            {"family_id": "FM_vol", "logic_id": "L1",
             "structure_template": "gated", "conditioning_type": "volume",
             "horizon_bucket": "short"},
            lib_signals, lib_meta, family_registry, fwd,
        )

        assert "pairwise" in result
        assert result["pairwise"]["max_lib_corr"] is not None

        assert "family_view" in result
        assert result["family_view"] is not None
        assert result["family_view"]["family_assignment_status"] == "registered"
        assert "family_overlap_score" in result["family_view"]

        assert "subspace_view" in result
        assert result["subspace_view"] is not None

    def test_unknown_family_skips_family_layer(self):
        cand = _make_signal(self.idx, self.rng.randn(self.n))
        lib_signals = {"F001": _make_signal(self.idx, self.rng.randn(self.n))}
        lib_meta = {"F001": {"family_id": "FM_x"}}

        result = self.engine.analyze(
            cand,
            {"family_id": "FM_unknown"},
            lib_signals, lib_meta, {}, None,
        )

        assert result["family_view"]["family_assignment_status"] == "unknown"
        assert result["family_view"]["family_overlap_score"] is None
        assert result["subspace_view"] is None  # no forward_returns

    def test_provisional_family(self):
        cand = _make_signal(self.idx, self.rng.randn(self.n))
        lib_signals = {
            "F001": _make_signal(self.idx, self.rng.randn(self.n)),
        }
        lib_meta = {"F001": {"family_id": "FM_new"}}
        family_registry = {"FM_new": {"status": "provisional"}}

        result = self.engine.analyze(
            cand,
            {"family_id": "FM_new"},
            lib_signals, lib_meta, family_registry, None,
        )

        assert result["family_view"]["family_assignment_status"] == "provisional"
        assert result["family_view"]["family_registry_check"] == "degraded"

    def test_insufficient_basis_for_subspace(self):
        """When fewer than 2 basis factors, subspace should report insufficient."""
        cand = _make_signal(self.idx, self.rng.randn(self.n))
        lib_signals = {"F001": _make_signal(self.idx, self.rng.randn(self.n))}
        lib_meta = {"F001": {"family_id": "FM_a", "logic_id": "L1"}}
        family_registry = {"FM_a": {"status": "registered"}}
        fwd = _make_signal(self.idx, self.rng.randn(self.n))

        result = self.engine.analyze(
            cand,
            {"family_id": "FM_a", "logic_id": "L_other"},
            lib_signals, lib_meta, family_registry, fwd,
        )

        assert result["subspace_view"]["subspace_confidence"] == "insufficient_basis"
        assert result["subspace_view"]["subspace_redundancy_score"] is None

    def test_no_library_factors(self):
        """Engine should handle empty library gracefully."""
        cand = _make_signal(self.idx, self.rng.randn(self.n))

        result = self.engine.analyze(
            cand, {"family_id": "FM_unknown"}, {}, {}, {}, None,
        )

        assert result["pairwise"]["max_lib_corr"] == 0.0
        assert result["family_view"]["family_assignment_status"] == "unknown"
        assert result["subspace_view"] is None

    def test_near_duplicate_detected_through_engine(self):
        """An identical library factor should be flagged as near-duplicate."""
        values = self.rng.randn(self.n)
        cand = _make_signal(self.idx, values)
        lib_signals = {"F001": _make_signal(self.idx, values.copy())}
        lib_meta = {"F001": {"family_id": "FM_x"}}

        result = self.engine.analyze(
            cand, {"family_id": "FM_y"}, lib_signals, lib_meta, {}, None,
        )

        assert result["pairwise"]["is_near_duplicate"] is True
        assert result["pairwise"]["max_lib_corr"] > 0.99
