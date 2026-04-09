"""
Market Regime Momentum with Quality Gate

Mechanism:
1. Compute market-regime momentum (same as batch_084 C002):
   - Low market vol: positive momentum
   - High market vol: risk-off (flip signal)
2. Apply quality gate: only include stocks where BOTH:
   - PE rank < 0.50 (cheap stocks — avoids str_1m style trap)
   - Amount rank in 20-80th percentile (avoids micro/mega cap)
3. Apply EWM smoothing
4. Volume filter

This is the direct next probe from batch_084 diagnostics:
market-level regime + PE + turnover双重过滤 → 干净信号.
Python required for the multi-condition quality gate.
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
        - pe_filter_pct: float (default 0.50) — maximum PE percentile
        - amt_low_pct: float (default 0.20) — minimum amount percentile
        - amt_high_pct: float (default 0.80) — maximum amount percentile
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    mom_period = params.get("mom_period", 20)
    vol_period = params.get("vol_period", 20)
    vol_threshold = params.get("vol_threshold", 1.0)
    ewm_span = params.get("ewm_span", 10)
    pe_filter_pct = params.get("pe_filter_pct", 0.50)
    amt_low_pct = params.get("amt_low_pct", 0.20)
    amt_high_pct = params.get("amt_high_pct", 0.80)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    volume = df["volume"]
    amount = df["amount"]

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
    high_vol_regime = vol_ratio > vol_threshold
    low_vol_regime = vol_ratio < vol_threshold

    # Step 6: Market-regime signal
    regime_signal = (
        low_vol_regime.astype(float) * ret +
        high_vol_regime.astype(float) * (-ret)
    )

    # Step 7: EWM smoothing
    signal_smooth = regime_signal.groupby(level="instrument").transform(
        lambda x: x.ewm(span=ewm_span).mean()
    )

    # Step 8: Cross-sectional rank
    signal_rank = signal_smooth.groupby(level="datetime").rank(pct=True) * 2 - 1

    # Step 9: Volume filter
    vol_avg = volume.rolling(20).mean()
    vol_pct_rank = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct_rank > vol_filter_pct

    # Step 10: Amount quality filter (mid-range only)
    amt_pct = amount.groupby(level="datetime").rank(pct=True)
    amt_filter = (amt_pct > amt_low_pct) & (amt_pct < amt_high_pct)

    # Apply quality filters
    signal_filtered = signal_rank.where(vol_filter & amt_filter)

    return signal_filtered
