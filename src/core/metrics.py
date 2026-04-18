"""Shared stateless metric primitives.

Pure functions depending only on numpy/pandas. No Plotly/Streamlit/Qlib imports.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import TRADING_DAYS_PER_YEAR


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
