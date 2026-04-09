"""
Regime-Adaptive Short-Term Momentum

Mechanism:
1. Compute 5d return and its rolling volatility (10d)
2. Classify regime: high_vol (>60th percentile) vs low_vol (<40th percentile)
3. In high_vol: use shorter decay (faster signal)
   In low_vol: use longer decay (slower signal)
4. Use volume as a liquidity filter

This is a Python factor that DSL cannot express due to regime classification.
"""

import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Parameters:
    -----------
    df : pd.DataFrame with columns [open, high, low, close, volume, amount]
    params : dict with optional keys:
        - mom_period: int (default 5)
        - vol_period: int (default 10)
        - vol_high_percentile: float (default 0.60)
        - vol_low_percentile: float (default 0.40)
        - decay_high_vol: float (default 0.7)
        - decay_low_vol: float (default 0.3)
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    mom_period = params.get("mom_period", 5)
    vol_period = params.get("vol_period", 10)
    vol_high_pct = params.get("vol_high_percentile", 0.60)
    vol_low_pct = params.get("vol_low_percentile", 0.40)
    decay_high_vol = params.get("decay_high_vol", 0.7)
    decay_low_vol = params.get("decay_low_vol", 0.3)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    volume = df["volume"]

    # Step 1: 5d return
    ret = close.pct_change(mom_period)

    # Step 2: Rolling volatility (10d std of returns)
    vol = ret.rolling(vol_period).std()

    # Step 3: Cross-sectional percentile of volatility (rank within each date)
    vol_pct = vol.groupby(level="datetime").rank(pct=True)

    # Step 4: Regime classification
    # high_vol = 1 if vol_pct > vol_high_pct, low_vol = 1 if vol_pct < vol_low_pct
    high_vol_mask = vol_pct > vol_high_pct
    low_vol_mask = vol_pct < vol_low_pct
    middle_mask = ~(high_vol_mask | low_vol_mask)  # neutral zone

    # Step 5: Compute EWM decays
    # High volatility regime: faster decay (more responsive)
    decay_high = ret.ewm(span=mom_period * decay_high_vol).mean()

    # Low volatility regime: slower decay (smoothing)
    decay_low = ret.ewm(span=mom_period * (1 + decay_low_vol)).mean()

    # Middle regime: blend of both
    decay_middle = ret.ewm(span=mom_period).mean()

    # Step 6: Combine based on regime
    regime_signal = pd.Series(index=ret.index, dtype=float)
    regime_signal = high_vol_mask * decay_high + low_vol_mask * decay_low + middle_mask * decay_middle

    # Step 7: Volume filtering — only include stocks with sufficient liquidity
    vol_avg = volume.rolling(20).mean()
    vol_pct_rank = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct_rank > vol_filter_pct  # True = acceptable liquidity

    # Apply volume filter
    signal = regime_signal * vol_filter.astype(float)

    # Step 8: Rank within each date for cross-sectional consistency
    signal_final = signal.groupby(level="datetime").rank(pct=True) * 2 - 1  # Normalize to [-1, 1]

    return signal_final
