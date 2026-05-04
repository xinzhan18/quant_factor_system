"""C006 — Low-IVOL gated cumulative idiosyncratic momentum, 60d (T004).

`Sum(ε, 60) * 1[RealizedVol(ret, 60) < cross_section_median]` — masks the
cumulative residual signal to the low-volatility half of the cross-section
each date, zeroing the high-vol half.

T004 question: Barra residualization removes linear vol_20d exposure, but
N-day cumulative may re-accumulate path-dependent vol exposure (P004 律
warning). If gating to low-vol stocks improves alpha_surv / dom_style ≠
vol_20d, this confirms path memory leaks vol back. If dom_style still =
vol_20d, the gating itself becomes a (negative) vol_20d signal — important
lesson either way.

Note: gating zero-out is not rate-form (level × indicator), should not
trigger F300.
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
WINDOW = 60


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
    raw_w = pd.DataFrame(ret_arr, index=dates, columns=symbols)

    cum_res = res_w.rolling(WINDOW, min_periods=int(WINDOW * 0.6)).sum()
    realized_vol = raw_w.rolling(WINDOW, min_periods=int(WINDOW * 0.6)).std()

    # Cross-sectional median per date (NaN-aware)
    median_vol = realized_vol.median(axis=1)
    # Broadcast: True where below median (low-vol regime)
    low_vol_mask = realized_vol.lt(median_vol, axis=0)
    # Multiply: cum_res survives only in low-vol regime; high-vol → 0
    factor_w = cum_res.where(low_vol_mask, 0.0)

    out = factor_w.stack(dropna=False)
    out.index.names = ["datetime", "instrument"]
    out.name = "value"
    return out
