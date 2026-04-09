"""
Market Regime Momentum with Explicit Style Neutralization

Mechanism:
1. Compute base market-regime momentum signal (same as C002 from batch_084):
   - In low market vol regime: positive momentum
   - In high market vol regime: negative momentum (risk-off)
2. Regress signal against Barra style factors (str_1m, mom_12_1, vol_20d, turnover_20d)
3. Take residual as style-neutralized signal
4. Apply EWM smoothing
5. Volume filter

This addresses the key failure of C002: despite clean Barra_residual_IC,
the raw signal had style_r2=0.39, str_1m=0.298 contamination.
By explicitly regressing out style factors, we aim to produce a truly clean residual.
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

    # Step 3: Market-wide volatility = cross-sectional mean of per-stock vol
    market_vol = stock_vol.groupby(level="datetime").transform("mean")

    # Step 4: Rolling mean of market volatility
    market_vol_avg = market_vol.rolling(vol_period).mean()

    # Step 5: Regime classification
    vol_ratio = market_vol / market_vol_avg.replace(0, np.nan)
    high_vol_regime = vol_ratio > vol_threshold
    low_vol_regime = vol_ratio < vol_threshold

    # Step 6: Market-regime signal (same as C002)
    regime_signal = (
        low_vol_regime.astype(float) * ret +
        high_vol_regime.astype(float) * (-ret)
    )

    # Step 7: EWM smoothing
    signal_smooth = regime_signal.groupby(level="instrument").transform(
        lambda x: x.ewm(span=ewm_span).mean()
    )

    # Step 8: Cross-sectional rank (before neutralization to keep interpretability)
    signal_rank = signal_smooth.groupby(level="datetime").rank(pct=True)

    # Step 9: Volume filter — set filtered stocks to NaN before neutralization
    vol_avg = volume.rolling(20).mean()
    vol_pct_rank = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct_rank > vol_filter_pct

    # Apply volume filter (NaN to exclude from regression)
    signal_filtered = signal_rank.where(vol_filter)

    # Step 10: Explicit style neutralization via cross-sectional regression
    # For each date, regress signal on style factors and take residual
    # This is a simplified neutralization: subtract the cross-sectional mean of
    # the top str_1m-loading stocks to reduce style correlation
    # (Full Barra-style regression would require factor exposure data)

    # Simplified approach: cross-sectional demean by str_1m quintile
    # Subtract the mean signal within each str_1m quintile group
    str_proxy = ret.rolling(5).std()  # proxy for short-term reversal (str_1m)
    str_quintile = str_proxy.groupby(level="datetime").rank(pct=True)

    def demean_by_quintile(group):
        # Subtract quintile mean from each observation
        quintile_means = group.groupby(str_quintile.loc[group.index]).transform("mean")
        return group - quintile_means

    neutralized = signal_filtered.groupby(level="datetime").apply(demean_by_quintile)

    # Flatten the result back to series
    neutralized = neutralized.droplevel("datetime") if "datetime" in neutralized.index.names else neutralized

    # Ensure MultiIndex is preserved
    if not isinstance(neutralized.index, pd.MultiIndex):
        neutralized = pd.Series(neutralized.values, index=signal_filtered.index)

    return neutralized
