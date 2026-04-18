"""Vectorized quintile returns + long-short portfolio stats.

Wraps ``core.factor_stats.quintile_returns`` (vectorized pivot →
cross-sectional qcut → masked numpy aggregation) and
``core.factor_stats.monotonicity`` for rank-ordering assessment.

Also absorbs long-short risk-adjusted metrics (formerly a private
helper in ``phase2_execute``): ``compute_long_short_stats`` turns a
daily long-short series into the summary block consumed by
``result.yaml.candidates[].quintile.ls_stats``.
"""

from __future__ import annotations

from typing import Any, Sequence

import numpy as np
import pandas as pd

from core.factor_stats import monotonicity, quintile_returns
from core.metrics import (
    annualize_return,
    calmar_ratio,
    max_drawdown,
    max_drawdown_duration,
    sharpe_ratio,
    sortino_ratio,
)


def compute_quintile_returns(
    factor_flat: pd.DataFrame,
    returns_flat: pd.DataFrame,
    n_quantiles: int = 5,
    min_obs: int = 30,
) -> dict[str, Any]:
    """Cross-sectional quantile returns + monotonicity + long-short daily.

    Returns
    -------
    dict
        ``{"quintile_returns": {"q1", ..., "qN"}, "monotonicity": float,
        "long_short_daily": list[float], "long_short_mean": float,
        "long_short_n_days": int, "per_quintile_daily": DataFrame}``

    ``per_quintile_daily`` is a (date × q1..qN) DataFrame used by Phase 4
    charts. Callers should persist it separately (parquet) rather than
    embedding in result.yaml.
    """
    qret, daily_ls, per_q_daily = quintile_returns(
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
        "per_quintile_daily": per_q_daily,
    }


def compute_long_short_stats(daily_ls: Sequence[float]) -> dict[str, Any]:
    """Risk-adjusted metrics from a daily long-short series.

    Returns an empty dict when ``daily_ls`` is empty so downstream callers
    can safely ``update()`` / merge without guarding.
    """
    if not daily_ls:
        return {}

    arr = np.asarray(list(daily_ls), dtype=float)
    arr = arr[np.isfinite(arr)]
    n = int(arr.size)
    if n == 0:
        return {}

    series = pd.Series(arr)
    cum = (1.0 + series).cumprod()

    ann_ret = annualize_return(series)
    mdd = float(max_drawdown(cum))
    std = float(arr.std(ddof=0))
    mean = float(arr.mean())
    tstat = float(mean / (std / np.sqrt(n))) if std > 0 else 0.0

    return {
        "mean": round(mean, 6),
        "std": round(std, 6),
        "sharpe": round(float(sharpe_ratio(series)), 4),
        "sortino": round(float(sortino_ratio(series)), 4),
        "calmar": round(float(calmar_ratio(ann_ret, mdd)), 4),
        "max_dd": round(mdd, 4),
        "max_dd_duration": int(max_drawdown_duration(cum)),
        "tstat": round(tstat, 4),
        "n_days": n,
    }
