"""C001 — Residual return persistence (rank-diff geometry).

Test rank-diff paradigm in residual domain (test T014).

LHS: CsRank of past 20-day mean of |residual return| (residual dispersion level).
RHS: CsRank of past 20-day mean of $turnover_rate (raw liquidity level).
Factor = LHS - RHS, then signed by direction expectation (high residual + low
turnover = idiosyncratic illiquid = positive expected alpha).

Avoids:
- F004 (which is the residual itself — corr should be <0.30 since this is dispersion of past, not future residual)
- F012/F018/F020 anchor cluster (RHS=turnover_rate not amount/Amihud)
- Forward-looking shift(-k) — uses past residual based on past returns
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.linalg import pinv

REQUIRED_FIELDS = ["$close", "$turnover_rate"]
VECTORIZED = True

STYLE_NAMES = [
    "log_circ_cap", "book_to_price", "mom_12_1", "str_1m",
    "vol_20d", "turnover_20d", "ep_ratio",
]
BARRA_CACHE = "storage/cache/barra_factors.parquet"
WINDOW = 20


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
    residual = y - np.einsum("pdi,pi->pd", X, beta)
    return residual


def _csrank(df_wide):
    """Per-row (date) cross-sectional rank in [0,1], NaN preserved."""
    return df_wide.rank(axis=1, pct=True)


def compute(df: pd.DataFrame) -> pd.Series:
    barra = pd.read_parquet(BARRA_CACHE)

    # Past return = (close_t / close_{t-1}) - 1 — known at time t.
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
    abs_res_mean = res_w.abs().rolling(WINDOW, min_periods=WINDOW // 2).mean()

    turn_w = df["$turnover_rate"].unstack("instrument").sort_index()
    turn_w = turn_w.reindex(index=dates, columns=symbols)
    turn_mean = turn_w.rolling(WINDOW, min_periods=WINDOW // 2).mean()

    lhs_rank = _csrank(abs_res_mean)
    rhs_rank = _csrank(turn_mean)
    factor_w = lhs_rank - rhs_rank

    out = factor_w.stack(dropna=False)
    out.index.names = ["datetime", "instrument"]
    out.name = "value"
    return out
