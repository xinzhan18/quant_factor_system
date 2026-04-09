"""
Cross-Sectional Return Decomposition — Market vs Idiosyncratic

Mechanism:
1. For each date, regress stock returns on market return
2. Extract residuals as idiosyncratic return (alpha signal)
3. Apply time-series smoothing to reduce noise
4. Condition on volume to filter thin stocks

This captures: stock-specific return component after removing market movement.
"""

import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Parameters:
    -----------
    df : pd.DataFrame with columns [open, high, low, close, volume, amount, pe_ratio, turnover_rate]
    params : dict with optional keys:
        - ret_period: int (default 5) — return lookback period
        - ewm_span: int (default 10) — smoothing span
        - vol_filter: float (default 0.3) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    ret_period = params.get("ret_period", 5)
    ewm_span = params.get("ewm_span", 10)
    vol_filter_pct = params.get("vol_filter", 0.3)

    close = df["close"]
    volume = df["volume"]

    # Step 1: Compute stock returns
    ret = close.pct_change(ret_period)

    # Step 2: For each date, compute cross-sectional regression
    # Market return = equal-weighted mean of all stocks
    market_ret = ret.groupby(level="datetime").transform("mean")

    # Step 3: Compute residuals: ret - beta * market_ret
    # For simplicity, assume beta = 1 (same market exposure for all stocks)
    # In practice, we could estimate beta from rolling regression
    residual = ret - market_ret

    # Step 4: Apply EWM smoothing to reduce noise
    residual_smooth = residual.groupby(level="instrument").transform(
        lambda x: x.ewm(span=ewm_span).mean()
    )

    # Step 5: Volume filter — only include stocks with sufficient volume
    vol_avg = volume.rolling(20).mean()
    vol_pct = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct > vol_filter_pct

    # Apply volume filter
    signal = residual_smooth * vol_filter.astype(float)

    return signal
