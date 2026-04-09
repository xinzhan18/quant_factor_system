"""
TsSkew 120d × Liquidity — Skewness Conditioned on Amount Rank

Mechanism:
1. Compute daily returns per stock
2. Compute 120d rolling skewness (per-stock, time-series)
3. Cross-sectional rank of volume/amount (liquidity measure)
4. Condition skewness signal on liquidity level (high liquidity stocks)
5. EWM smoothing
6. Volume filter (additional)
7. Final cross-sectional rank

Hypothesis: 60d skewness was a pure reversal signal (IC=-0.023, absorbed by turnover_20d).
Conditioning on liquidity (CsRank of amount) may isolate skewness from turnover effects.
120d window captures longer-horizon return asymmetry.
"""

import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Parameters:
    -----------
    df : pd.DataFrame with columns [open, high, low, close, volume, amount]
    params : dict with optional keys:
        - skew_period: int (default 120) — rolling skewness lookback
        - liq_filter_pct: float (default 0.50) — minimum liquidity percentile
        - ewm_span: int (default 10) — smoothing span
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    skew_period = params.get("skew_period", 120)
    liq_filter_pct = params.get("liq_filter_pct", 0.50)
    ewm_span = params.get("ewm_span", 10)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    volume = df["volume"]
    amount = df["amount"]

    # Step 1: Daily returns per stock
    ret = close.pct_change()

    # Step 2: Per-stock rolling skewness at extended window (120d)
    rolling_skew = ret.rolling(skew_period, min_periods=skew_period // 3).skew()

    # Step 3: Liquidity filter — amount percentile
    amt_avg = amount.rolling(20).mean()
    amt_pct_rank = amt_avg.groupby(level="datetime").rank(pct=True)
    liq_filter = amt_pct_rank > liq_filter_pct

    # Step 4: Apply liquidity filter to skewness
    filtered_skew = rolling_skew * liq_filter.astype(float)

    # Step 5: EWM smoothing
    signal_smooth = filtered_skew.groupby(level="instrument").transform(
        lambda x: x.ewm(span=ewm_span).mean()
    )

    # Step 6: Volume filter (additional)
    vol_avg = volume.rolling(20).mean()
    vol_pct_rank = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct_rank > vol_filter_pct

    # Apply volume filter
    signal = signal_smooth * vol_filter.astype(float)

    # Step 7: Cross-sectional rank
    signal = signal.groupby(level="datetime").rank(pct=True) * 2 - 1

    return signal
