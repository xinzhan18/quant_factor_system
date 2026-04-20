"""
C001 — Huber Regression Residual (robust to outliers)

OLS residual is sensitive to extreme returns; Huber regression with M=1.345*sigma
downweights outliers, which may yield a more stable residual signal.
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
HUBER_M = 1.345


def _huber_irls(X: NDArray, y: NDArray, valid: NDArray, n_iter: int = 5) -> NDArray:
    """Iteratively reweighted least squares for Huber loss; per-date 2D."""
    n_dates, n_symbols, n_features = X.shape
    beta = np.zeros((n_dates, n_features))
    Xm = X * valid[..., None]
    ym = y * valid

    XtX = np.einsum("pdi,pdj->pij", Xm, Xm)
    Xty = np.einsum("pdi,pd->pi", Xm, ym)
    for p in range(n_dates):
        beta[p] = pinv(XtX[p], rcond=1e-15) @ Xty[p]

    for _ in range(n_iter):
        resid = ym - np.einsum("pdi,pi->pd", Xm, beta)
        scale = 1.4826 * np.median(np.abs(resid - np.median(resid, axis=1, keepdims=True)), axis=1, keepdims=True)
        scale = np.where(scale < 1e-9, 1e-9, scale)
        u = resid / scale
        w = np.where(np.abs(u) <= HUBER_M, 1.0, HUBER_M / np.abs(u + 1e-12))
        w = w * valid
        XwX = np.einsum("pdi,pd,pdj->pij", Xm, w, Xm)
        Xwy = np.einsum("pdi,pd,pd->pi", Xm, w, ym)
        for p in range(n_dates):
            beta[p] = pinv(XwX[p], rcond=1e-15) @ Xwy[p]
    return ym - np.einsum("pdi,pi->pd", Xm, beta)


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
        if sn not in barra_aligned.columns:
            continue
        s = barra_aligned[sn].unstack("instrument")
        style_vals[:, :, k] = s.reindex(index=dates_ordered, columns=symbols).to_numpy()

    ret_arr = fwd_aligned.unstack("instrument").reindex(index=dates_ordered, columns=symbols).values
    valid = (~np.isnan(ret_arr)) & (~np.all(np.isnan(style_vals), axis=2))
    X = np.concatenate([style_vals, np.ones((n_dates, n_symbols, 1))], axis=2)
    X = np.nan_to_num(X, nan=0.0)
    y = np.nan_to_num(ret_arr, nan=0.0)

    residuals = _huber_irls(X, y, valid.astype(np.float64))
    residuals = np.where(valid, residuals, np.nan)

    return pd.Series(
        residuals.ravel(),
        index=pd.MultiIndex.from_product([dates_ordered, symbols], names=["datetime", "instrument"]),
    ).reindex(forward_ret.index)
