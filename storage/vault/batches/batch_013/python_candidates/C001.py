"""
C001 — Barra Residual Alpha (Full Barra style orthogonal residual)

Baseline: Replicate Barra_residual_return (C001 from batch_012).
Regress Returns ~ Barra 7 style factors, take residual as alpha signal.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.linalg import pinv

REQUIRED_FIELDS = ["$close", "$volume"]
VECTORIZED = True

STYLE_NAMES = [
    "log_circ_cap",
    "book_to_price",
    "mom_12_1",
    "str_1m",
    "vol_20d",
    "turnover_20d",
    "ep_ratio",
]

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
    n_styles = len(STYLE_NAMES)

    style_vals = np.zeros((n_dates, n_symbols, n_styles), dtype=np.float64)
    for k, style_name in enumerate(STYLE_NAMES):
        if style_name not in barra_aligned.columns:
            continue
        s = barra_aligned[style_name].unstack("instrument")
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
