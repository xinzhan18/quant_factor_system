"""Tests for research.stats.effect_strength."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.stats.effect_strength import compute_effect_strength


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
    """Build a flat [time, symbol, value] panel with controlled properties."""
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


class TestComputeEffectStrength:
    """Tests for compute_effect_strength."""

    def test_positive_signal(self):
        """Factor positively correlated with returns yields positive IC."""
        rng = np.random.default_rng(42)
        n_dates, n_sym = 500, 100
        factor_signal = rng.normal(size=(n_dates, n_sym))
        # Returns = factor + noise => positive correlation
        returns_signal = factor_signal * 0.3 + rng.normal(size=(n_dates, n_sym)) * 0.7

        start = "2018-01-01"
        fv = _make_panel(n_dates, n_sym, start, rng, factor_signal)
        fr = _make_panel(n_dates, n_sym, start, rng, returns_signal)

        dates = sorted(fv["time"].unique())
        mid = dates[n_dates // 2]

        result = compute_effect_strength(
            fv, fr,
            train_range=(str(dates[0].date()), str(mid.date())),
            validation_range=(str((mid + pd.Timedelta(days=1)).date()), str(dates[-1].date())),
        )

        assert result["ic_mean_train"] > 0
        assert result["ic_mean_validation"] > 0
        assert 0 < result["ic_win_rate_validation"] <= 1.0
        assert isinstance(result["ic_series_train"], pd.Series)
        assert isinstance(result["ic_series_validation"], pd.Series)

    def test_negative_signal(self):
        """Factor negatively correlated with returns yields negative IC."""
        rng = np.random.default_rng(7)
        n_dates, n_sym = 400, 80
        factor_signal = rng.normal(size=(n_dates, n_sym))
        returns_signal = -factor_signal * 0.3 + rng.normal(size=(n_dates, n_sym)) * 0.7

        start = "2017-01-01"
        fv = _make_panel(n_dates, n_sym, start, rng, factor_signal)
        fr = _make_panel(n_dates, n_sym, start, rng, returns_signal)

        dates = sorted(fv["time"].unique())
        mid = dates[n_dates // 2]

        result = compute_effect_strength(
            fv, fr,
            train_range=(str(dates[0].date()), str(mid.date())),
            validation_range=(str((mid + pd.Timedelta(days=1)).date()), str(dates[-1].date())),
        )

        assert result["ic_mean_train"] < 0
        assert result["ic_mean_validation"] < 0

    def test_no_signal(self):
        """Pure noise factor has IC near zero."""
        rng = np.random.default_rng(99)
        n_dates, n_sym = 400, 100
        factor_signal = rng.normal(size=(n_dates, n_sym))
        returns_signal = rng.normal(size=(n_dates, n_sym))

        start = "2019-01-01"
        fv = _make_panel(n_dates, n_sym, start, rng, factor_signal)
        fr = _make_panel(n_dates, n_sym, start, rng, returns_signal)

        dates = sorted(fv["time"].unique())
        mid = dates[n_dates // 2]

        result = compute_effect_strength(
            fv, fr,
            train_range=(str(dates[0].date()), str(mid.date())),
            validation_range=(str((mid + pd.Timedelta(days=1)).date()), str(dates[-1].date())),
        )

        # IC should be close to zero
        assert abs(result["ic_mean_train"]) < 0.05
        assert abs(result["ic_mean_validation"]) < 0.05

    def test_monotonicity_output(self):
        """Monotonicity is a scalar in [-1, 1]."""
        rng = np.random.default_rng(11)
        n_dates, n_sym = 300, 60
        factor_signal = rng.normal(size=(n_dates, n_sym))
        returns_signal = factor_signal * 0.5 + rng.normal(size=(n_dates, n_sym)) * 0.5

        start = "2020-01-01"
        fv = _make_panel(n_dates, n_sym, start, rng, factor_signal)
        fr = _make_panel(n_dates, n_sym, start, rng, returns_signal)

        dates = sorted(fv["time"].unique())
        mid = dates[n_dates // 2]

        result = compute_effect_strength(
            fv, fr,
            train_range=(str(dates[0].date()), str(mid.date())),
            validation_range=(str((mid + pd.Timedelta(days=1)).date()), str(dates[-1].date())),
        )

        mono = result["monotonicity_validation"]
        assert -1.0 <= mono <= 1.0 or np.isnan(mono)

    def test_empty_factor_values(self):
        """Empty factor values returns NaN metrics."""
        fv = pd.DataFrame(columns=["time", "symbol", "value"])
        fr = pd.DataFrame(columns=["time", "symbol", "value"])

        result = compute_effect_strength(
            fv, fr,
            train_range=("2020-01-01", "2021-12-31"),
            validation_range=("2022-01-01", "2023-12-31"),
        )

        assert np.isnan(result["ic_mean_train"])
        assert np.isnan(result["ic_mean_validation"])
