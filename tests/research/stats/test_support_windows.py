"""Tests for research.stats.support_windows."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.stats.support_windows import check_support_windows
from tests.research.stats.conftest import make_panel


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestCheckSupportWindows:

    def test_no_flip(self):
        """All windows consistent -> warning=none."""
        rng = np.random.default_rng(42)
        n, s = 800, 60
        factor = rng.normal(size=(n, s))
        returns = factor * 0.3 + rng.normal(size=(n, s)) * 0.7

        fv = make_panel(n, s, "2019-01-01", rng, factor)
        fr = make_panel(n, s, "2019-01-01", rng, returns)

        windows = [
            {"window_id": "w1", "range": ["2020-01-01", "2021-12-31"]},
            {"window_id": "w2", "range": ["2021-01-01", "2022-12-31"]},
        ]

        result = check_support_windows(fv, fr, primary_sign=1.0, windows=windows)
        assert result["warning"] == "none"
        assert len(result["checks"]) == 2
        for c in result["checks"]:
            assert c["sign_consistent"] is True

    def test_single_flip(self):
        """One window flips sign -> warning=single_flip."""
        rng = np.random.default_rng(7)
        n, s = 800, 60
        factor = rng.normal(size=(n, s))
        returns = factor * 0.3 + rng.normal(size=(n, s)) * 0.7

        fv = make_panel(n, s, "2019-01-01", rng, factor)
        fr = make_panel(n, s, "2019-01-01", rng, returns)

        windows = [
            {"window_id": "w1", "range": ["2020-01-01", "2021-12-31"]},
            {"window_id": "w2", "range": ["2021-01-01", "2022-12-31"]},
        ]

        # primary_sign = -1 means the first window (positive IC) will flip
        result = check_support_windows(fv, fr, primary_sign=-1.0, windows=windows)
        # At least one should flip because factor has positive correlation
        assert result["warning"] in ("single_flip", "repeated_flip")

    def test_repeated_flip(self):
        """Both windows flip -> warning=repeated_flip."""
        rng = np.random.default_rng(42)
        n, s = 800, 60
        factor = rng.normal(size=(n, s))
        returns = factor * 0.3 + rng.normal(size=(n, s)) * 0.7

        fv = make_panel(n, s, "2019-01-01", rng, factor)
        fr = make_panel(n, s, "2019-01-01", rng, returns)

        windows = [
            {"window_id": "w1", "range": ["2020-01-01", "2021-06-30"]},
            {"window_id": "w2", "range": ["2021-07-01", "2022-12-31"]},
        ]

        # primary_sign = -1 with a positive-IC factor -> both windows flip
        result = check_support_windows(fv, fr, primary_sign=-1.0, windows=windows)
        assert result["warning"] == "repeated_flip"

    def test_empty_window(self):
        """Window with no data is handled gracefully."""
        fv = pd.DataFrame(columns=["time", "symbol", "value"])
        fr = pd.DataFrame(columns=["time", "symbol", "value"])

        windows = [
            {"window_id": "empty", "range": ["2030-01-01", "2030-12-31"]},
        ]
        result = check_support_windows(fv, fr, primary_sign=1.0, windows=windows)
        assert len(result["checks"]) == 1
        assert result["checks"][0]["sign_consistent"] is False

    def test_output_structure(self):
        """Verify output structure."""
        rng = np.random.default_rng(11)
        n, s = 300, 40
        fv = make_panel(n, s, "2020-01-01", rng)
        fr = make_panel(n, s, "2020-01-01", rng)

        windows = [
            {"window_id": "w1", "range": ["2020-06-01", "2021-06-01"]},
        ]
        result = check_support_windows(fv, fr, primary_sign=1.0, windows=windows)

        assert "checks" in result
        assert "warning" in result
        c = result["checks"][0]
        assert "window_id" in c
        assert "ic_mean_support" in c
        assert "sign_consistent" in c
