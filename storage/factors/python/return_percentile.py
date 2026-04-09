"""
Return Percentile — Cross-Sectional Relative Return Signal

Mechanism:
1. Compute rolling return at 20d
2. For each stock, compute its percentile rank within its OWN rolling return distribution
   — i.e., how does today's return compare to the stock's own 20d return range?
3. This captures "return relative to own recent history" (not cross-sectional)
4. Apply EWM smoothing
5. Volume filter

This is fundamentally different from cross-sectional rank:
- Cross-sectional rank: how does this stock's return compare to OTHER stocks today?
- Return percentile: how does today's return compare to THIS stock's own recent range?
"""

import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Parameters:
    -----------
    df : pd.DataFrame with columns [open, high, low, close, volume, amount]
    params : dict with optional keys:
        - ret_period: int (default 20) — return lookback
        - ewm_span: int (default 10) — smoothing span
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    ret_period = params.get("ret_period", 20)
    ewm_span = params.get("ewm_span", 10)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    volume = df["volume"]

    # Step 1: Compute rolling return
    ret = close.pct_change(ret_period)

    # Step 2: For each stock, compute rolling percentile of current return
    # within its own 20d return distribution
    # rolling_min = rolling minimum of return
    # rolling_max = rolling maximum of return
    roll_min = ret.rolling(ret_period).min()
    roll_max = ret.rolling(ret_period).max()
    roll_range = roll_max - roll_min

    # Percentile = (current - min) / range
    # This measures where today's return sits in the stock's own recent range
    percentile = (ret - roll_min) / roll_range.replace(0, np.nan)

    # Handle edge cases: flat range (all same returns) → set to NaN
    percentile = percentile.where(roll_range > 0)

    # Step 3: EWM smoothing
    pct_smooth = percentile.groupby(level="instrument").transform(
        lambda x: x.ewm(span=ewm_span).mean()
    )

    # Step 4: Volume filter
    vol_avg = volume.rolling(20).mean()
    vol_pct_rank = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct_rank > vol_filter_pct

    # Apply volume filter
    signal = pct_smooth * vol_filter.astype(float)

    return signal
