"""
C006 — Inverse Debt-to-Asset Ratio TTM residualize on (log_market_cap, vol_20d, book_to_price) → CsRank

Rationale (replace op_margin which has zero coverage in current data):
低 debt_to_asset = 高财务安全 = "balance-sheet quality"。
取 -debt_to_asset 让 high quality = high signal value，与 ROE/ROA 方向一致。
3 basis 全控（size + vol_20d + book_to_price） — 与 C003 narrow basis 形成对照
"book_to_price 加入是否过切"。该字段是"solvency quality"维度，与 ROE/ROA 的
"earnings quality"维度几何独立，扩展 quality numerator 类型覆盖。
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
QUALITY_FIELD = "debt_to_asset_ttm"
STYLE_NAMES = ["log_circ_cap", "vol_20d", "book_to_price"]


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
    # Negate so higher signal = lower debt = better quality (sign-align with ROE/ROA family)
    quality = -ttm[QUALITY_FIELD]

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
