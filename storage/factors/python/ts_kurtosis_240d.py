"""
TsKurtosis 240d — Extended Window Rolling Kurtosis

Mechanism:
1. Compute daily returns per stock
2. Compute 240d rolling kurtosis (per-stock, time-series)
3. EWM smoothing
4. Volume filter
5. Cross-sectional rank

Hypothesis: 240d (≈1 year) captures structural tail risk that shorter windows miss.
If 120d kurtosis was signal-free (IC≈0), 240d may capture a different aspect
of return distribution — structural vs transient tail risk.
"""

import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Parameters:
    -----------
    df : pd.DataFrame with columns [open, high, low, close, volume, amount]
    params : dict with optional keys:
        - kurt_period: int (default 240) — rolling kurtosis lookback
        - ewm_span: int (default 10) — smoothing span
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    kurt_period = params.get("kurt_period", 240)
    ewm_span = params.get("ewm_span", 10)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    volume = df["volume"]

    # Step 1: Daily returns per stock
    ret = close.pct_change()

    # Step 2: Per-stock rolling kurtosis at EXTENDED window (240d ≈ 1 year)
    rolling_kurt = ret.rolling(kurt_period, min_periods=kurt_period // 3).kurt()

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
