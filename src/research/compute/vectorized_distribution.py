"""Vectorized factor-distribution statistics.

Produces the ``distribution`` block of ``result.yaml`` — cross-sectional
skew / kurtosis / zero-ratio / extreme-value ratio for one candidate.

Coverage is **not** computed here: it's a top-level ``result.yaml`` field
(also read directly by Phase 3 hard gates) and is derived from the
preprocessed factor series in the orchestrator. Keeping coverage out of
this module avoids duplicating the same computation.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from core.factor_stats import distribution_stats, multiindex_to_flat


def compute_distribution(
    factor: pd.Series | pd.DataFrame,
    *,
    extreme_z_threshold: float = 3.0,
) -> dict[str, Any]:
    """Factor distribution statistics (per-candidate, single pass).

    Parameters
    ----------
    factor
        Either a ``(time, symbol)`` MultiIndex Series or a single-column
        DataFrame of (raw or preprocessed) factor values.
    extreme_z_threshold
        Absolute z-score above which a value counts as an outlier. The
        z is computed against the non-NaN sample's mean / std — not
        per-date, so this is a pooled metric.

    Returns
    -------
    dict
        ``{"zero_ratio", "skew", "kurt", "extreme_ratio"}`` — all
        ``float | None``.
    """
    if factor is None:
        return _empty()

    # Normalize to Series
    if isinstance(factor, pd.DataFrame):
        if factor.shape[1] == 0:
            return _empty()
        series = factor.iloc[:, 0]
    else:
        series = factor

    if series.empty:
        return _empty()

    total = len(series)
    non_nan = series.dropna()
    if len(non_nan) < 10:
        return _empty()

    # Skew / kurt via core.factor_stats (reuses MultiIndex-agnostic math)
    frame = (
        factor
        if isinstance(factor, pd.DataFrame)
        else series.to_frame(name=series.name or "value")
    )
    frame.index.names = ["datetime", "instrument"]
    flat = multiindex_to_flat(frame)
    dstats = distribution_stats(flat)

    zero_ratio = float((non_nan == 0).sum() / total)

    extreme_ratio: float | None
    std = float(non_nan.std())
    if std > 0:
        z = ((non_nan - non_nan.mean()) / std).abs()
        extreme_ratio = round(
            float((z > extreme_z_threshold).sum() / len(non_nan)), 6
        )
    else:
        extreme_ratio = 0.0

    return {
        "zero_ratio": round(zero_ratio, 6),
        "skew": float(dstats["skew"]) if dstats["coverage"] > 0 else None,
        "kurt": float(dstats["kurtosis"]) if dstats["coverage"] > 0 else None,
        "extreme_ratio": extreme_ratio,
    }


def _empty() -> dict[str, Any]:
    return {
        "zero_ratio": None,
        "skew": None,
        "kurt": None,
        "extreme_ratio": None,
    }
