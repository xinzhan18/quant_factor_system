"""
Dollar Volume Weighted Return — Smart Money Flow Signal

Mechanism:
1. Compute per-stock return
2. For each date, compute amount share = stock_amount / universe_total_amount
3. DVW return = sum over all stocks of (weight_i * return_i)
   But for cross-sectional signal: each stock's DVW contribution = return_i * amount_share_i
   This measures "return per unit of universe attention"
4. Apply EWM smoothing to denoise
5. Volume filter for liquidity

This captures: smart money flow by weighting returns by monetary commitment.
DSL cannot express per-stock cross-sectional normalization by total universe amount.
"""

import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Parameters:
    -----------
    df : pd.DataFrame with columns [open, high, low, close, volume, amount]
    params : dict with optional keys:
        - ret_period: int (default 5) — return lookback
        - ewm_span: int (default 10) — smoothing span
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    ret_period = params.get("ret_period", 5)
    ewm_span = params.get("ewm_span", 10)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    amount = df["amount"]
    volume = df["volume"]

    # Step 1: Compute stock returns
    ret = close.pct_change(ret_period)

    # Step 2: Compute amount share within each date (cross-sectional)
    # Each stock's weight = its amount / sum of all amounts on that date
    date_totals = amount.groupby(level="datetime").transform("sum")
    amount_share = amount / date_totals.replace(0, np.nan)

    # Step 3: DVW return = return * amount_share
    # This is "return per unit of universe monetary attention"
    dvw = ret * amount_share

    # Step 4: EWM smoothing within each instrument
    dvw_smooth = dvw.groupby(level="instrument").transform(
        lambda x: x.ewm(span=ewm_span).mean()
    )

    # Step 5: Volume filter — set filtered stocks to NaN
    vol_avg = volume.rolling(20).mean()
    vol_pct_rank = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct_rank > vol_filter_pct

    # Apply volume filter (set to NaN, not zero, to exclude from ranking)
    dvw_filtered = dvw_smooth.where(vol_filter)

    # Step 6: Cross-sectional rank to normalize — converts tiny values to proper distribution
    signal = dvw_filtered.groupby(level="datetime").rank(pct=True) * 2 - 1

    return signal
