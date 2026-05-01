"""
C003 — Gross Profit Margin TTM residualize on (log_market_cap, vol_20d) → CsRank

Rationale: gross_profit_margin 比 ROE 更稳，less leverage-dependent，
反映"产品定价 / 成本控制"基本面，跨行业 cross-section 上有更多噪音但
在 csi1000 上更难被 capital structure regime 扰动。
窄 basis (size, vol_20d) 测试 gross margin 残差是否携带独立 alpha。
"""

from __future__ import annotations
import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.linalg import pinv

REQUIRED_FIELDS = ["$close"]
VECTORIZED = True

BARRA_CACHE = "storage/cache/barra_factors.parquet"
TTM_CACHE = "storage/cache/ttm_fundamentals.parquet"
QUALITY_FIELD = "gross_margin_ttm"
STYLE_NAMES = ["log_circ_cap", "vol_20d"]


def _cs_residual_rank(quality_arr: NDArray, styles: NDArray, valid: NDArray) -> NDArray:
    n_dates, n_symbols, _ = styles.shape
    X = np.concatenate([styles, np.ones((n_dates, n_symbols, 1))], axis=2)
    X = np.nan_to_num(X, nan=0.0) * valid[..., None]
    y = np.nan_to_num(quality_arr, nan=0.0) * valid
    XtX = np.einsum("pdi,pdj->pij", X, X)
    Xty = np.einsum("pdi,pd->pi", X, y)
    beta = np.zeros((n_dates, X.shape[2]))
    for p in range(n_dates):
        beta[p] = pinv(XtX[p], rcond=1e-15) @ Xty[p]
    resid = y - np.einsum("pdi,pi->pd", X, beta)
    out = np.full_like(resid, np.nan, dtype=np.float64)
    for p in range(n_dates):
        v = valid[p].astype(bool)
        if v.sum() < 5:
            continue
        x = resid[p][v]
        order = np.argsort(np.argsort(x))
        n = len(x)
        out[p, v] = order / (n - 1) - 0.5
    return out


def compute(df: pd.DataFrame) -> pd.Series:
    barra: pd.DataFrame = pd.read_parquet(BARRA_CACHE)
    ttm: pd.DataFrame = pd.read_parquet(TTM_CACHE)
    quality = ttm[QUALITY_FIELD]

    target_idx = df.index
    common_idx = target_idx.intersection(barra.index).intersection(quality.dropna().index)
    quality_aligned = quality.reindex(common_idx)
    barra_aligned = barra.reindex(common_idx)

    dates_ordered = pd.Index(sorted(quality_aligned.index.get_level_values("datetime").unique()))
    symbols = quality_aligned.index.get_level_values("instrument").unique()
    n_dates = len(dates_ordered)
    n_symbols = len(symbols)

    style_vals = np.zeros((n_dates, n_symbols, len(STYLE_NAMES)), dtype=np.float64)
    for k, sn in enumerate(STYLE_NAMES):
        s = barra_aligned[sn].unstack("instrument")
        style_vals[:, :, k] = s.reindex(index=dates_ordered, columns=symbols).to_numpy()

    quality_arr = quality_aligned.unstack("instrument").reindex(
        index=dates_ordered, columns=symbols
    ).values

    valid = (~np.isnan(quality_arr)) & (~np.any(np.isnan(style_vals), axis=2))
    ranked = _cs_residual_rank(quality_arr, style_vals, valid.astype(np.float64))

    out = pd.Series(
        ranked.ravel(),
        index=pd.MultiIndex.from_product([dates_ordered, symbols], names=["datetime", "instrument"]),
    )
    return out.reindex(target_idx)
