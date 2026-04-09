"""
Rolling Beta Residual — True Idiosyncratic Return

Mechanism:
1. Compute stock returns and equal-weighted market return
2. For each stock, estimate rolling beta using expanding window regression
   beta = Cov(stock_ret, market_ret) / Var(market_ret)
3. Compute residual = stock_ret - beta * market_ret
4. This is the "true" idiosyncratic return after beta adjustment
5. Apply EWM smoothing
6. Volume filter for liquidity

This captures: the portion of stock return NOT explained by market movement,
using a rolling beta that adapts to regime changes. DSL cannot perform
rolling regression (needs explicit loop or pandas rolling regression).

Key difference from batch_082 cross_sectional_residual:
- batch_082 assumed beta=1 for all stocks (gross simplification)
- Here we estimate per-stock rolling beta
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
        - beta_window: int (default 60) — expanding window for beta estimation
        - ewm_span: int (default 10) — smoothing span
        - vol_filter_pct: float (default 0.30) — minimum volume percentile

    Returns:
    --------
    pd.Series with MultiIndex (datetime, instrument)
    """
    ret_period = params.get("ret_period", 5)
    beta_window = params.get("beta_window", 60)
    ewm_span = params.get("ewm_span", 10)
    vol_filter_pct = params.get("vol_filter_pct", 0.30)

    close = df["close"]
    volume = df["volume"]

    # Step 1: Compute stock returns
    ret = close.pct_change(ret_period)

    # Step 2: Compute equal-weighted market return
    market_ret = ret.groupby(level="datetime").transform("mean")

    # Step 3: Compute rolling covariance and variance
    # Using expanding window for beta estimation
    cov = ret.multiply(market_ret).groupby(level="instrument").transform(
        lambda x: x.ewm(span=beta_window, adjust=False).mean()
    )
    var_market = market_ret.pow(2).groupby(level="instrument").transform(
        lambda x: x.ewm(span=beta_window, adjust=False).mean()
    )

    # Step 4: Compute rolling beta = Cov / Var
    beta = cov / var_market.replace(0, np.nan)

    # Step 5: Compute residual return = ret - beta * market_ret
    residual = ret - beta.multiply(market_ret)

    # Step 6: EWM smoothing within each instrument
    residual_smooth = residual.groupby(level="instrument").transform(
        lambda x: x.ewm(span=ewm_span).mean()
    )

    # Step 7: Volume filter
    vol_avg = volume.rolling(20).mean()
    vol_pct_rank = vol_avg.groupby(level="datetime").rank(pct=True)
    vol_filter = vol_pct_rank > vol_filter_pct

    # Apply volume filter
    signal = residual_smooth * vol_filter.astype(float)

    return signal
