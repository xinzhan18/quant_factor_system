"""
Momentum Continuation — Autocorrelation of Returns within Vol Regime

Mechanism:
1. Compute daily returns
2. Compute TsCorr of returns with lagged returns (autocorrelation at lag=1)
   — measures whether today's return predicts tomorrow's (momentum vs mean-reversion)
3. Filter by low vol regime (keep only momentum-period stocks)
4. EWM smoothing
5. Volume filter
6. Cross-sectional rank

Hypothesis: In low-vol regime, stocks with positive autocorrelation (momentum continuation)
are different from str_1m reversal stocks. Autocorrelation is a time-series property,
not a cross-sectional ranking of returns. This should be orthogonal to str_1m.
"""

import numpy as np
import pandas as pd


def compute(df: pd.DataFrame, params: dict) -> pd.Series:
    """
    Parameters:
    -----------
    df : pd.DataFrame with columns [open, high, low, close, volume, amount]
    params : dict with optional keys:
        - mom_period: int (default 20) — momentum lookback for return computation
        - acf_lag: int (default 1) — autocorrelation lag
        - vol_period: int (default 20) — market volatility lookback
        - vol_threshold: float (default 1.0) — market vol ratio threshold
        - ewm_span: int (default 10) — smoothing span
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    mom_period = params.get("mom_period", 20)
    acf_lag = params.get("acf_lag", 1)
    vol_period = params.get("vol_period", 20)
    vol_threshold = params.get("vol_threshold", 1.0)
    ewm_span = params.get("ewm_span", 10)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    volume = df["volume"]

    # Step 1: Daily returns
    ret = close.pct_change()

    # Step 2: Lagged returns for autocorrelation
    ret_lagged = ret.shift(acf_lag)

    # Step 3: Rolling autocorrelation (TsCorr between ret and ret_lagged)
    # Using rolling corr with a window — measures autocorrelation at lag=acf_lag
    autocorr = ret.rolling(mom_period).corr(ret_lagged)

    # Step 4: Market volatility for regime classification
    stock_vol = ret.rolling(vol_period).std()
    market_vol = stock_vol.groupby(level="datetime").transform("mean")
    market_vol_avg = market_vol.rolling(vol_period).mean()
    vol_ratio = market_vol / market_vol_avg.replace(0, np.nan)
    low_vol_regime = vol_ratio < vol_threshold

    # Step 5: Filter by low-vol regime only
    regime_filtered = autocorr * low_vol_regime.astype(float)

    # Step 6: EWM smoothing
    signal_smooth = regime_filtered.groupby(level="instrument").transform(
        lambda x: x.ewm(span=ewm_span).mean()
    )

    # Step 7: Volume filter
    vol_avg = volume.rolling(20).mean()
    vol_pct_rank = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct_rank > vol_filter_pct

    # Apply volume filter
    signal = signal_smooth * vol_filter.astype(float)

    # Step 8: Cross-sectional rank
    signal = signal.groupby(level="datetime").rank(pct=True) * 2 - 1

    return signal
