"""
C005 — Size-Neutral Barra Residual

Compute Barra residual within each market-cap quintile.
Strips size effect within groups before computing Barra residual,
isolating pure style-driven alpha from size confounds.
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


def _cross_sectional_residual_2d(
    returns_2d: NDArray[np.float64],
    styles_2d: NDArray[np.float64],
    valid_2d: NDArray[np.bool_],
) -> NDArray[np.float64]:
    """Cross-sectional residual for 2D (date x symbol) arrays."""
    n_dates, n_symbols = returns_2d.shape
    n_styles = styles_2d.shape[1] if styles_2d.ndim > 1 else 1

    residuals = np.zeros_like(returns_2d)
    for p in range(n_dates):
        valid = valid_2d[p]
        if not np.any(valid):
            residuals[p] = np.nan
            continue

        y = returns_2d[p, valid]
        X = styles_2d[p, valid]
        if X.shape[0] < X.shape[1] + 1:
            residuals[p] = np.nan
            continue

        X = np.concatenate([X, np.ones((X.shape[0], 1))], axis=1)
        X = np.nan_to_num(X, nan=0.0)
        y = np.nan_to_num(y, nan=0.0)

        try:
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            residual = y - X @ beta
            residuals[p, valid] = residual
        except Exception:
            residuals[p] = np.nan

    return residuals


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

    # Get log_circ_cap for size ranking (index 0)
    size_vals = style_vals[:, :, 0]  # log_circ_cap

    # Compute residuals within size quintiles
    residuals = np.zeros((n_dates, n_symbols))
    for p in range(n_dates):
        valid_mask = valid[p]
        if not np.any(valid_mask):
            residuals[p] = np.nan
            continue

        # Get size ranks for this date
        size_p = size_vals[p]
        valid_size = ~np.isnan(size_p) & valid_mask

        if np.sum(valid_size) < 10:
            residuals[p] = np.nan
            continue

        # Assign to quintiles
        size_valid = size_p[valid_size]
        try:
            quintile_labels = pd.qcut(size_valid, q=5, labels=False, duplicates="drop")
        except Exception:
            residuals[p] = np.nan
            continue

        # For each quintile, compute residual
        ret_p = ret_arr[p]
        style_p = style_vals[p]

        for q in range(5):
            q_mask = valid_size & (quintile_labels == q)
            if not np.any(q_mask):
                continue

            y = ret_p[q_mask]
            X = style_p[q_mask]
            X = np.concatenate([X, np.ones((X.shape[0], 1))], axis=1)
            X = np.nan_to_num(X, nan=0.0)
            y = np.nan_to_num(y, nan=0.0)

            try:
                beta = np.linalg.lstsq(X, y, rcond=None)[0]
                residual = y - X @ beta
                residuals[p, q_mask] = residual
            except Exception:
                continue

    residuals = np.where(valid, residuals, np.nan)

    result = pd.Series(
        residuals.ravel(),
        index=pd.MultiIndex.from_product(
            [dates_ordered, symbols], names=["datetime", "instrument"]
        ),
    ).reindex(forward_ret.index)

    return result
