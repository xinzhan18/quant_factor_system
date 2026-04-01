"""Shared stateless metric primitives.

Pure functions depending only on numpy/pandas. No Plotly/Streamlit/Qlib imports.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import TRADING_DAYS_PER_YEAR


def ic_summary_from_series(daily_ics: pd.Series) -> dict:
    """Compute IC summary statistics from a daily IC series.

    Returns dict with keys: ic_mean, ic_std, ic_ir, ic_win_rate.
    """
    if daily_ics.empty:
        return {"ic_mean": np.nan, "ic_std": np.nan, "ic_ir": np.nan, "ic_win_rate": np.nan}
    arr = daily_ics.values.astype(float)
    valid = arr[~np.isnan(arr)]
    if len(valid) == 0:
        return {"ic_mean": np.nan, "ic_std": np.nan, "ic_ir": np.nan, "ic_win_rate": np.nan}
    ic_mean = float(np.mean(valid))
    ic_std = float(np.std(valid, ddof=1)) if len(valid) > 1 else np.nan
    ic_ir = float(ic_mean / ic_std) if ic_std and ic_std > 0 else np.nan
    ic_win_rate = float(np.sum(valid > 0) / len(valid))
    return {"ic_mean": ic_mean, "ic_std": ic_std, "ic_ir": ic_ir, "ic_win_rate": ic_win_rate}


def annualize_return(daily_returns: pd.Series) -> float:
    """Annualize the mean of daily returns."""
    if daily_returns.empty:
        return np.nan
    return float(daily_returns.mean() * TRADING_DAYS_PER_YEAR)


def annualize_volatility(daily_returns: pd.Series) -> float:
    """Annualize daily return volatility (std)."""
    if daily_returns.empty:
        return np.nan
    return float(daily_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR))


def sharpe_ratio(daily_returns: pd.Series) -> float:
    """Compute annualized Sharpe ratio (assuming zero risk-free rate)."""
    ann_ret = annualize_return(daily_returns)
    ann_vol = annualize_volatility(daily_returns)
    if np.isnan(ann_ret) or np.isnan(ann_vol) or ann_vol == 0:
        return np.nan
    return float(ann_ret / ann_vol)


def max_drawdown(cumulative: pd.Series) -> float:
    """Compute maximum drawdown from a cumulative return/value series.

    Returns a non-positive float (the trough-to-peak drop).
    """
    if cumulative.empty:
        return np.nan
    peak = cumulative.cummax()
    dd = cumulative - peak
    return float(dd.min())


def calmar_ratio(ann_ret: float, max_dd: float) -> float:
    """Compute Calmar ratio (annualized return / |max drawdown|)."""
    if np.isnan(ann_ret) or np.isnan(max_dd) or max_dd == 0:
        return np.nan
    return float(ann_ret / abs(max_dd))


def win_rate(series: pd.Series) -> float:
    """Compute fraction of positive values in a series."""
    if series.empty:
        return np.nan
    valid = series.dropna()
    if len(valid) == 0:
        return np.nan
    return float((valid > 0).sum() / len(valid))


def sortino_ratio(daily_returns: pd.Series) -> float:
    """Sortino ratio: annualized return / annualized downside deviation."""
    ann_ret = annualize_return(daily_returns)
    negative_returns = daily_returns[daily_returns < 0]
    if len(negative_returns) == 0:
        return float("inf")
    downside_std = negative_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    if downside_std == 0:
        return float("inf")
    return ann_ret / downside_std


def max_drawdown_duration(cumulative: pd.Series) -> int:
    """Number of trading days in the longest drawdown (peak to recovery or end)."""
    if len(cumulative) < 2:
        return 0
    running_max = cumulative.cummax()
    in_drawdown = cumulative < running_max
    if not in_drawdown.any():
        return 0
    groups = (~in_drawdown).cumsum()
    dd_groups = groups[in_drawdown]
    if len(dd_groups) == 0:
        return 0
    return int(dd_groups.value_counts().max())
