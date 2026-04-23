"""
C001 — residualize turnover-PE rank-diff by vol_20d + turnover_20d.

Base reserve: batch_009 C007 `Sub(CsRank($turnover_rate), CsRank($pe_ratio))`.
Goal: keep the strongest rank-order / PnL signal while stripping the two
most obvious Barra carriers from T001.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.linalg import pinv

REQUIRED_FIELDS = ["$close"]
VECTORIZED = True

STYLE_NAMES = ["vol_20d", "turnover_20d"]
BARRA_CACHE = "storage/cache/barra_factors.parquet"


def _cross_section_rank(frame: pd.DataFrame) -> pd.DataFrame:
    ranked = frame.rank(axis=1, method="average", pct=True)
    return ranked - 0.5


def _cs_residual(
    signal_arr: np.ndarray, styles: np.ndarray, valid: np.ndarray
) -> np.ndarray:
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


def _residualize(signal_flat: pd.Series) -> pd.Series:
    barra = pd.read_parquet(BARRA_CACHE)

    common_idx = signal_flat.index.intersection(barra.index)
    signal_aligned = signal_flat.reindex(common_idx)
    barra_aligned = barra.reindex(common_idx)

    dates = signal_aligned.index.get_level_values("datetime").unique()
    symbols = signal_aligned.index.get_level_values("instrument").unique()

    signal_arr = (
        signal_aligned.unstack("instrument")
        .reindex(index=dates, columns=symbols)
        .to_numpy()
    )
    style_vals = np.zeros(
        (len(dates), len(symbols), len(STYLE_NAMES)), dtype=np.float64
    )
    for k, style_name in enumerate(STYLE_NAMES):
        style_wide = (
            barra_aligned[style_name]
            .unstack("instrument")
            .reindex(index=dates, columns=symbols)
        )
        style_vals[:, :, k] = style_wide.to_numpy()

    valid_signal = np.isfinite(signal_arr)
    valid_style = ~np.all(np.isnan(style_vals), axis=2)
    valid = valid_signal & valid_style

    residuals = _cs_residual(signal_arr, style_vals, valid.astype(np.float64))
    residuals = np.where(valid, residuals, np.nan)

    result = pd.Series(
        residuals.ravel(),
        index=pd.MultiIndex.from_product(
            [dates, symbols], names=["datetime", "instrument"]
        ),
    )
    return result.reindex(signal_flat.index)


def compute(df: pd.DataFrame) -> pd.Series:
    barra = pd.read_parquet(BARRA_CACHE).reindex(df.index)
    turnover = barra["turnover_20d"].unstack("instrument")
    ep = barra["ep_ratio"].unstack("instrument")

    signal_wide = _cross_section_rank(turnover) + _cross_section_rank(ep)
    signal_flat = signal_wide.stack(dropna=False)
    signal_flat.name = "signal"
    return _residualize(signal_flat)
