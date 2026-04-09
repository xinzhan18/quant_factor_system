"""
Momentum Only in Low-Vol Regime — Simplified Market Regime Signal

Mechanism:
1. Compute market-wide volatility (same as batch_084 C002)
2. In low market vol regime: positive momentum (20d return)
3. In high market vol regime: ZERO exposure (not flipped, just excluded)
4. Apply EWM smoothing
5. Volume filter

Hypothesis: The risk-off flip in C002 (high vol → short) may introduce str_1m style.
By simply excluding high-vol regime stocks rather than flipping to short,
the remaining low-vol momentum signal may be cleaner.
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
        - vol_threshold: float (default 1.0) — market vol ratio threshold
        - ewm_span: int (default 10) — smoothing span
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    mom_period = params.get("mom_period", 20)
    vol_period = params.get("vol_period", 20)
    vol_threshold = params.get("vol_threshold", 1.0)
    ewm_span = params.get("ewm_span", 10)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    volume = df["volume"]

    # Step 1: Compute stock returns
    ret = close.pct_change(mom_period)

    # Step 2: Per-stock rolling volatility
    stock_vol = ret.rolling(vol_period).std()

    # Step 3: Market-wide volatility = cross-sectional mean
    market_vol = stock_vol.groupby(level="datetime").transform("mean")

    # Step 4: Rolling mean of market volatility
    market_vol_avg = market_vol.rolling(vol_period).mean()

    # Step 5: Regime classification
    vol_ratio = market_vol / market_vol_avg.replace(0, np.nan)
    low_vol_regime = vol_ratio < vol_threshold

    # Step 6: Signal: only in low-vol regime, zero elsewhere
    regime_signal = ret * low_vol_regime.astype(float)

    # Step 7: EWM smoothing
    signal_smooth = regime_signal.groupby(level="instrument").transform(
        lambda x: x.ewm(span=ewm_span).mean()
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
