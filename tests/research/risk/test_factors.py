"""Tests for risk/factors.py — 7 style factors."""

import numpy as np
import pandas as pd

from research.risk.factors import compute_style_factor_matrix
from research.risk.constants import STYLE_NAMES


def _make_market_data(n_dates=300, n_stocks=50, seed=42):
    """Synthetic market data with (datetime, instrument) MultiIndex."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2021-01-01", periods=n_dates)
    stocks = [f"S{i:03d}" for i in range(n_stocks)]
    idx = pd.MultiIndex.from_product([dates, stocks], names=["datetime", "instrument"])
    n = len(idx)

    close = pd.Series(rng.lognormal(4, 0.3, n), index=idx, name="$close")
    circ_cap = pd.Series(rng.lognormal(10, 1, n), index=idx, name="$circ_market_cap")
    pb = pd.Series(rng.uniform(0.5, 10, n), index=idx, name="$pb_ratio")
    pe = pd.Series(rng.uniform(5, 50, n), index=idx, name="$pe_ratio")
    turnover = pd.Series(rng.uniform(0.01, 0.1, n), index=idx, name="$turnover_rate")

    return close, circ_cap, pb, pe, turnover


class TestComputeStyleFactorMatrix:
    def test_output_has_7_columns(self):
        close, cap, pb, pe, to = _make_market_data()
        matrix = compute_style_factor_matrix(close, cap, pb, pe, to)
        assert set(matrix.columns) == set(STYLE_NAMES)

    def test_output_multiindex(self):
        close, cap, pb, pe, to = _make_market_data()
        matrix = compute_style_factor_matrix(close, cap, pb, pe, to)
        assert matrix.index.names == ["datetime", "instrument"]

    def test_size_monotone_with_cap(self):
        close, cap, pb, pe, to = _make_market_data(n_dates=50)
        matrix = compute_style_factor_matrix(close, cap, pb, pe, to)
        # On each date, higher cap should generally → higher log_circ_cap z-score
        date = matrix.index.get_level_values(0).unique()[40]
        day_cap = cap.loc[date].dropna()
        day_size = matrix.loc[date, "log_circ_cap"].dropna()
        common = day_cap.index.intersection(day_size.index)
        if len(common) > 20:
            from scipy.stats import spearmanr
            corr, _ = spearmanr(day_cap.loc[common], day_size.loc[common])
            assert corr > 0.8

    def test_value_nan_for_negative_pb(self):
        close, cap, pb, pe, to = _make_market_data(n_dates=50)
        pb.iloc[:100] = -1.0  # negative PB
        matrix = compute_style_factor_matrix(close, cap, pb, pe, to)
        # Those entries should be NaN in book_to_price
        btp = matrix["book_to_price"]
        first_date = btp.index.get_level_values(0).unique()[0]
        assert btp.loc[first_date].isna().sum() > 0

    def test_momentum_nan_early_dates(self):
        close, cap, pb, pe, to = _make_market_data(n_dates=300)
        matrix = compute_style_factor_matrix(close, cap, pb, pe, to)
        # First ~252 dates should have NaN momentum (insufficient history)
        early_date = matrix.index.get_level_values(0).unique()[10]
        assert matrix.loc[early_date, "mom_12_1"].isna().all()

    def test_normalization_per_date(self):
        close, cap, pb, pe, to = _make_market_data(n_dates=300)
        matrix = compute_style_factor_matrix(close, cap, pb, pe, to)
        # Check a late date where all factors should have valid data
        late_date = matrix.index.get_level_values(0).unique()[-1]
        for col in ["log_circ_cap", "vol_20d", "turnover_20d"]:
            vals = matrix.loc[late_date, col].dropna()
            if len(vals) > 10:
                assert abs(vals.mean()) < 0.1
                assert abs(vals.std() - 1.0) < 0.2
