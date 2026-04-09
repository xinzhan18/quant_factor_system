"""
TsKurtosis Unconditional — Long-Window Rolling Kurtosis of Returns

Mechanism:
1. Compute daily returns per stock
2. Compute 120d rolling kurtosis of returns (per-stock, time-series)
3. EWM smoothing
4. Volume filter
5. Cross-sectional rank

Hypothesis: 120d kurtosis measures tail risk over a longer horizon.
Unlike 60d kurtosis (batch_086 C001 failed), 120d captures
structural tail risk rather than transient microstructure noise.
Should be orthogonal to str_1m (1-month reversal).
"""

import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Parameters:
    -----------
    df : pd.DataFrame with columns [open, high, low, close, volume, amount]
    params : dict with optional keys:
        - kurt_period: int (default 120) — rolling kurtosis lookback
        - ewm_span: int (default 10) — smoothing span
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    kurt_period = params.get("kurt_period", 120)
    ewm_span = params.get("ewm_span", 10)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    volume = df["volume"]

    # Step 1: Daily returns per stock
    ret = close.pct_change()

    # Step 2: Per-stock rolling kurtosis at LONG window (120d)
    rolling_kurt = ret.rolling(kurt_period, min_periods=kurt_period // 2).kurt()

    # Step 3: EWM smoothing
    signal_smooth = rolling_kurt.groupby(level="instrument").transform(
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
