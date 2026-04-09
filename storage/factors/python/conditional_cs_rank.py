"""
Conditional Cross-Sectional Rank — Regime-Dependent Signal Selection

Mechanism:
1. Compute short-term (5d) and medium-term (20d) returns
2. Classify regime: high_vol (>60th percentile) vs low_vol (<40th percentile)
3. In high_vol: use short-term momentum signal
   In low_vol: use medium-term momentum signal
   In middle: blend both
4. Use cross-sectional rank for each regime to ensure proper normalization
5. Volume filter for liquidity

This captures: the hypothesis that different volatility regimes favor
different momentum timeframes. DSL cannot express if-else on cross-sectional
quantities.
"""

import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Parameters:
    -----------
    df : pd.DataFrame with columns [open, high, low, close, volume, amount]
    params : dict with optional keys:
        - short_period: int (default 5) — short-term momentum window
        - long_period: int (default 20) — medium-term momentum window
        - vol_period: int (default 10) — volatility lookback
        - vol_high_pct: float (default 0.60)
        - vol_low_pct: float (default 0.40)
        - vol_filter_pct: float (default 0.30)

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    short_period = params.get("short_period", 5)
    long_period = params.get("long_period", 20)
    vol_period = params.get("vol_period", 10)
    vol_high_pct = params.get("vol_high_pct", 0.60)
    vol_low_pct = params.get("vol_low_pct", 0.40)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    volume = df["volume"]

    # Step 1: Compute short and long period returns
    ret_short = close.pct_change(short_period)
    ret_long = close.pct_change(long_period)

    # Step 2: Compute rolling volatility
    vol = ret_short.rolling(vol_period).std()

    # Step 3: Cross-sectional percentile of volatility
    vol_pct = vol.groupby(level="datetime").rank(pct=True)

    # Step 4: Regime classification
    high_vol_mask = vol_pct > vol_high_pct
    low_vol_mask = vol_pct < vol_low_pct
    middle_mask = ~(high_vol_mask | low_vol_mask)

    # Step 5: Compute cross-sectional ranks for each return signal
    # Rank within each date, then normalize to [-1, 1]
    rank_short = ret_short.groupby(level="datetime").rank(pct=True) * 2 - 1
    rank_long = ret_long.groupby(level="datetime").rank(pct=True) * 2 - 1

    # Step 6: Blend based on regime
    # High vol: short-term signal dominates
    # Low vol: medium-term signal dominates
    # Middle: equal blend
    regime_signal = (
        high_vol_mask.astype(float) * rank_short +
        low_vol_mask.astype(float) * rank_long +
        middle_mask.astype(float) * (rank_short + rank_long) / 2
    )

    # Step 7: Volume filter — only include stocks with sufficient liquidity
    vol_avg = volume.rolling(20).mean()
    vol_pct_rank = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct_rank > vol_filter_pct

    # Apply volume filter
    signal = regime_signal * vol_filter.astype(float)

    return signal
