"""
C004 — 10d Barra Residual (shorter lookback for Barra styles)

Use 10-day lookback instead of 20d for Barra style factors.
Shorter-horizon styles may capture faster mean-reversion in style space.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.linalg import pinv

REQUIRED_FIELDS = ["$close", "$volume"]
VECTORIZED = True

# 10d versions of Barra styles
STYLE_NAMES_10D = [
    "log_circ_cap",
    "book_to_price",
    "mom_12_1",
    "str_1m",
    "vol_10d",
    "turnover_10d",
    "ep_ratio",
]

# Map 10d style names to what's available in Barra cache
STYLE_NAME_MAP = {
    "log_circ_cap": "log_circ_cap",
    "book_to_price": "book_to_price",
    "mom_12_1": "mom_12_1",
    "str_1m": "str_1m",
    "vol_10d": "vol_10d",
    "turnover_10d": "turnover_10d",
    "ep_ratio": "ep_ratio",
}

BARRA_CACHE = "storage/cache/barra_factors.parquet"


def _cross_sectional_residual(
    returns: NDArray[np.float64],
    styles: NDArray[np.float64],
    valid: NDArray[np.bool_],
) -> NDArray[np.float64]:
    n_dates, n_symbols, n_styles = styles.shape
    X = np.concatenate([styles, np.ones((n_dates, n_symbols, 1))], axis=2)
    X = np.nan_to_num(X, nan=0.0) * valid[..., None]
    y = np.nan_to_num(returns, nan=0.0) * valid

    XtX = np.einsum("pdi,pdj->pij", X, X)
    Xty = np.einsum("pdi,pd->pi", X, y)

    n_features = X.shape[2]
    XtX_inv = np.zeros((n_dates, n_features, n_features))
    for p in range(n_dates):
        XtX_inv[p] = pinv(XtX[p], rcond=1e-15)

    beta = np.einsum("pij,pj->pi", XtX_inv, Xty)
    residual = y - np.einsum("pdi,pi->pd", X, beta)
    return residual


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
    n_styles = len(STYLE_NAMES_10D)

    style_vals = np.zeros((n_dates, n_symbols, n_styles), dtype=np.float64)
    for k, barra_style in enumerate(STYLE_NAMES_10D):
        cache_name = STYLE_NAME_MAP[barra_style]
        if cache_name not in barra_aligned.columns:
            # Fallback: if vol_10d/turnover_10d not available, use 20d versions
            if barra_style == "vol_10d":
                cache_name = "vol_20d"
            elif barra_style == "turnover_10d":
                cache_name = "turnover_20d"
        if cache_name not in barra_aligned.columns:
            continue
        s = barra_aligned[cache_name].unstack("instrument")
        s_ordered = s.reindex(index=dates_ordered, columns=symbols)
        style_vals[:, :, k] = s_ordered.to_numpy()

    ret_arr = fwd_aligned.unstack("instrument").reindex(
        index=dates_ordered, columns=symbols
    ).values

    valid_ret = ~np.isnan(ret_arr)
    valid_style = ~np.all(np.isnan(style_vals), axis=2)
    valid = valid_ret & valid_style

    residuals = _cross_sectional_residual(ret_arr, style_vals, valid.astype(np.float64))
    residuals = np.where(valid, residuals, np.nan)

    result = pd.Series(
        residuals.ravel(),
        index=pd.MultiIndex.from_product(
            [dates_ordered, symbols], names=["datetime", "instrument"]
        ),
    ).reindex(forward_ret.index)

    return result
