"""
Volatility Regime Momentum — Market-Adaptive Signal

Mechanism:
1. Compute market-wide volatility (equal-weighted average of all stocks' 20d return std)
2. Classify market into high/low volatility regimes
3. In high vol regime: reduce position size / flip signal (market crash = risk off)
4. In low vol regime: full signal exposure
5. This is a market-regime-adaptive wrapper around a base momentum signal

The base signal is 20d return. The regime filter modulates exposure based on
market-wide volatility level. This is genuinely different from stock-level
volatility regime (which all failed in batch_082/083).
"""

import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Parameters:
    -----------
    df : pd.DataFrame with columns [open, high, low, close, volume, amount]
    params : dict with optional keys:
        - mom_period: int (default 20) — momentum lookback
        - vol_period: int (default 20) — market volatility lookback
        - vol_threshold: float (default 0.50) — market vol percentile threshold
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    mom_period = params.get("mom_period", 20)
    vol_period = params.get("vol_period", 20)
    vol_threshold = params.get("vol_threshold", 0.50)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    volume = df["volume"]

    # Step 1: Compute stock returns
    ret = close.pct_change(mom_period)

    # Step 2: Per-stock rolling volatility (time-series std within each stock)
    stock_vol = ret.rolling(vol_period).std()

    # Step 3: Market-wide volatility = cross-sectional mean of per-stock vol
    # This scalar changes each date, measuring overall market turbulence
    market_vol = stock_vol.groupby(level="datetime").transform("mean")

    # Step 4: Rolling mean of market volatility (time-series average)
    market_vol_avg = market_vol.rolling(vol_period).mean()

    # Step 5: Regime classification: is today's market_vol above or below its recent average?
    # If ratio > 1: high vol regime (risk-off: flip momentum)
    # If ratio < 1: low vol regime (normal momentum)
    vol_ratio = market_vol / market_vol_avg.replace(0, np.nan)

    # Step 6: Regime classification
    # vol_ratio > vol_threshold (default 1.0) means market vol above recent average → high vol regime
    # vol_ratio is a scalar per date, broadcast to all stocks
    high_vol_regime = vol_ratio > vol_threshold
    low_vol_regime = vol_ratio < vol_threshold

    # Step 6: In high vol regime: flip signal (risk-off)
    # In low vol regime: normal momentum
    # Signal = ret in low vol, = -ret in high vol
    regime_signal = (
        low_vol_regime.astype(float) * ret +
        high_vol_regime.astype(float) * (-ret)
    )

    # Step 7: EWM smoothing
    signal_smooth = regime_signal.groupby(level="instrument").transform(
        lambda x: x.ewm(span=mom_period).mean()
    )

    # Step 8: Volume filter
    vol_avg = volume.rolling(20).mean()
    vol_pct_rank = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct_rank > vol_filter_pct

    # Apply volume filter
    signal = signal_smooth * vol_filter.astype(float)

    # Cross-sectional rank
    signal = signal.groupby(level="datetime").rank(pct=True) * 2 - 1

    return signal
