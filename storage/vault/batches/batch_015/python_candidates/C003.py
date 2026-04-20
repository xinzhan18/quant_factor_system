"""
C003 — Heteroscedastic-Aware Residual: OLS residual / rolling 20d std

Standardizes Barra residual by its rolling 20d cross-sectional std per symbol,
producing a z-score-like signal robust to time-varying volatility regimes.
Hypothesis: F004 raw residual is contaminated by vol regime shifts; per-symbol
normalization recovers cleaner alpha.
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.linalg import pinv

REQUIRED_FIELDS = ["$close"]
VECTORIZED = True

STYLE_NAMES = ["log_circ_cap", "book_to_price", "mom_12_1", "str_1m", "vol_20d", "turnover_20d", "ep_ratio"]
BARRA_CACHE = "storage/cache/barra_factors.parquet"
NORM_WINDOW = 20


def _cs_residual(returns, styles, valid):
    n_dates, n_symbols, _ = styles.shape
    X = np.concatenate([styles, np.ones((n_dates, n_symbols, 1))], axis=2)
    X = np.nan_to_num(X, nan=0.0) * valid[..., None]
    y = np.nan_to_num(returns, nan=0.0) * valid
    XtX = np.einsum("pdi,pdj->pij", X, X)
    Xty = np.einsum("pdi,pd->pi", X, y)
    beta = np.zeros((n_dates, X.shape[2]))
    for p in range(n_dates):
        beta[p] = pinv(XtX[p], rcond=1e-15) @ Xty[p]
    return y - np.einsum("pdi,pi->pd", X, beta)


def compute(df: pd.DataFrame) -> pd.Series:
    barra: pd.DataFrame = pd.read_parquet(BARRA_CACHE)
    ret = df["$close"].unstack("instrument")
    forward_ret = ret.shift(-1).stack("instrument")
    forward_ret.name = "returns_fwd"

    common_idx = forward_ret.index.intersection(barra.index)
    fwd_aligned = forward_ret.reindex(common_idx)
    barra_aligned = barra.reindex(common_idx)

    dates_ordered = fwd_aligned.index.get_level_values("datetime").unique()
    symbols = fwd_aligned.index.get_level_values("instrument").unique()
    n_dates = len(dates_ordered)
    n_symbols = len(symbols)

    style_vals = np.zeros((n_dates, n_symbols, len(STYLE_NAMES)), dtype=np.float64)
    for k, sn in enumerate(STYLE_NAMES):
        if sn in barra_aligned.columns:
            s = barra_aligned[sn].unstack("instrument")
            style_vals[:, :, k] = s.reindex(index=dates_ordered, columns=symbols).to_numpy()

    ret_arr = fwd_aligned.unstack("instrument").reindex(index=dates_ordered, columns=symbols).values
    valid = (~np.isnan(ret_arr)) & (~np.all(np.isnan(style_vals), axis=2))

    residuals = _cs_residual(ret_arr, style_vals, valid.astype(np.float64))
    residuals = np.where(valid, residuals, np.nan)

    # Per-symbol rolling 20d std normalization
    res_df = pd.DataFrame(residuals, index=dates_ordered, columns=symbols)
    rolling_std = res_df.rolling(NORM_WINDOW, min_periods=10).std()
    rolling_std = rolling_std.where(rolling_std > 1e-9, 1e-9)
    z = res_df / rolling_std

    return pd.Series(
        z.values.ravel(),
        index=pd.MultiIndex.from_product([dates_ordered, symbols], names=["datetime", "instrument"]),
    ).reindex(forward_ret.index)
