"""
PE-Conditioned Covariance — Quality-Gated Price-Volume Co-movement

Mechanism:
1. Compute 20d Covariance between close and amount
2. Condition on PE ratio: only long stocks with PE in bottom 50% of universe
3. This implements "quality gate" — only capture covariance signal from undervalued stocks
4. Apply EWM smoothing
5. Volume filter

This is the same mechanism as DSL Cov($close, $amount, 20) but with a PE quality gate
that DSL cannot express (would require nested If or Masking).

The hypothesis: Cov captures price-volume co-movement (smart money), but the signal
is cleaner when restricted to lower-PE stocks (fundamental quality filter).
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
        - pe_filter_pct: float (default 0.50) — maximum PE percentile to include
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    cov_period = params.get("cov_period", 20)
    ewm_span = params.get("ewm_span", 10)
    pe_filter_pct = params.get("pe_filter_pct", 0.50)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    amount = df["amount"]
    volume = df["volume"]
    pe_ratio = df["pe_ratio"]

    # Step 1: Compute 20d returns
    ret = close.pct_change(cov_period)
    amt_ret = amount.pct_change(cov_period)

    # Step 2: Compute rolling covariance
    cov = ret.multiply(amt_ret).groupby(level="instrument").transform(
        lambda x: x.ewm(span=cov_period, adjust=False).mean()
    )

    # Step 3: PE quality gate — only keep low-PE stocks
    pe_pct = pe_ratio.groupby(level="datetime").rank(pct=True)
    pe_filter = pe_pct < pe_filter_pct  # True = acceptable valuation

    # Step 4: EWM smoothing
    cov_smooth = cov.groupby(level="instrument").transform(
        lambda x: x.ewm(span=ewm_span).mean()
    )

    # Apply PE filter
    cov_filtered = cov_smooth.where(pe_filter)

    # Step 5: Volume filter
    vol_avg = volume.rolling(20).mean()
    vol_pct_rank = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct_rank > vol_filter_pct

    # Apply volume filter (set to NaN, not zero)
    signal = cov_filtered.where(vol_filter)

    # Cross-sectional rank normalization
    signal = signal.groupby(level="datetime").rank(pct=True) * 2 - 1

    return signal
