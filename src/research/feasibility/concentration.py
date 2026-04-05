"""Concentration metrics for a proxy portfolio.

- ``tail_trade_concentration``: weight mass in top-k names, time-averaged.
- ``small_cap_concentration``: weight fraction in small-cap stocks (market-cap
  at or below cross-sectional 30th percentile), time-averaged.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from research.feasibility.liquidity import _weighted_flag_ratio


def compute_tail_concentration(
    abs_weights: pd.DataFrame,
    *,
    top_k: int = 10,
) -> float:
    """Top-k absolute weight sum, averaged over dates.

    Parameters
    ----------
    abs_weights : DataFrame
        MultiIndex (datetime, instrument), column ``weight``.
    top_k : int
        Number of top positions to consider.

    Returns
    -------
    float
        Time-averaged tail concentration in [0, 1].
    """
    w_col = abs_weights.columns[0]

    def _date_tail(group: pd.Series) -> float:
        total = group.sum()
        if total == 0:
            return np.nan
        top = group.nlargest(min(top_k, len(group))).sum()
        return top / total

    per_date = abs_weights[w_col].groupby(level=0).apply(_date_tail)
    return float(per_date.mean())


def compute_small_cap_concentration(
    abs_weights: pd.DataFrame,
    market_cap: pd.DataFrame,
    *,
    pct: float = 0.30,
) -> float:
    """Weight fraction in small-cap stocks, time-averaged.

    A stock is *small-cap* if its ``market_cap`` is at or below the
    cross-sectional ``pct`` percentile on that date.

    Parameters
    ----------
    abs_weights : DataFrame
        MultiIndex (datetime, instrument), column ``weight``.
    market_cap : DataFrame
        MultiIndex (datetime, instrument), single column.
    pct : float
        Percentile threshold (0-1) for small-cap definition.

    Returns
    -------
    float
        Time-averaged small-cap weight fraction in [0, 1].
    """
    w_col = abs_weights.columns[0]
    cap_col = market_cap.columns[0]

    w = abs_weights[w_col]
    cap = market_cap[cap_col]

    threshold = cap.groupby(level=0).transform(
        lambda s: np.nanpercentile(s.dropna().values, pct * 100)
        if len(s.dropna()) > 0
        else np.nan
    )
    small_flag = cap <= threshold

    common_idx = w.index.intersection(small_flag.index)
    return _weighted_flag_ratio(w.loc[common_idx], small_flag.loc[common_idx])
