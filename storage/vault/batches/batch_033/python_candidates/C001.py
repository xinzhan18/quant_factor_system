"""
C001 — C003_b8 corr-ratio signal stripped of vol_20d only.

Signal-level orthogonalization for amount_volatility_signal T005.
Take the reserve candidate `Corr(amount, volume, 20) / Corr(amount, volume, 60)`
and regress out only the cross-sectional vol_20d style each day.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.linalg import pinv

REQUIRED_FIELDS = ["$amount", "$volume"]
VECTORIZED = True

STYLE_NAMES = ["vol_20d"]
BARRA_CACHE = "storage/cache/barra_factors.parquet"
SHORT = 20
LONG = 60
EPS = 1e-8


def _rolling_corr(lhs: pd.DataFrame, rhs: pd.DataFrame, window: int) -> pd.DataFrame:
    mean_l = lhs.rolling(window, min_periods=window).mean()
    mean_r = rhs.rolling(window, min_periods=window).mean()
    cov = (lhs * rhs).rolling(window, min_periods=window).mean() - mean_l * mean_r
    var_l = (lhs * lhs).rolling(window, min_periods=window).mean() - mean_l * mean_l
    var_r = (rhs * rhs).rolling(window, min_periods=window).mean() - mean_r * mean_r
    denom = np.sqrt(var_l.clip(lower=0.0) * var_r.clip(lower=0.0))
    return cov / denom.where(denom > EPS)


def _cs_residual(signal_arr: np.ndarray, styles: np.ndarray, valid: np.ndarray) -> np.ndarray:
    n_dates, n_symbols, _ = styles.shape
    x = np.concatenate([styles, np.ones((n_dates, n_symbols, 1))], axis=2)
    x = np.nan_to_num(x, nan=0.0) * valid[..., None]
    y = np.nan_to_num(signal_arr, nan=0.0) * valid

    xtx = np.einsum("pdi,pdj->pij", x, x)
    xty = np.einsum("pdi,pd->pi", x, y)

    n_features = x.shape[2]
    xtx_inv = np.zeros((n_dates, n_features, n_features))
    for p in range(n_dates):
        xtx_inv[p] = pinv(xtx[p], rcond=1e-15)

    beta = np.einsum("pij,pj->pi", xtx_inv, xty)
    return y - np.einsum("pdi,pi->pd", x, beta)


def compute(df: pd.DataFrame) -> pd.Series:
    barra = pd.read_parquet(BARRA_CACHE)

    amount = df["$amount"].unstack("instrument")
    volume = df["$volume"].unstack("instrument")

    corr_short = _rolling_corr(amount, volume, SHORT)
    corr_long = _rolling_corr(amount, volume, LONG)
    signal_wide = corr_short / corr_long.where(corr_long.abs() > EPS)
    signal_flat = signal_wide.stack(dropna=False)
    signal_flat.name = "signal"

    common_idx = signal_flat.index.intersection(barra.index)
    signal_aligned = signal_flat.reindex(common_idx)
    barra_aligned = barra.reindex(common_idx)

    dates = signal_aligned.index.get_level_values("datetime").unique()
    symbols = signal_aligned.index.get_level_values("instrument").unique()

    signal_arr = signal_aligned.unstack("instrument").reindex(index=dates, columns=symbols).to_numpy()
    style_vals = np.zeros((len(dates), len(symbols), len(STYLE_NAMES)), dtype=np.float64)

    for k, style_name in enumerate(STYLE_NAMES):
        style_wide = barra_aligned[style_name].unstack("instrument").reindex(index=dates, columns=symbols)
        style_vals[:, :, k] = style_wide.to_numpy()

    valid_signal = np.isfinite(signal_arr)
    valid_style = ~np.all(np.isnan(style_vals), axis=2)
    valid = valid_signal & valid_style

    residuals = _cs_residual(signal_arr, style_vals, valid.astype(np.float64))
    residuals = np.where(valid, residuals, np.nan)

    result = pd.Series(
        residuals.ravel(),
        index=pd.MultiIndex.from_product([dates, symbols], names=["datetime", "instrument"]),
    )
    return result.reindex(signal_flat.index)
