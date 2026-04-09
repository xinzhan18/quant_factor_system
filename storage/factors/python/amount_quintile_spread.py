"""
Amount Sentiment Duration — Quintile Spread with Regime Adaptation

Mechanism:
1. Compute 5-day amount momentum (pct change in amount)
2. Compute amount volatility (rolling std)
3. Compute quintile spread: mean(signal in Q5) - mean(signal in Q1)
4. Apply time decay to emphasize recent quintile spreads
5. Use volume as a liquidity filter

This captures: smart money accumulation over multiple days, with regime-aware weighting.
"""

import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Parameters:
    -----------
    df : pd.DataFrame with columns [open, high, low, close, volume, amount]
    params : dict with optional keys:
        - mom_period: int (default 5)
        - vol_period: int (default 10)
        - decay_span: int (default 10) — EWM span for time decay
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    mom_period = params.get("mom_period", 5)
    vol_period = params.get("vol_period", 10)
    decay_span = params.get("decay_span", 10)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    amount = df["amount"]
    volume = df["volume"]

    # Step 1: Amount momentum (5d)
    amt_mom = amount.pct_change(mom_period)

    # Step 2: Amount volatility (10d rolling std)
    amt_vol = amt_mom.rolling(vol_period).std()

    # Step 3: Normalize momentum by volatility (return per unit risk)
    risk_adjusted = amt_mom / amt_vol.replace(0, np.nan)

    # Step 4: Cross-sectional quintile rank
    quintile_rank = risk_adjusted.groupby(level="datetime").rank(pct=True)

    # Step 5: Compute quintile spread
    # For each date, compute mean signal in Q5 and Q1
    def quintile_spread(group):
        q5 = group[group >= 0.8].mean()  # Top 20%
        q1 = group[group <= 0.2].mean()  # Bottom 20%
        return q5 - q1

    spread = risk_adjusted.groupby(level="datetime").apply(quintile_spread)

    # Step 6: Apply time decay to emphasize recent spreads
    # Use EWM with span=10 to weight recent observations more
    spread_ewm = spread.ewm(span=decay_span).mean()

    # Step 7: Broadcast spread back to instrument level
    # spread_ewm is a Series indexed by datetime only; we need to align it
    # Create a DataFrame aligned with the original index
    dates = risk_adjusted.index.get_level_values("datetime").unique()
    spread_aligned = pd.Series(
        index=risk_adjusted.index,
        dtype=float
    )
    for date in dates:
        mask = risk_adjusted.index.get_level_values("datetime") == date
        spread_aligned.loc[mask] = spread_ewm.loc[date]

    # Step 8: Volume filter — only include stocks with sufficient liquidity
    vol_avg = volume.rolling(20).mean()
    vol_pct = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct > vol_filter_pct

    # Apply volume filter
    signal = spread_aligned * vol_filter.astype(float)

    return signal
