"""C002 — Residual return Std vs amount rank-diff.

Higher-moment of past residual return (residual return Std over 20d) ranked
against rank of long-window amount mean. Signed body-position higher-moment
LHS in residual domain.

LHS: CsRank(Std(residual_ret, 20))  — second moment of idiosyncratic returns
RHS: CsRank(Mean($amount, 60))       — long-window amount basis (avoids F018 amount_20)

Avoids F004 (residual itself, not its dispersion), F018 (amount_20 not amount_60).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.linalg import pinv

REQUIRED_FIELDS = ["$close", "$amount"]
VECTORIZED = True

STYLE_NAMES = [
    "log_circ_cap", "book_to_price", "mom_12_1", "str_1m",
    "vol_20d", "turnover_20d", "ep_ratio",
]
BARRA_CACHE = "storage/cache/barra_factors.parquet"
LHS_WINDOW = 20
RHS_WINDOW = 60


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


def _csrank(df_wide):
    return df_wide.rank(axis=1, pct=True)


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
    res_std = res_w.rolling(LHS_WINDOW, min_periods=LHS_WINDOW // 2).std()

    amt_w = df["$amount"].unstack("instrument").sort_index().reindex(
        index=dates, columns=symbols)
    amt_mean = amt_w.rolling(RHS_WINDOW, min_periods=RHS_WINDOW // 2).mean()

    factor_w = _csrank(res_std) - _csrank(amt_mean)
    out = factor_w.stack(dropna=True)  # Drop NaN to keep coverage high (mirrors F004)
    out.index.names = ["datetime", "instrument"]
    out.name = "value"
    return out
