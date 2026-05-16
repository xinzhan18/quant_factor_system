"""Conditional rolling mean template."""

from __future__ import annotations

import pandas as pd

from research.daily_templates.expression import evaluate_expression


def run(df: pd.DataFrame, params: dict) -> pd.Series:
    """Compute rolling mean of value over rows where condition is true."""
    window = int(params.get("window", 20))
    min_count = int(params.get("min_count", 1))
    if window <= 0:
        raise ValueError("window must be positive")
    if min_count <= 0:
        raise ValueError("min_count must be positive")

    value = evaluate_expression(params["value"], df)
    condition = evaluate_expression(params["condition"], df).astype(bool)
    masked = value.where(condition)
    grouped = masked.groupby(level=-1, group_keys=False)
    count = grouped.rolling(window, min_periods=1).count().droplevel(0)
    mean = grouped.rolling(window, min_periods=min_count).mean().droplevel(0)
    return mean.where(count >= min_count).sort_index().rename("value")
