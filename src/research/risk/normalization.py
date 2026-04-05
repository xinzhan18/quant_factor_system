"""Cross-sectional normalization: winsorize + z-score.

Pure functions. No I/O, no Qlib.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def cross_sectional_normalize(
    series: pd.Series,
    sigma: float = 3.0,
) -> pd.Series:
    """Per-date winsorize at ±sigma*std then z-score.

    Input: pd.Series with (datetime, instrument) MultiIndex.
    Output: same shape, NaN-preserving.
    """
    if series.empty:
        return series.copy()

    # Two-pass winsorize: first pass computes robust median/MAD to set clip bounds,
    # second pass re-standardizes. This prevents a single extreme outlier from
    # inflating std and making the clip ineffective.
    grouped = series.groupby(level=0)
    median = grouped.transform("median")
    mad = grouped.transform(lambda x: (x - x.median()).abs().median())
    # MAD-based bounds (1.4826 converts MAD to std-equivalent for normal data)
    robust_std = 1.4826 * mad
    robust_std = robust_std.replace(0, np.nan)

    lower = median - sigma * robust_std
    upper = median + sigma * robust_std
    clipped = series.clip(lower=lower, upper=upper)

    # Z-score after clipping
    grouped2 = clipped.groupby(level=0)
    mean2 = grouped2.transform("mean")
    std2 = grouped2.transform("std").replace(0, np.nan)

    return (clipped - mean2) / std2
