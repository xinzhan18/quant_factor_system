"""Tests for research.stats.probe."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.stats.probe import run_probe


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_panel(
    n_dates: int,
    n_symbols: int,
    start: str,
    rng: np.random.Generator,
    signal: np.ndarray | None = None,
) -> pd.DataFrame:
    dates = pd.bdate_range(start, periods=n_dates, freq="B")
    symbols = [f"S{i:03d}" for i in range(n_symbols)]
    rows = []
    for i, d in enumerate(dates):
        for j, s in enumerate(symbols):
            val = signal[i, j] if signal is not None else rng.normal()
            rows.append({"time": d, "symbol": s, "value": val})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestRunProbe:

    def test_strong_signal_passes(self):
        """Strong positive IC factor -> pass."""
        rng = np.random.default_rng(42)
        n, s = 500, 80
        factor = rng.normal(size=(n, s))
        returns = factor * 0.4 + rng.normal(size=(n, s)) * 0.6

        fv = _make_panel(n, s, "2018-01-01", rng, factor)
        fr = _make_panel(n, s, "2018-01-01", rng, returns)

        splits = [
            ("2018-01-01", "2019-06-30"),
            ("2019-07-01", "2020-12-31"),
        ]

        result = run_probe(fv, fr, train_splits=splits)

        assert result["computable"] is True
        assert result["variance_ok"] is True
        assert result["signal_strength_hint"] in ("strong", "medium")
        assert result["verdict"] == "pass"

    def test_noise_factor_fails(self):
        """Pure noise factor -> fail or reserve."""
        rng = np.random.default_rng(99)
        n, s = 400, 80
        factor = rng.normal(size=(n, s))
        returns = rng.normal(size=(n, s))

        fv = _make_panel(n, s, "2018-01-01", rng, factor)
        fr = _make_panel(n, s, "2018-01-01", rng, returns)

        splits = [
            ("2018-01-01", "2019-06-30"),
            ("2019-07-01", "2020-12-31"),
        ]

        result = run_probe(fv, fr, train_splits=splits)
        assert result["verdict"] in ("fail", "reserve")

    def test_empty_factor_fails(self):
        """Empty factor data -> fail."""
        fv = pd.DataFrame(columns=["time", "symbol", "value"])
        fr = pd.DataFrame(columns=["time", "symbol", "value"])

        result = run_probe(fv, fr, train_splits=[("2020-01-01", "2021-12-31")])
        assert result["verdict"] == "fail"
        assert result["computable"] is False

    def test_constant_factor_fails(self):
        """Near-constant factor -> fail."""
        rng = np.random.default_rng(5)
        n, s = 200, 50
        factor = np.ones((n, s)) * 42.0  # Constant
        returns = rng.normal(size=(n, s))

        fv = _make_panel(n, s, "2020-01-01", rng, factor)
        fr = _make_panel(n, s, "2020-01-01", rng, returns)

        result = run_probe(fv, fr, train_splits=[("2020-01-01", "2021-12-31")])
        assert result["verdict"] == "fail"
        assert result["variance_ok"] is False

    def test_forbidden_pattern(self):
        """Matching a forbidden pattern -> fail."""
        rng = np.random.default_rng(42)
        n, s = 200, 50
        factor = rng.normal(size=(n, s))
        returns = factor * 0.3 + rng.normal(size=(n, s)) * 0.7

        fv = _make_panel(n, s, "2020-01-01", rng, factor)
        fr = _make_panel(n, s, "2020-01-01", rng, returns)

        result = run_probe(
            fv, fr,
            train_splits=[("2020-01-01", "2021-12-31")],
            forbidden_patterns=[r"\$vwap"],
            expression="Rank($vwap)",
        )
        assert result["forbidden_hit"] is True
        assert result["verdict"] == "fail"

    def test_complex_expression_reserve(self):
        """Overly nested expression -> reserve."""
        rng = np.random.default_rng(42)
        n, s = 300, 50
        factor = rng.normal(size=(n, s))
        returns = factor * 0.3 + rng.normal(size=(n, s)) * 0.7

        fv = _make_panel(n, s, "2018-01-01", rng, factor)
        fr = _make_panel(n, s, "2018-01-01", rng, returns)

        # Deeply nested expression
        deep = "A(" * 15 + "$close" + ")" * 15

        result = run_probe(
            fv, fr,
            train_splits=[("2018-01-01", "2019-06-30"), ("2019-07-01", "2020-12-31")],
            expression=deep,
            max_complexity=10,
        )
        assert result["complexity_ok"] is False
        # Should not be pass
        assert result["verdict"] in ("reserve", "fail")

    def test_low_valid_ratio_fails(self):
        """Mostly NaN factor -> fail."""
        rng = np.random.default_rng(3)
        n, s = 200, 50
        factor = rng.normal(size=(n, s))
        # Set 80% to NaN
        mask = rng.random((n, s)) < 0.80
        factor[mask] = np.nan

        fv = _make_panel(n, s, "2020-01-01", rng, factor)
        fr = _make_panel(n, s, "2020-01-01", rng)

        result = run_probe(fv, fr, train_splits=[("2020-01-01", "2021-12-31")])
        assert result["valid_ratio"] < 0.30
        assert result["verdict"] == "fail"

    def test_output_keys(self):
        """All expected keys are present in the output."""
        rng = np.random.default_rng(42)
        n, s = 300, 60
        factor = rng.normal(size=(n, s))
        returns = factor * 0.3 + rng.normal(size=(n, s)) * 0.7

        fv = _make_panel(n, s, "2018-01-01", rng, factor)
        fr = _make_panel(n, s, "2018-01-01", rng, returns)

        result = run_probe(
            fv, fr,
            train_splits=[("2018-01-01", "2019-06-30"), ("2019-07-01", "2020-12-31")],
        )

        expected_keys = {
            "computable", "valid_ratio", "variance_ok", "forbidden_hit",
            "complexity_ok", "signal_strength_hint", "split_consistency_hint",
            "duplicate_risk_hint", "verdict",
        }
        assert expected_keys.issubset(result.keys())
