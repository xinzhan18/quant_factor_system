"""C001 — Cumulative idiosyncratic momentum, 60d window (T001 short).

Path-integral cumulative residual return: `Sum(ε_t, t in [t-N+1, t])` where ε is
the cross-sectional Barra residual of past 1-day returns regressed on the 7
Barra style factors at each date.

Design rationale (vs F004):
- F004 = single-day residual (point estimate); this = N-day cumulative residual
  rank (path integral). Single-day rank ≠ N-day cumulative rank in cross-section.
- Mechanism: small positive idiosyncratic alphas accumulate persistently across
  many days, while raw return momentum is killed by vol/turnover absorption
  (return_momentum_acceleration / asymmetric_momentum / fundamental_momentum
  all dead). Residualization strips that absorption path.
- Strict t-N..t-1 window — no shift(-k), no t-period info. Past-return based.

Expected sign: positive (winners persist in residual space).
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

    # Past 1-day return at date t = (close_t - close_{t-1}) / close_{t-1}.
    # Known at time t — no forward leak.
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
    cum_res = res_w.rolling(WINDOW, min_periods=int(WINDOW * 0.6)).sum()

    out = cum_res.stack(dropna=False)
    out.index.names = ["datetime", "instrument"]
    out.name = "value"
    return out
