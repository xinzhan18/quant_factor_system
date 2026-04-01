"""Data preparation utilities for factor report generation.

Merge factor values with price data, compute future returns, and split IS/OOS.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def merge_factor_price(
    factor_df: pd.DataFrame,
    price_df: pd.DataFrame,
    clip_method: str = "mad",
    clip_k: float = 5.0,
    clip_threshold: float = 0.11,
) -> pd.DataFrame:
    """Merge factor values with price data and compute future returns.

    Parameters
    ----------
    factor_df : DataFrame with columns [time, symbol, value]
    price_df : DataFrame with columns [time, symbol, close]
    clip_method : "mad" (median absolute deviation) or "fixed"
    clip_k : MAD multiplier for clipping (used when clip_method="mad")
    clip_threshold : absolute threshold for clipping (used when clip_method="fixed")

    Returns
    -------
    DataFrame with columns [time, symbol, value, future_return].
    NaN future_returns (last date per symbol) are dropped.
    Extreme returns are clipped per clip_method.
    """
    # Merge on time + symbol
    merged = factor_df.merge(price_df, on=["time", "symbol"], how="inner")

    # Compute future return: next-day close / today close - 1
    merged = merged.sort_values(["symbol", "time"]).reset_index(drop=True)
    merged["future_close"] = merged.groupby("symbol")["close"].shift(-1)
    merged["future_return"] = merged["future_close"] / merged["close"] - 1

    # Drop rows with NaN future_return (last date per symbol)
    merged = merged.dropna(subset=["future_return"]).reset_index(drop=True)

    # Clip extreme returns
    if clip_method == "mad":
        median = merged["future_return"].median()
        mad = (merged["future_return"] - median).abs().median()
        if mad > 0:
            lower = median - clip_k * mad
            upper = median + clip_k * mad
            merged["future_return"] = merged["future_return"].clip(lower, upper)
    elif clip_method == "fixed":
        merged["future_return"] = merged["future_return"].clip(
            -clip_threshold, clip_threshold
        )

    # Keep only the needed columns
    merged = merged[["time", "symbol", "value", "future_return"]].copy()
    return merged


def split_is_oos(
    merged_df: pd.DataFrame, split_date
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split merged DataFrame into in-sample and out-of-sample.

    Parameters
    ----------
    merged_df : DataFrame with a 'time' column
    split_date : boundary date; IS = time < split_date, OOS = time >= split_date

    Returns
    -------
    Tuple of (is_df, oos_df).
    """
    is_df = merged_df[merged_df["time"] < split_date].copy()
    oos_df = merged_df[merged_df["time"] >= split_date].copy()
    return is_df, oos_df
