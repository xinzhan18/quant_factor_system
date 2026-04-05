"""Stability computations: split, regime, sign consistency, decay.

Pure vectorized functions. No I/O, no Qlib.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Split stability
# ---------------------------------------------------------------------------

def compute_split_stability(
    ic_series: pd.Series,
    n_splits: int = 4,
    min_days: int = 60,
) -> Dict[str, Any]:
    """Split validation IC series into equal periods and assess stability.

    Args:
        ic_series: Daily IC values with DatetimeIndex.
        n_splits: Target number of equal-length splits (falls back to 3 if
            4 splits each have fewer than *min_days* observations).
        min_days: Minimum trading days per split.

    Returns:
        Dict with split_ic_means, sign_consistency, dispersion, bucket.
    """
    ic = ic_series.dropna().sort_index()
    if ic.empty:
        return _insufficient_splits()

    # Try n_splits first, fall back to n_splits - 1
    for n in (n_splits, n_splits - 1):
        if n < 3:
            return _insufficient_splits()
        chunks = np.array_split(ic.values, n)
        if all(len(c) >= min_days for c in chunks):
            break
    else:
        return _insufficient_splits()

    split_means = [float(np.mean(c)) for c in chunks]
    overall_mean = float(np.mean(ic.values))

    # Sign consistency: fraction of splits with same sign as overall mean
    if abs(overall_mean) < 1e-10:
        sign_consistency = 0.0
    else:
        target_sign = np.sign(overall_mean)
        sign_consistency = sum(
            1 for m in split_means if np.sign(m) == target_sign
        ) / len(split_means)

    # Dispersion: std of split means / |overall mean|
    dispersion = float(
        np.std(split_means, ddof=0) / (abs(np.mean(split_means)) + 1e-6)
    )

    # Bucket
    if sign_consistency >= 0.75 and dispersion <= 0.75:
        bucket = "high"
    elif sign_consistency >= 0.50 and dispersion <= 1.25:
        bucket = "medium"
    else:
        bucket = "low"

    return {
        "split_ic_means": split_means,
        "sign_consistency": round(sign_consistency, 4),
        "dispersion": round(dispersion, 4),
        "bucket": bucket,
        "n_splits": len(chunks),
    }


def _insufficient_splits() -> Dict[str, Any]:
    return {
        "split_ic_means": [],
        "sign_consistency": np.nan,
        "dispersion": np.nan,
        "bucket": "insufficient_splits",
        "n_splits": 0,
    }


# ---------------------------------------------------------------------------
# Regime stability
# ---------------------------------------------------------------------------

def compute_regime_stability(
    ic_series: pd.Series,
    benchmark_returns: pd.Series,
    min_regime_days: int = 40,
) -> Dict[str, Any]:
    """Assess IC stability across bull / bear / range regimes.

    Regime classification uses trailing-60-day cumulative return of the
    benchmark:
      - bull:  r60 > 0.08
      - bear:  r60 < -0.08
      - range: otherwise

    Args:
        ic_series: Daily IC values with DatetimeIndex.
        benchmark_returns: Daily benchmark returns with DatetimeIndex.
        min_regime_days: Minimum days in a regime for it to be valid.

    Returns:
        Dict with regime_ic_means, sign_consistency, strength_ratio, bucket.
    """
    ic = ic_series.dropna().sort_index()
    bench = benchmark_returns.dropna().sort_index()

    if ic.empty or bench.empty:
        return _insufficient_regime()

    # Trailing 60-day cumulative return
    r60 = bench.rolling(60, min_periods=60).apply(
        lambda x: (1 + x).prod() - 1, raw=True
    )

    # Align
    common = ic.index.intersection(r60.dropna().index)
    if len(common) == 0:
        return _insufficient_regime()

    ic_aligned = ic.loc[common]
    r60_aligned = r60.loc[common]

    # Classify regimes
    labels = pd.Series("range", index=common)
    labels[r60_aligned > 0.08] = "bull"
    labels[r60_aligned < -0.08] = "bear"

    regime_ic_means: Dict[str, float] = {}
    valid_regimes: List[str] = []

    for regime in ("bull", "bear", "range"):
        mask = labels == regime
        regime_ic = ic_aligned[mask]
        if len(regime_ic) >= min_regime_days:
            regime_ic_means[regime] = float(regime_ic.mean())
            valid_regimes.append(regime)
        else:
            regime_ic_means[regime] = np.nan

    if len(valid_regimes) < 2:
        return _insufficient_regime(regime_ic_means=regime_ic_means)

    # Overall sign
    overall_mean = float(ic_aligned.mean())
    if abs(overall_mean) < 1e-10:
        return _insufficient_regime(regime_ic_means=regime_ic_means)

    target_sign = np.sign(overall_mean)
    n_flips = sum(
        1
        for r in valid_regimes
        if np.sign(regime_ic_means[r]) != target_sign
    )
    sign_consistency = (len(valid_regimes) - n_flips) / len(valid_regimes)

    # Strength ratio: max|IC| / min|IC| across valid regimes
    abs_means = [abs(regime_ic_means[r]) for r in valid_regimes]
    strength_ratio = max(abs_means) / max(min(abs_means), 1e-4)

    # Weak regime: |IC| < 0.002
    n_weak = sum(1 for a in abs_means if a < 0.002)

    # Bucket
    if n_flips == 0 and strength_ratio <= 2.0:
        bucket = "high"
    elif n_flips <= 1 and n_weak <= 1 and strength_ratio <= 3.0:
        bucket = "medium"
    else:
        bucket = "low"

    return {
        "regime_ic_means": regime_ic_means,
        "sign_consistency": round(sign_consistency, 4),
        "strength_ratio": round(strength_ratio, 4),
        "bucket": bucket,
        "valid_regimes": valid_regimes,
    }


def _insufficient_regime(
    regime_ic_means: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    return {
        "regime_ic_means": regime_ic_means or {},
        "sign_consistency": np.nan,
        "strength_ratio": np.nan,
        "bucket": "insufficient_regime_coverage",
        "valid_regimes": [],
    }


# ---------------------------------------------------------------------------
# Sign consistency (train vs validation)
# ---------------------------------------------------------------------------

def compute_sign_consistency(
    ic_train: pd.Series, ic_validation: pd.Series
) -> bool:
    """Check whether mean IC has the same sign in train and validation.

    Returns False if either series is empty or has near-zero mean.
    """
    t_mean = ic_train.dropna().mean() if not ic_train.empty else 0.0
    v_mean = ic_validation.dropna().mean() if not ic_validation.empty else 0.0
    if abs(t_mean) < 1e-10 or abs(v_mean) < 1e-10:
        return False
    return bool(np.sign(t_mean) == np.sign(v_mean))


# ---------------------------------------------------------------------------
# Train-validation decay
# ---------------------------------------------------------------------------

def compute_train_validation_decay(
    ic_train_mean: float, ic_val_mean: float
) -> float:
    """Compute decay ratio from train to validation IC mean.

    Returns |val| / |train|.  Values < 1 indicate decay; > 1 indicates
    strengthening.  Returns NaN if train mean is near zero.
    """
    if abs(ic_train_mean) < 1e-10:
        return np.nan
    return abs(ic_val_mean) / abs(ic_train_mean)
