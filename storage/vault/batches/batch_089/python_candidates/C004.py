"""C004 — Vol-normalized cumulative idiosyncratic momentum, 120d (T002).

Strict paper definition: `Sum(ε, N) / Std(ε, N)` — cumulative residual
divided by its own time-series volatility over the same window. The
ratio is unit-less and removes per-stock idiosyncratic vol heterogeneity
that could otherwise inject vol_20d-related cross-section ranking noise.

vs C002 raw Sum: tests whether vol-normalization is the structural piece
the paper relied on (paper IR=2.04 implicitly assumes risk-adjusted form).

Note on F300 rate-form: numerator (Sum) and denominator (Std) are both
derived from the same residual series — this is a magnitude-standardization
ratio (scalar / scalar), not a rate-of-change form. Should not trip F300
rate-form default-skip rule.
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
WINDOW = 120


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
        XtX_inv[p] = pinv(XtX[p], rtol=1e-15)
    beta = np.einsum("pij,pj->pi", XtX_inv, Xty)
    residual = y - np.einsum("pdi,pi->pd", X, beta)
    return residual


def compute(df: pd.DataFrame) -> pd.Series:
    barra = pd.read_parquet(BARRA_CACHE)

    close_w = df["$close"].unstack("instrument").sort_index()
    past_ret_w = close_w.pct_change(1)
    past_ret = past_ret_w.stack("instrument", dropna=False)
    past_ret.name = "ret"

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
    valid_ret = ~np.isnan(ret_arr)
    valid_sty = ~np.all(np.isnan(style_arr), axis=2)
    valid = valid_ret & valid_sty

    residuals = _cross_sectional_residual(
        ret_arr, style_arr, valid.astype(np.float64))
    residuals = np.where(valid, residuals, np.nan)

    res_w = pd.DataFrame(residuals, index=dates, columns=symbols)
    cum = res_w.rolling(WINDOW, min_periods=int(WINDOW * 0.6)).sum()
    vol = res_w.rolling(WINDOW, min_periods=int(WINDOW * 0.6)).std()
    # Avoid division by zero / very small vol → mask to NaN
    vol = vol.where(vol > 1e-8)
    risk_adj = cum / vol

    out = risk_adj.stack(dropna=False)
    out.index.names = ["datetime", "instrument"]
    out.name = "value"
    return out
