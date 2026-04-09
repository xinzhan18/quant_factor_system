"""
TsSkew Rank — Rolling Skewness of Returns

Mechanism:
1. Compute daily returns per stock
2. Compute 60d rolling skewness of returns (per-stock, time-series)
3. EWM smoothing
4. Volume filter
5. Cross-sectional rank

Hypothesis: Skewness measures asymmetry of return distribution.
Negative skew (left tail) indicates crash risk → mean reversion.
Positive skew (right tail) indicates momentum potential.
60d window balances structural signal vs microstructure noise.
"""

import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Parameters:
    -----------
    df : pd.DataFrame with columns [open, high, low, close, volume, amount]
    params : dict with optional keys:
        - skew_period: int (default 60) — rolling skewness lookback
        - ewm_span: int (default 10) — smoothing span
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    skew_period = params.get("skew_period", 60)
    ewm_span = params.get("ewm_span", 10)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    volume = df["volume"]

    # Step 1: Daily returns per stock
    ret = close.pct_change()

    # Step 2: Per-stock rolling skewness
    rolling_skew = ret.rolling(skew_period, min_periods=skew_period // 2).skew()

    # Step 3: EWM smoothing
    signal_smooth = rolling_skew.groupby(level="instrument").transform(
        lambda x: x.ewm(span=ewm_span).mean()
    )

    # Step 4: Volume filter
    vol_avg = volume.rolling(20).mean()
    vol_pct_rank = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct_rank > vol_filter_pct

    # Apply volume filter
    signal = signal_smooth * vol_filter.astype(float)

    # Step 5: Cross-sectional rank
    signal = signal.groupby(level="datetime").rank(pct=True) * 2 - 1

    return signal
