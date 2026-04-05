"""Tests for risk/exposures.py — Barra exposure regression."""

import numpy as np
import pandas as pd

from research.risk.exposures import compute_barra_exposures


def _make_flat(n_dates=100, n_stocks=80, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2022-01-01", periods=n_dates)
    stocks = [f"S{i:03d}" for i in range(n_stocks)]
    records = []
    for d in dates:
        for s in stocks:
            records.append({"time": d, "symbol": s, "value": rng.normal()})
    return pd.DataFrame(records)


def _make_style_matrix(n_dates=100, n_stocks=80, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2022-01-01", periods=n_dates)
    stocks = [f"S{i:03d}" for i in range(n_stocks)]
    idx = pd.MultiIndex.from_product([dates, stocks], names=["datetime", "instrument"])
    cols = ["log_circ_cap", "book_to_price", "mom_12_1", "str_1m",
            "vol_20d", "turnover_20d", "ep_ratio"]
    data = rng.normal(size=(len(idx), len(cols)))
    return pd.DataFrame(data, index=idx, columns=cols)


class TestComputeBarraExposures:
    def test_pure_size_factor(self):
        """Alpha = size style → dominant should be log_circ_cap, survival low."""
        rng = np.random.default_rng(10)
        n_dates, n_stocks = 100, 80
        dates = pd.bdate_range("2022-01-01", periods=n_dates)
        stocks = [f"S{i:03d}" for i in range(n_stocks)]
        idx = pd.MultiIndex.from_product([dates, stocks], names=["datetime", "instrument"])

        style_matrix = _make_style_matrix(n_dates, n_stocks, seed=10)
        # Alpha = size + tiny noise
        size_vals = style_matrix["log_circ_cap"].values
        factor_flat = []
        i = 0
        for d in dates:
            for s in stocks:
                factor_flat.append({"time": d, "symbol": s, "value": size_vals[i] + rng.normal(0, 0.1)})
                i += 1
        factor_flat = pd.DataFrame(factor_flat)

        returns_flat = _make_flat(n_dates, n_stocks, seed=99)

        result = compute_barra_exposures(
            factor_flat, style_matrix, returns_flat, raw_view_ic=0.02
        )

        assert result["dominant_style_exposure"] == "log_circ_cap"
        assert result["style_r_squared"] > 0.5
        assert result["style_crowding_risk"] in ("medium", "high")

    def test_orthogonal_factor(self):
        """Alpha = random noise → low exposures, high survival."""
        factor_flat = _make_flat(seed=77)
        style_matrix = _make_style_matrix(seed=88)
        returns_flat = _make_flat(seed=99)

        result = compute_barra_exposures(
            factor_flat, style_matrix, returns_flat, raw_view_ic=0.02
        )

        assert result["style_r_squared"] is not None
        assert result["style_r_squared"] < 0.3
        assert result["style_crowding_risk"] in ("low", "medium")

    def test_survival_nan_when_raw_ic_tiny(self):
        factor_flat = _make_flat()
        style_matrix = _make_style_matrix()
        returns_flat = _make_flat(seed=99)

        result = compute_barra_exposures(
            factor_flat, style_matrix, returns_flat, raw_view_ic=1e-6
        )
        assert result["alpha_survival_ratio"] is None

    def test_empty_factor(self):
        empty = pd.DataFrame(columns=["time", "symbol", "value"])
        style_matrix = _make_style_matrix()
        returns_flat = _make_flat(seed=99)

        result = compute_barra_exposures(
            empty, style_matrix, returns_flat, raw_view_ic=0.02
        )
        assert result["style_exposures"] == {}
        assert result["barra_residual_ic"] is None

    def test_empty_style_matrix(self):
        factor_flat = _make_flat()
        empty_style = pd.DataFrame()
        returns_flat = _make_flat(seed=99)

        result = compute_barra_exposures(
            factor_flat, empty_style, returns_flat, raw_view_ic=0.02
        )
        assert result["style_exposures"] == {}

    def test_crowding_high(self):
        """Manually verify high crowding classification."""
        from research.risk.exposures import _classify_crowding
        assert _classify_crowding(0.30, {"a": 0.6}) == "high"

    def test_crowding_medium(self):
        from research.risk.exposures import _classify_crowding
        assert _classify_crowding(0.15, {"a": 0.1}) == "medium"

    def test_crowding_low(self):
        from research.risk.exposures import _classify_crowding
        assert _classify_crowding(0.05, {"a": 0.1}) == "low"
