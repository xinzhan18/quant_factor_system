"""Liquidity coverage ratio for a proxy portfolio.

``liq20 = median($amount, 20)`` per stock.  A stock is *liquid* when its
``liq20`` is at or above the cross-sectional 30th percentile on that date.

``liquidity_coverage_ratio`` = fraction of absolute portfolio weight in
liquid stocks, averaged across rebalance dates.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_liquidity_coverage(
    abs_weights: pd.DataFrame,
    amount_data: pd.DataFrame,
    *,
    window: int = 20,
    pct: float = 0.30,
) -> float:
    """Return the time-averaged liquidity coverage ratio.

    Parameters
    ----------
    abs_weights : DataFrame
        MultiIndex (datetime, instrument), column ``weight`` (absolute).
    amount_data : DataFrame
        MultiIndex (datetime, instrument), single column with daily
        turnover amount.
    window : int
        Rolling median window for the liquidity proxy.
    pct : float
        Cross-sectional percentile threshold (0-1).

    Returns
    -------
    float
        Time-averaged liquidity coverage ratio in [0, 1].
    """
    amt_col = amount_data.columns[0]

    # Rolling median per instrument
    liq20 = (
        amount_data[amt_col]
        .groupby(level=1)
        .transform(lambda s: s.rolling(window, min_periods=1).median())
    )

    # Cross-sectional percentile threshold per date
    threshold = liq20.groupby(level=0).transform(
        lambda s: np.nanpercentile(s.dropna().values, pct * 100)
        if len(s.dropna()) > 0
        else np.nan
    )

    liquid_flag = liq20 >= threshold

    w_col = abs_weights.columns[0]
    w = abs_weights[w_col]

    common_idx = w.index.intersection(liquid_flag.index)
    w = w.loc[common_idx]
    liquid_flag = liquid_flag.loc[common_idx]

    return _weighted_flag_ratio(w, liquid_flag)


def _weighted_flag_ratio(weights: pd.Series, flag: pd.Series) -> float:
    """Time-averaged fraction of weight in flagged positions.

    Shared helper for liquidity and concentration computations.
    Both *weights* and *flag* must share a MultiIndex (datetime, instrument).
    """
    dates = weights.index.get_level_values(0).unique()
    ratios = []
    for dt in dates:
        try:
            w_dt = weights.loc[dt]
            flag_dt = flag.loc[dt]
            common = w_dt.index.intersection(flag_dt.index)
            if len(common) == 0:
                continue
            total = w_dt.loc[common].sum()
            if total == 0:
                continue
            ratios.append(w_dt.loc[common][flag_dt.loc[common]].sum() / total)
        except KeyError:
            continue

    if not ratios:
        return 0.0
    return float(np.nanmean(ratios))
