"""
Quality-Conditioned Covariance — Amount-Level-Gated Price-Volume Co-movement

Mechanism:
1. Compute 20d Covariance between close and amount
2. Condition on amount level: only include stocks with amount in middle 10-90th percentile
   (avoids micro-cap and mega-cap)
3. Apply EWM smoothing
4. Volume filter

The mechanism is the same as DSL Cov($close, $amount, 20) but with amount-level gating
that DSL cannot express for individual stocks (would require Masking/conditional).
"""

import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Parameters:
    -----------
    df : pd.DataFrame with columns [open, high, low, close, volume, amount]
    params : dict with optional keys:
        - cov_period: int (default 20) — covariance lookback
        - ewm_span: int (default 10) — smoothing span
        - amt_low_pct: float (default 0.10) — minimum amount percentile to include
        - amt_high_pct: float (default 0.90) — maximum amount percentile to include
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    cov_period = params.get("cov_period", 20)
    ewm_span = params.get("ewm_span", 10)
    amt_low_pct = params.get("amt_low_pct", 0.10)
    amt_high_pct = params.get("amt_high_pct", 0.90)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    amount = df["amount"]
    volume = df["volume"]

    # Step 1: Compute 20d returns
    ret = close.pct_change(cov_period)
    amt_ret = amount.pct_change(cov_period)

    # Step 2: Compute rolling covariance between close and amount returns
    cov = ret.multiply(amt_ret).groupby(level="instrument").transform(
        lambda x: x.ewm(span=cov_period, adjust=False).mean()
    )

    # Step 3: Amount level quality gate — only keep mid-range amount stocks
    # Avoids micro-cap (too illiquid) and mega-cap (too institutional)
    amt_pct = amount.groupby(level="datetime").rank(pct=True)
    amt_filter = (amt_pct > amt_low_pct) & (amt_pct < amt_high_pct)

    # Step 4: EWM smoothing
    cov_smooth = cov.groupby(level="instrument").transform(
        lambda x: x.ewm(span=ewm_span).mean()
    )

    # Apply quality filter
    cov_filtered = cov_smooth.where(amt_filter)

    # Step 5: Volume filter
    vol_avg = volume.rolling(20).mean()
    vol_pct_rank = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct_rank > vol_filter_pct

    # Apply volume filter
    signal = cov_filtered.where(vol_filter)

    # Cross-sectional rank normalization
    signal = signal.groupby(level="datetime").rank(pct=True) * 2 - 1

    return signal
