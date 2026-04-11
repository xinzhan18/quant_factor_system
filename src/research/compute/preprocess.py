"""Vectorized cross-sectional preprocessing.

Two-step pipeline:

1. **Winsorize by MAD** (k=5, scale=1.4826) — clip to ``median ± k·1.4826·MAD``
   per date.
2. **Cross-sectional z-score** — ``(x - row_mean) / row_std`` per date.

Both steps are matrix operations on a ``(n_dates × n_symbols)`` wide frame,
not ``groupby.transform`` (which is an implicit per-date for-loop — see
refactor_plan §6 and R5 "全程向量化"). The old
``src/research/compute/preprocess.py`` used groupby.transform and was 2×
slower on 2000×5000 panels.

Neutralization is intentionally absent — per ``config.yaml``
``preprocess.neutralize: false``, CP04 Risk Cleanness performs Barra
residual IC after the fact instead.

Input/output
------------
Both ``winsorize_mad`` and ``zscore_cross_section`` take a
``pd.Series`` with a MultiIndex ``(time, symbol)``. Missing values stay
missing; the optional ``tradable_mask`` argument to
``preprocess_factor`` is an additional bool mask that is applied before
winsorization.

Parameters live in ``config.yaml`` and are passed in explicitly — no
module-level defaults so tests are deterministic.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PreprocessConfig:
    """Config bundle passed to :func:`preprocess_factor`."""

    winsorize_mad_k: float = 5.0
    winsorize_mad_scale: float = 1.4826  # normal-distribution MAD → std
    zscore: bool = True


def _to_wide(series: pd.Series) -> pd.DataFrame:
    """Pivot a ``(time, symbol)``-indexed Series to a ``time × symbol`` frame."""
    if not isinstance(series.index, pd.MultiIndex):
        raise ValueError(
            "preprocess: expected MultiIndex(time, symbol) Series, "
            f"got index type {type(series.index).__name__}"
        )
    wide = series.unstack(level=-1)
    return wide


def _from_wide(wide: pd.DataFrame, name: str = "value") -> pd.Series:
    """Convert a wide frame back to a MultiIndex Series, preserving NaNs."""
    # future_stack=True is the pandas 2.1+ behavior and keeps NaN rows.
    s = wide.stack(future_stack=True)
    s.name = name
    return s


def winsorize_mad(
    wide: pd.DataFrame,
    k: float,
    scale: float,
) -> pd.DataFrame:
    """Clip values to ``row_median ± k·scale·MAD`` per row.

    ``wide`` is ``(n_dates × n_symbols)``. ``k·scale`` is the number of
    "std-equivalent" deviations — e.g. ``k=5, scale=1.4826`` clips at
    ~7.4 raw-MAD units, or equivalently ~5 standard deviations under
    normality.

    Pure matrix operations — no for-loop, no groupby.
    """
    row_median = wide.median(axis=1, skipna=True)
    abs_dev = wide.sub(row_median, axis=0).abs()
    mad = abs_dev.median(axis=1, skipna=True)

    half_width = (k * scale) * mad
    lower = row_median - half_width
    upper = row_median + half_width

    clipped = wide.clip(lower=lower, upper=upper, axis=0)
    return clipped


def zscore_cross_section(wide: pd.DataFrame) -> pd.DataFrame:
    """Cross-sectional z-score per row (date).

    Uses ``ddof=0`` (population std) to match the refactor_plan §6
    reference implementation. Rows with zero or undefined std (e.g. all
    NaN or all constant) collapse to ``0.0`` where a value existed,
    ``NaN`` otherwise.
    """
    row_mean = wide.mean(axis=1, skipna=True)
    row_std = wide.std(axis=1, skipna=True, ddof=0)

    # Protect against zero / NaN std: safe_std replaces 0 with NaN so the
    # division yields NaN, then we fill back to 0.0 where the original
    # value was present.
    safe_std = row_std.where(row_std > 0)
    centered = wide.sub(row_mean, axis=0)
    out = centered.div(safe_std, axis=0)

    # Any row where std was 0 gets filled with 0 for originally-valid cells
    original_valid = wide.notna()
    zero_std_rows = row_std.fillna(0).eq(0)
    if zero_std_rows.any():
        fill_mask = original_valid.loc[zero_std_rows[zero_std_rows].index]
        out.loc[zero_std_rows[zero_std_rows].index] = out.loc[
            zero_std_rows[zero_std_rows].index
        ].mask(fill_mask, 0.0)
    return out


def preprocess_factor(
    factor: pd.Series,
    config: PreprocessConfig,
    tradable_mask: pd.Series | None = None,
) -> pd.Series:
    """Apply the full tradable-mask → winsorize → z-score pipeline.

    Parameters
    ----------
    factor
        MultiIndex (time, symbol) Series of raw factor values.
    config
        :class:`PreprocessConfig` with winsorize params and zscore flag.
    tradable_mask
        Optional MultiIndex (time, symbol) bool Series. Cells where the
        mask is False (or missing) become NaN before preprocessing.

    Returns
    -------
    pd.Series
        MultiIndex (time, symbol) preprocessed values. Shape and index
        are preserved (NaNs where input was NaN or masked out).
    """
    masked = factor
    if tradable_mask is not None:
        # Align indices, missing mask entries default to "not tradable"
        aligned = tradable_mask.reindex(factor.index, fill_value=False)
        masked = factor.where(aligned.astype(bool), np.nan)

    wide = _to_wide(masked)

    wide = winsorize_mad(
        wide,
        k=config.winsorize_mad_k,
        scale=config.winsorize_mad_scale,
    )

    if config.zscore:
        wide = zscore_cross_section(wide)

    out = _from_wide(wide, name=factor.name or "value")
    # Reindex back to the original index shape (idempotent if no holes)
    return out.reindex(factor.index)
