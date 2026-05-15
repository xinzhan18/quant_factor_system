"""
C001 — Python residualize on (F008, F026) for b076/C005 atom

Revival path from calibration finding/013 (round 91):
  Raw atom: TsRank((h+l)/2 / close, 60)
  b076/C005 实测 alpha_surv=1.43 / ls_t=+4.84 / mono=+0.90 / incr_ic=+0.0418 (4 项 CP top)
  但 max_corr=0.449@F008 cluster 阻断 admit.

This candidate runs single-step cross-section OLS:
    raw_atom_t = β0 + β1 * F008_t + β2 * F026_t + residual_t
取 residual_t 作为 factor value, expected max_corr@F008/F026 < 0.30 after orthogonalization.

F008 = Mean(Div(Sub($high, $close), Sub($high, $low)), 3)  -- upper_shadow_persistence_3d
F026 = TsRank(Div(Sub($close, $low), Sub($high, $low)), 60) -- daily_close_position_tsrank_60

R5 vectorization: 3D tensor (date × symbol × feature) einsum + pinv, no per-date loop.
P004-deep self-check ✓: 不是 N-day path-integral (TsRank inner 是 single-step rank-of-current).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from numpy.typing import NDArray
from scipy.linalg import pinv

REQUIRED_FIELDS = ["$high", "$low", "$close"]
VECTORIZED = True

EPS = 1e-9
WINDOW_60 = 60
WINDOW_3 = 3


def _ts_rank(arr: NDArray[np.float64], window: int) -> NDArray[np.float64]:
    """TsRank along axis 0 (time): rank-of-current-value-in-trailing-window.

    Returns NaN for first `window-1` rows. Rank is normalized to [0, 1].
    Vectorized via stride_tricks on rolling windows.
    """
    n_t, n_s = arr.shape
    out = np.full_like(arr, np.nan, dtype=np.float64)
    if n_t < window:
        return out
    # Build rolling-window view: shape (n_t-window+1, window, n_s)
    from numpy.lib.stride_tricks import sliding_window_view

    win_view = sliding_window_view(arr, window_shape=window, axis=0)
    # win_view shape: (n_t-window+1, n_s, window)  (axis ordering)
    # We want shape (n_t-window+1, window, n_s) -> transpose
    win_view = np.transpose(win_view, (0, 2, 1))
    current = win_view[:, -1:, :]  # last value in each window, shape (n_t-w+1, 1, n_s)
    # rank: count how many values in window <= current, normalized to [0,1]
    less_eq = (win_view <= current).sum(axis=1).astype(np.float64)  # (n_t-w+1, n_s)
    # Normalize: rank in [1/window, 1]
    out[window - 1 :, :] = less_eq / float(window)
    # Propagate NaNs: if any NaN in window, result is NaN
    has_nan = np.isnan(win_view).any(axis=1)  # (n_t-w+1, n_s)
    out[window - 1 :, :] = np.where(has_nan, np.nan, out[window - 1 :, :])
    return out


def _rolling_mean(arr: NDArray[np.float64], window: int) -> NDArray[np.float64]:
    """Rolling mean along axis 0 with NaN handling. Window-1 leading NaNs."""
    n_t, n_s = arr.shape
    out = np.full_like(arr, np.nan, dtype=np.float64)
    if n_t < window:
        return out
    from numpy.lib.stride_tricks import sliding_window_view

    win_view = sliding_window_view(arr, window_shape=window, axis=0)
    win_view = np.transpose(win_view, (0, 2, 1))
    # If any NaN in window -> NaN; else mean
    has_nan = np.isnan(win_view).any(axis=1)
    mean_vals = win_view.mean(axis=1)
    out[window - 1 :, :] = np.where(has_nan, np.nan, mean_vals)
    return out


def _cross_sectional_residual(
    y: NDArray[np.float64],
    X_features: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Single-step cross-section OLS residual per date.

    y:           (n_dates, n_symbols)
    X_features:  (n_dates, n_symbols, n_features)  -- features WITHOUT intercept

    Returns residual (n_dates, n_symbols) where valid; NaN elsewhere.
    """
    n_dates, n_symbols, n_features = X_features.shape
    # Append intercept
    intercept = np.ones((n_dates, n_symbols, 1), dtype=np.float64)
    X = np.concatenate([X_features, intercept], axis=2)  # (n_d, n_s, n_f+1)

    # Validity mask: row in regression iff y and all features finite
    valid = np.isfinite(y) & np.all(np.isfinite(X), axis=2)  # (n_d, n_s)

    # Zero-out invalid rows so they don't contribute to XtX/Xty
    X_masked = np.where(valid[..., None], X, 0.0)
    y_masked = np.where(valid, y, 0.0)

    XtX = np.einsum("dsi,dsj->dij", X_masked, X_masked)  # (n_d, n_f+1, n_f+1)
    Xty = np.einsum("dsi,ds->di", X_masked, y_masked)  # (n_d, n_f+1)

    # Per-date pinv: vectorize via numpy.linalg.pinv (broadcasts over leading dims)
    XtX_inv = np.linalg.pinv(XtX, rcond=1e-12)  # (n_d, n_f+1, n_f+1)

    beta = np.einsum("dij,dj->di", XtX_inv, Xty)  # (n_d, n_f+1)
    y_hat = np.einsum("dsi,di->ds", X, beta)  # (n_d, n_s)
    residual = y - y_hat

    # Mask invalid back to NaN
    residual = np.where(valid, residual, np.nan)
    return residual


def compute(df: pd.DataFrame) -> pd.Series:
    """Compute residualized TsRank((h+l)/2 / close, 60) on (F008, F026).

    Input df: MultiIndex (datetime, instrument) with columns $high, $low, $close.
    Output: Series with same MultiIndex, residual factor values.
    """
    # Unstack to (date, symbol) 2D arrays
    high = df["$high"].unstack("instrument")
    low = df["$low"].unstack("instrument")
    close = df["$close"].unstack("instrument")

    # Ensure same column order
    cols = close.columns
    high = high.reindex(columns=cols)
    low = low.reindex(columns=cols)

    dates = close.index
    n_d, n_s = close.shape

    h = high.to_numpy(dtype=np.float64)
    l = low.to_numpy(dtype=np.float64)
    c = close.to_numpy(dtype=np.float64)

    # ----- Raw atom: TsRank((h+l)/2 / close, 60) -----
    mid = 0.5 * (h + l)
    raw_ratio = mid / (c + EPS)
    raw_atom = _ts_rank(raw_ratio, WINDOW_60)  # (n_d, n_s)

    # ----- F008: Mean((H-C)/(H-L), 3) -----
    hml = h - l
    hmc = h - c
    f008_inner = hmc / (hml + EPS)
    f008 = _rolling_mean(f008_inner, WINDOW_3)

    # ----- F026: TsRank((C-L)/(H-L), 60) -----
    cml = c - l
    f026_inner = cml / (hml + EPS)
    f026 = _ts_rank(f026_inner, WINDOW_60)

    # Stack features for residualize
    features = np.stack([f008, f026], axis=2)  # (n_d, n_s, 2)

    residual = _cross_sectional_residual(raw_atom, features)

    # Pack back to MultiIndex Series with same shape as input
    result_df = pd.DataFrame(residual, index=dates, columns=cols)
    result = result_df.stack(dropna=False)
    result.index.names = ["datetime", "instrument"]
    # Reindex to input order
    result = result.reindex(df.index)
    return result
