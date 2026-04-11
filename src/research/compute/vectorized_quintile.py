"""Vectorized quintile returns + monotonicity — Phase 2 interface.

Thin wrapper over ``core.factor_stats.quintile_returns`` / ``monotonicity``.
Those functions are already the fully vectorized reference implementations
(pivot → cross-sectional rank/qcut → masked numpy ops, no per-date loop).
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from core.factor_stats import monotonicity, quintile_returns


def compute_quintile_returns(
    factor_flat: pd.DataFrame,
    returns_flat: pd.DataFrame,
    n_quantiles: int = 5,
    min_obs: int = 30,
) -> dict[str, Any]:
    """Cross-sectional quantile returns + monotonicity in one pass.

    Parameters
    ----------
    factor_flat, returns_flat
        Flat ``[time, symbol, value]`` frames.
    n_quantiles
        Number of quantile groups (typically 5 for quintiles).
    min_obs
        Minimum valid cross-sectional observations per day to include
        the day in the aggregation.

    Returns
    -------
    dict
        ``{"quintile_returns": {"q1": ..., "q2": ..., "q3": ..., "q4": ...,
        "q5": ...}, "monotonicity": float, "long_short_daily":
        list[float], "long_short_mean": float, "long_short_n_days": int}``
    """
    qret, daily_ls = quintile_returns(
        factor_flat, returns_flat, n_quantiles=n_quantiles, min_obs=min_obs
    )
    mono = monotonicity(qret)

    ls_mean = (
        float(sum(daily_ls) / len(daily_ls)) if daily_ls else float("nan")
    )
    return {
        "quintile_returns": {k: float(v) for k, v in qret.items()},
        "monotonicity": float(mono),
        "long_short_daily": daily_ls,
        "long_short_mean": ls_mean,
        "long_short_n_days": int(len(daily_ls)),
    }
