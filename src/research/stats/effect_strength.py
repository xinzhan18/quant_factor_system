"""Effect strength computation: IC mean/IR/win_rate/monotonicity.

Pure vectorized functions. No I/O, no Qlib.
"""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

import numpy as np
import pandas as pd

from core.factor_stats import (
    daily_cross_sectional_ic,
    ic_summary,
    monotonicity,
    quintile_returns,
)


def _filter_range(
    df: pd.DataFrame, start: str, end: str
) -> pd.DataFrame:
    """Filter a flat DataFrame [time, symbol, value] to a date range (inclusive)."""
    mask = (df["time"] >= pd.Timestamp(start)) & (df["time"] <= pd.Timestamp(end))
    return df.loc[mask].copy()


def compute_effect_strength(
    factor_values: pd.DataFrame,
    forward_returns: pd.DataFrame,
    train_range: Tuple[str, str],
    validation_range: Tuple[str, str],
    min_obs: int = 30,
    n_quantiles: int = 5,
) -> Dict[str, Any]:
    """Compute effect strength metrics on train and validation periods.

    Uses Spearman rank IC cross-sectionally per day, then aggregates.

    Args:
        factor_values: Flat DataFrame [time, symbol, value].
        forward_returns: Flat DataFrame [time, symbol, value].
        train_range: (start, end) date strings for in-sample period.
        validation_range: (start, end) date strings for out-of-sample period.
        min_obs: Minimum cross-sectional observations per day.
        n_quantiles: Number of quantile groups for monotonicity.

    Returns:
        Dict with ic_mean_train, ic_ir_train, ic_mean_validation,
        ic_ir_validation, ic_win_rate_validation, monotonicity_validation,
        plus ic_series_train and ic_series_validation for downstream use.
    """
    # Split data into train / validation
    fv_train = _filter_range(factor_values, *train_range)
    fr_train = _filter_range(forward_returns, *train_range)
    fv_val = _filter_range(factor_values, *validation_range)
    fr_val = _filter_range(forward_returns, *validation_range)

    # Train IC
    ic_train = daily_cross_sectional_ic(fv_train, fr_train, min_obs=min_obs)
    train_stats = ic_summary(ic_train)

    # Validation IC
    ic_val = daily_cross_sectional_ic(fv_val, fr_val, min_obs=min_obs)
    val_stats = ic_summary(ic_val)

    # Monotonicity on validation
    q_ret, _ = quintile_returns(fv_val, fr_val, n_quantiles=n_quantiles)
    mono_val = monotonicity(q_ret)

    return {
        "ic_mean_train": train_stats["ic_mean"],
        "ic_ir_train": train_stats["ic_ir"],
        "ic_mean_validation": val_stats["ic_mean"],
        "ic_ir_validation": val_stats["ic_ir"],
        "ic_win_rate_validation": val_stats["ic_win_rate"],
        "monotonicity_validation": mono_val,
        # Carry IC series for downstream stability/reliability tests
        "ic_series_train": ic_train,
        "ic_series_validation": ic_val,
    }
