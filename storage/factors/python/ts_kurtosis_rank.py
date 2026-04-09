"""
TsKurtosis Rank — Rolling Kurtosis of Returns in Low-Vol Regime

Mechanism:
1. Compute per-stock rolling kurtosis of daily returns (time-series, NOT cross-sectional)
2. Filter by low vol regime (exclude high-vol periods)
3. EWM smoothing
4. Volume filter
5. Cross-sectional rank

Hypothesis: Kurtosis is truly intertemporal — measures tail risk per stock over time.
Cross-sectional ranking of kurtosis should NOT be absorbed by str_1m
because kurtosis and short-term reversal are orthogonal mechanisms.
"""

import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Parameters:
    -----------
    df : pd.DataFrame with columns [open, high, low, close, volume, amount]
    params : dict with optional keys:
        - kurt_period: int (default 60) — rolling kurtosis lookback
        - vol_period: int (default 20) — market volatility lookback
        - vol_threshold: float (default 1.0) — market vol ratio threshold
        - ewm_span: int (default 10) — smoothing span
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    kurt_period = params.get("kurt_period", 60)
    vol_period = params.get("vol_period", 20)
    vol_threshold = params.get("vol_threshold", 1.0)
    ewm_span = params.get("ewm_span", 10)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    volume = df["volume"]

    # Step 1: Daily returns per stock
    ret = close.pct_change()

    # Step 2: Per-stock rolling kurtosis (truly time-series, per-stock)
    # min_periods=kurt_period//2 to require enough data
    rolling_kurt = ret.rolling(kurt_period, min_periods=kurt_period // 2).kurt()

    # Step 3: Market volatility for regime classification
    stock_vol = ret.rolling(vol_period).std()
    market_vol = stock_vol.groupby(level="datetime").transform("mean")
    market_vol_avg = market_vol.rolling(vol_period).mean()
    vol_ratio = market_vol / market_vol_avg.replace(0, np.nan)
    low_vol_regime = vol_ratio < vol_threshold

    # Step 4: Filter by low-vol regime only (exclude high-vol periods)
    regime_filtered = rolling_kurt * low_vol_regime.astype(float)

    # Step 5: EWM smoothing
    signal_smooth = regime_filtered.groupby(level="instrument").transform(
        lambda x: x.ewm(span=ewm_span).mean()
    )

    # Step 6: Volume filter
    vol_avg = volume.rolling(20).mean()
    vol_pct_rank = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct_rank > vol_filter_pct

    # Apply volume filter
    signal = signal_smooth * vol_filter.astype(float)

    # Step 7: Cross-sectional rank
    signal = signal.groupby(level="datetime").rank(pct=True) * 2 - 1

    return signal
