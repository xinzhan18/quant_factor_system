"""Statistical reliability: expanding-window IC, bootstrap, purged walk-forward.

Pure vectorized functions. No I/O, no Qlib.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from core.factor_stats import daily_cross_sectional_ic, ic_summary


# ---------------------------------------------------------------------------
# Expanding-window IC stability
# ---------------------------------------------------------------------------

def compute_expanding_window_ic(
    factor_values: pd.DataFrame,
    forward_returns: pd.DataFrame,
    start: str,
    step_months: int = 6,
    min_obs: int = 30,
) -> Dict[str, Any]:
    """Expand training window from *start* in steps, compute cumulative IC.

    At each step the window grows by *step_months* and we compute the IC
    over the entire window up to that point.

    Args:
        factor_values: Flat DataFrame [time, symbol, value].
        forward_returns: Flat DataFrame [time, symbol, value].
        start: Earliest date string (inclusive).
        step_months: Months to add per expansion step.
        min_obs: Minimum cross-sectional observations per day.

    Returns:
        Dict with path (list of {end_date, ic_mean}), stability, sign_consistency,
        decay_ratio, pass.
    """
    start_ts = pd.Timestamp(start)
    fv = factor_values.loc[factor_values["time"] >= start_ts].copy()
    fr = forward_returns.loc[forward_returns["time"] >= start_ts].copy()

    if fv.empty or fr.empty:
        return _empty_expanding()

    max_date = fv["time"].max()
    path: List[Dict[str, Any]] = []

    end = start_ts + pd.DateOffset(months=step_months)
    while end <= max_date:
        fv_win = fv.loc[fv["time"] <= end]
        fr_win = fr.loc[fr["time"] <= end]
        ic_series = daily_cross_sectional_ic(fv_win, fr_win, min_obs=min_obs)
        if not ic_series.empty:
            path.append({
                "end_date": str(end.date()),
                "ic_mean": float(ic_series.mean()),
            })
        end += pd.DateOffset(months=step_months)

    if len(path) < 2:
        return _empty_expanding(path=path)

    ic_means = np.array([p["ic_mean"] for p in path])

    # Sign consistency: fraction of steps sharing the sign of the final window
    final_sign = np.sign(ic_means[-1])
    if final_sign == 0:
        sign_consistency = 0.0
    else:
        sign_consistency = float(np.mean(np.sign(ic_means) == final_sign))

    # Stability: 1 - coeff_of_variation (capped at [0, 1])
    std = float(np.std(ic_means, ddof=1)) if len(ic_means) > 1 else 0.0
    mean_abs = abs(float(np.mean(ic_means)))
    cv = std / (mean_abs + 1e-8)
    stability = float(np.clip(1.0 - cv, 0.0, 1.0))

    # Decay ratio: last ic_mean / first ic_mean (absolute)
    if abs(ic_means[0]) < 1e-10:
        decay_ratio = np.nan
    else:
        decay_ratio = abs(ic_means[-1]) / abs(ic_means[0])

    # Pass criteria: sign_consistency >= 0.6 and stability >= 0.3
    passed = bool(sign_consistency >= 0.6 and stability >= 0.3)

    return {
        "path": path,
        "stability": round(stability, 4),
        "sign_consistency": round(sign_consistency, 4),
        "decay_ratio": round(decay_ratio, 4) if np.isfinite(decay_ratio) else np.nan,
        "pass": passed,
    }


def _empty_expanding(path: Optional[List] = None) -> Dict[str, Any]:
    return {
        "path": path or [],
        "stability": np.nan,
        "sign_consistency": np.nan,
        "decay_ratio": np.nan,
        "pass": False,
    }


# ---------------------------------------------------------------------------
# Bootstrap stability (moving-block bootstrap)
# ---------------------------------------------------------------------------

def compute_bootstrap_stability(
    ic_series: pd.Series,
    B: int = 200,
    seed: int = 42,
) -> Dict[str, Any]:
    """Moving-block bootstrap on daily IC series.

    Block length L = min(60, max(20, round(sqrt(T)))).

    Args:
        ic_series: Daily IC values.
        B: Number of bootstrap resamples.
        seed: Random seed.

    Returns:
        Dict with sign_consistency, median_abs_ratio, score, status.
    """
    ic = ic_series.dropna().values.astype(float)
    T = len(ic)

    if T < 120:
        return {
            "sign_consistency": np.nan,
            "median_abs_ratio": np.nan,
            "score": np.nan,
            "status": "low_power",
        }

    block_len = min(60, max(20, round(np.sqrt(T))))
    raw_mean = float(np.mean(ic))
    raw_sign = np.sign(raw_mean)

    rng = np.random.default_rng(seed)

    # Pre-compute all bootstrap samples in a vectorized manner
    n_blocks = int(np.ceil(T / block_len))
    # For each bootstrap replicate, pick n_blocks random start indices
    starts = rng.integers(0, T - block_len + 1, size=(B, n_blocks))

    boot_means = np.empty(B, dtype=float)
    for i in range(B):
        # Concatenate blocks and truncate to T
        indices = np.concatenate(
            [np.arange(s, s + block_len) for s in starts[i]]
        )[:T]
        boot_means[i] = np.mean(ic[indices])

    # Sign consistency
    if raw_sign == 0:
        sign_consistency = 0.0
    else:
        sign_consistency = float(np.mean(np.sign(boot_means) == raw_sign))

    # Median absolute ratio
    median_abs_ratio = float(
        np.median(np.abs(boot_means)) / max(abs(raw_mean), 1e-6)
    )

    # Score
    score = 0.7 * sign_consistency + 0.3 * float(np.clip(median_abs_ratio, 0, 1))

    # Status
    if score >= 0.65:
        status = "good"
    elif score >= 0.45:
        status = "borderline"
    else:
        status = "poor"

    return {
        "sign_consistency": round(sign_consistency, 4),
        "median_abs_ratio": round(median_abs_ratio, 4),
        "score": round(score, 4),
        "status": status,
    }


# ---------------------------------------------------------------------------
# Purged walk-forward
# ---------------------------------------------------------------------------

def compute_purged_walk_forward(
    factor_values: pd.DataFrame,
    forward_returns: pd.DataFrame,
    purge_days: int = 5,
    n_splits: int = 5,
    min_test_days: int = 60,
    min_obs: int = 30,
) -> Dict[str, Any]:
    """Purged walk-forward cross-validation of IC.

    Time-series splits with a purge gap between train and test to avoid
    lookahead bias.

    Args:
        factor_values: Flat DataFrame [time, symbol, value].
        forward_returns: Flat DataFrame [time, symbol, value].
        purge_days: Gap days between train and test periods.
        n_splits: Number of walk-forward splits.
        min_test_days: Minimum test days per split.
        min_obs: Minimum cross-sectional observations per day.

    Returns:
        Dict with score, pass, status, fold_results.
    """
    all_dates = sorted(factor_values["time"].dropna().unique())
    T = len(all_dates)

    # Each fold: train on first k portions, test on (k+1)-th portion
    # Minimum: n_splits + 1 portions of min_test_days
    portion_size = T // (n_splits + 1)
    if portion_size < min_test_days:
        return {
            "score": np.nan,
            "pass": False,
            "status": "low_power",
            "fold_results": [],
        }

    fold_results: List[Dict[str, Any]] = []
    valid_fold_ics: List[float] = []

    for fold in range(n_splits):
        train_end_idx = (fold + 1) * portion_size - 1
        test_start_idx = train_end_idx + 1 + purge_days
        test_end_idx = test_start_idx + portion_size - 1

        if test_end_idx >= T:
            break

        train_end = all_dates[train_end_idx]
        test_start = all_dates[test_start_idx]
        test_end = all_dates[test_end_idx]

        # Test fold IC
        fv_test = factor_values.loc[
            (factor_values["time"] >= test_start) & (factor_values["time"] <= test_end)
        ]
        fr_test = forward_returns.loc[
            (forward_returns["time"] >= test_start)
            & (forward_returns["time"] <= test_end)
        ]

        ic = daily_cross_sectional_ic(fv_test, fr_test, min_obs=min_obs)
        if ic.empty:
            fold_results.append({"fold": fold, "ic_mean": np.nan, "n_days": 0})
            continue

        fold_ic = float(ic.mean())
        fold_results.append({
            "fold": fold,
            "ic_mean": round(fold_ic, 6),
            "n_days": len(ic),
        })
        valid_fold_ics.append(fold_ic)

    if len(valid_fold_ics) < 2:
        return {
            "score": np.nan,
            "pass": False,
            "status": "low_power",
            "fold_results": fold_results,
        }

    arr = np.array(valid_fold_ics)
    mean_ic = float(np.mean(arr))
    std_ic = float(np.std(arr, ddof=1))
    ir = mean_ic / std_ic if std_ic > 1e-10 else 0.0

    # Score: fraction of folds with same sign as mean
    if abs(mean_ic) < 1e-10:
        sign_frac = 0.0
    else:
        sign_frac = float(np.mean(np.sign(arr) == np.sign(mean_ic)))

    score = 0.5 * sign_frac + 0.5 * float(np.clip(abs(ir) / 0.3, 0, 1))
    passed = bool(score >= 0.50 and sign_frac >= 0.60)

    return {
        "score": round(score, 4),
        "pass": passed,
        "status": "sufficient",
        "fold_results": fold_results,
    }
