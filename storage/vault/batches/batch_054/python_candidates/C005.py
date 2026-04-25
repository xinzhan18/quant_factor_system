"""C005 — Multi-period residual decay (EMA half-life proxy).

Pure residual-only signal: ratio of short-EMA to long-EMA of past residual
returns — a momentum/decay structure on idiosyncratic returns. Tests
whether residual returns exhibit multi-period coherence.

Signal = EMA(residual, span=5) - EMA(residual, span=20)

A positive value means recent residual return exceeds longer-term trend
(idiosyncratic momentum acceleration).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.linalg import pinv

REQUIRED_FIELDS = ["$close"]
VECTORIZED = True

STYLE_NAMES = [
    "log_circ_cap", "book_to_price", "mom_12_1", "str_1m",
    "vol_20d", "turnover_20d", "ep_ratio",
]
BARRA_CACHE = "storage/cache/barra_factors.parquet"


def _cross_sectional_residual(returns, styles, valid):
    n_dates, n_symbols, _ = styles.shape
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
    return y - np.einsum("pdi,pi->pd", X, beta)


def compute(df: pd.DataFrame) -> pd.Series:
    barra = pd.read_parquet(BARRA_CACHE)

    close_w = df["$close"].unstack("instrument").sort_index()
    past_ret_w = close_w.pct_change(1)
    past_ret = past_ret_w.stack("instrument", dropna=False)

    common_idx = past_ret.index.intersection(barra.index)
    ret_aligned = past_ret.reindex(common_idx)
    barra_aligned = barra.reindex(common_idx)

    dates = sorted(ret_aligned.index.get_level_values("datetime").unique())
    symbols = sorted(ret_aligned.index.get_level_values("instrument").unique())

    style_arr = np.zeros((len(dates), len(symbols), len(STYLE_NAMES)))
    for k, name in enumerate(STYLE_NAMES):
        if name in barra_aligned.columns:
            s = barra_aligned[name].unstack("instrument").reindex(
                index=dates, columns=symbols)
            style_arr[:, :, k] = s.to_numpy()

    ret_arr = ret_aligned.unstack("instrument").reindex(
        index=dates, columns=symbols).to_numpy()
    valid = (~np.isnan(ret_arr)) & (~np.all(np.isnan(style_arr), axis=2))
    residuals = _cross_sectional_residual(
        ret_arr, style_arr, valid.astype(np.float64))
    residuals = np.where(valid, residuals, np.nan)

    res_w = pd.DataFrame(residuals, index=dates, columns=symbols)
    ema_short = res_w.ewm(span=5, adjust=False, min_periods=5).mean()
    ema_long = res_w.ewm(span=20, adjust=False, min_periods=10).mean()
    factor_w = ema_short - ema_long

    out = factor_w.stack(dropna=False)
    out.index.names = ["datetime", "instrument"]
    out.name = "value"
    return out
