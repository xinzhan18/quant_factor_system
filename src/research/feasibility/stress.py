"""Stress and holding-period proxies.

- ``rebalance_stress_proxy``: turnover * tail / max(lcr, 0.10).
- ``holding_period_proxy``: bucket derived from signal half-life.
- ``compute_half_life``: estimate from autocorrelation decay.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def compute_half_life(signal: pd.DataFrame, *, max_lag: int = 20) -> float:
    """Estimate the signal half-life from autocorrelation decay.

    For each instrument, compute the lag-k autocorrelation of the signal,
    then average across instruments.  The half-life is the first lag
    where the mean autocorrelation drops below 0.5, or ``max_lag`` if it
    never drops.

    Parameters
    ----------
    signal : DataFrame
        MultiIndex (datetime, instrument), single column.
    max_lag : int
        Maximum lag to test.

    Returns
    -------
    float
        Estimated half-life in trading days.
    """
    col = signal.columns[0]
    acf_by_lag = {lag: [] for lag in range(1, max_lag + 1)}

    for _inst, group in signal[col].groupby(level=1):
        series = group.droplevel(1).dropna()
        if len(series) < max_lag + 5:
            continue
        arr = series.values
        if np.var(arr) == 0:
            continue
        for lag in range(1, max_lag + 1):
            corr = np.corrcoef(arr[:-lag], arr[lag:])[0, 1]
            if np.isfinite(corr):
                acf_by_lag[lag].append(corr)

    # Average autocorrelation per lag
    for lag in range(1, max_lag + 1):
        vals = acf_by_lag[lag]
        if not vals:
            continue
        mean_acf = float(np.mean(vals))
        if mean_acf < 0.5:
            return float(lag)

    return float(max_lag)


def compute_holding_period_proxy(half_life: float) -> str:
    """Map half-life to a holding-period bucket.

    Returns
    -------
    str
        ``"short"`` if half_life <= 3, ``"medium"`` if 3 < half_life <= 10,
        ``"long"`` otherwise.
    """
    if half_life <= 3:
        return "short"
    if half_life <= 10:
        return "medium"
    return "long"


def compute_rebalance_stress(
    turnover: float,
    tail_concentration: float,
    liquidity_coverage_ratio: float,
) -> dict:
    """Compute rebalance stress proxy and its bucket.

    ``stress = turnover * tail_concentration / max(lcr, 0.10)``

    Parameters
    ----------
    turnover : float
        Mean two-sided turnover.
    tail_concentration : float
        Time-averaged tail trade concentration.
    liquidity_coverage_ratio : float
        Time-averaged liquidity coverage ratio.

    Returns
    -------
    dict
        Keys: ``rebalance_stress_proxy``, ``rebalance_stress_bucket``.
    """
    lcr_safe = max(liquidity_coverage_ratio, 0.10)
    stress = turnover * tail_concentration / lcr_safe

    if stress < 0.20:
        bucket = "low"
    elif stress <= 0.50:
        bucket = "medium"
    else:
        bucket = "high"

    return {
        "rebalance_stress_proxy": float(stress),
        "rebalance_stress_bucket": bucket,
    }
