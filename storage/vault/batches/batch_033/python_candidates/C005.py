"""
C005 — C002_b3 normalized amount slope stripped of vol_20d.

Take `Slope($amount / Mean($amount, 20), 20)` and remove the daily
cross-sectional vol_20d component.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.linalg import pinv

REQUIRED_FIELDS = ["$amount"]
VECTORIZED = True

STYLE_NAMES = ["vol_20d"]
BARRA_CACHE = "storage/cache/barra_factors.parquet"
WINDOW = 20
EPS = 1e-8


def _rolling_slope(signal_wide: pd.DataFrame, window: int) -> pd.DataFrame:
    arr = signal_wide.to_numpy(dtype=np.float64)
    n_dates, n_symbols = arr.shape
    out = np.full((n_dates, n_symbols), np.nan, dtype=np.float64)
    if n_dates < window:
        return pd.DataFrame(out, index=signal_wide.index, columns=signal_wide.columns)

    windows = np.lib.stride_tricks.sliding_window_view(arr, window_shape=window, axis=0)
    windows = np.transpose(windows, (0, 2, 1))

    x = np.arange(window, dtype=np.float64)
    x_centered = x - x.mean()
    denom = np.sum(x_centered * x_centered)

    valid = np.isfinite(windows).all(axis=1)
    filled = np.nan_to_num(windows, nan=0.0)
    slopes = np.einsum("tws,w->ts", filled, x_centered) / denom
    out[window - 1 :] = np.where(valid, slopes, np.nan)

    return pd.DataFrame(out, index=signal_wide.index, columns=signal_wide.columns)


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
    amount_mean = amount.rolling(WINDOW, min_periods=WINDOW).mean()
    normalized = amount / amount_mean.where(amount_mean.abs() > EPS)
    signal_wide = _rolling_slope(normalized, WINDOW)
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
