"""
C006 — Barra Residual × Sign(Δvolume_5) Interaction

Multiply Barra residual (full 7-style strip) by the sign of recent 5d volume
change. Hypothesis: idiosyncratic alpha is stronger when accompanied by rising
volume confirmation; sign-modulation reduces effective signal during low-volume
"random walks" and amplifies during attention-driven moves.
New mechanism beyond pure residualization.
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
VOL_LOOKBACK = 5


def _cs_residual(returns: NDArray[np.float64], styles: NDArray[np.float64], valid: NDArray[np.float64]) -> NDArray[np.float64]:
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


def compute(df: pd.DataFrame) -> pd.Series:
    barra: pd.DataFrame = pd.read_parquet(BARRA_CACHE)

    ret = df["$close"].unstack("instrument")
    forward_ret = ret.shift(-1).stack("instrument")
    forward_ret.name = "returns_fwd"

    # Volume change sign over last 5d (use $volume to determine recent direction)
    vol = df["$volume"].unstack("instrument")
    vol_change = vol - vol.shift(VOL_LOOKBACK)
    vol_sign = np.sign(vol_change).stack("instrument")
    vol_sign.name = "vol_sign"

    common_idx = forward_ret.index.intersection(barra.index).intersection(vol_sign.index)
    fwd_aligned = forward_ret.reindex(common_idx)
    barra_aligned = barra.reindex(common_idx)
    vol_sign_aligned = vol_sign.reindex(common_idx)

    dates_ordered = fwd_aligned.index.get_level_values("datetime").unique()
    symbols = fwd_aligned.index.get_level_values("instrument").unique()
    n_dates = len(dates_ordered)
    n_symbols = len(symbols)

    style_vals = np.zeros((n_dates, n_symbols, len(STYLE_NAMES)), dtype=np.float64)
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

    residuals = _cs_residual(ret_arr, style_vals, valid.astype(np.float64))
    residuals = np.where(valid, residuals, np.nan)

    # Multiply residual by sign of volume change
    vol_sign_arr = vol_sign_aligned.unstack("instrument").reindex(
        index=dates_ordered, columns=symbols
    ).values
    signal = residuals * vol_sign_arr

    result = pd.Series(
        signal.ravel(),
        index=pd.MultiIndex.from_product(
            [dates_ordered, symbols], names=["datetime", "instrument"]
        ),
    ).reindex(forward_ret.index)

    return result
