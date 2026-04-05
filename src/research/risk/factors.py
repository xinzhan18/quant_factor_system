"""7-factor Barra-like style model for A-share market.

Pure functions. No I/O, no Qlib. All computation vectorized via groupby.
Each _compute_* returns a Series with the same (datetime, instrument) MultiIndex.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .constants import STYLE_NAMES
from .normalization import cross_sectional_normalize


def compute_style_factor_matrix(
    close: pd.Series,
    circ_market_cap: pd.Series,
    pb_ratio: pd.Series,
    pe_ratio: pd.Series,
    turnover_rate: pd.Series,
    sigma: float = 3.0,
) -> pd.DataFrame:
    """Compute all 7 style factors, each cross-sectionally normalized.

    All inputs: pd.Series with (datetime, instrument) MultiIndex.
    Returns: DataFrame with (datetime, instrument) MultiIndex and 7 columns.
    """
    raw = {
        "log_circ_cap": _compute_size(circ_market_cap),
        "book_to_price": _compute_value(pb_ratio),
        "mom_12_1": _compute_momentum(close),
        "str_1m": _compute_reversal(close),
        "vol_20d": _compute_volatility(close),
        "turnover_20d": _compute_liquidity(turnover_rate),
        "ep_ratio": _compute_earnings_yield(pe_ratio),
    }

    normalized = {}
    for name in STYLE_NAMES:
        s = raw[name]
        normalized[name] = cross_sectional_normalize(s, sigma=sigma)

    return pd.DataFrame(normalized)


def _compute_size(circ_market_cap: pd.Series) -> pd.Series:
    return np.log(circ_market_cap.where(circ_market_cap > 0))


def _compute_value(pb_ratio: pd.Series) -> pd.Series:
    safe_pb = pb_ratio.where(pb_ratio > 0)
    return 1.0 / safe_pb


def _compute_momentum(close: pd.Series) -> pd.Series:
    """12-1 month momentum: close 21 days ago / close 252 days ago - 1."""
    close_21 = close.groupby(level="instrument").shift(21)
    close_252 = close.groupby(level="instrument").shift(252)
    return (close_21 / close_252.where(close_252 > 0)) - 1


def _compute_reversal(close: pd.Series) -> pd.Series:
    """1-month return: current close / close 21 days ago - 1."""
    close_21 = close.groupby(level="instrument").shift(21)
    return (close / close_21.where(close_21 > 0)) - 1


def _compute_volatility(close: pd.Series) -> pd.Series:
    """20-day realized volatility of daily returns."""
    daily_ret = close.groupby(level="instrument").pct_change()
    vol = daily_ret.groupby(level="instrument").rolling(
        20, min_periods=10
    ).std()
    # rolling adds an extra level; drop it
    if vol.index.nlevels > 2:
        vol = vol.droplevel(0)
    return vol


def _compute_liquidity(turnover_rate: pd.Series) -> pd.Series:
    """20-day mean turnover rate."""
    liq = turnover_rate.groupby(level="instrument").rolling(
        20, min_periods=10
    ).mean()
    if liq.index.nlevels > 2:
        liq = liq.droplevel(0)
    return liq


def _compute_earnings_yield(pe_ratio: pd.Series) -> pd.Series:
    safe_pe = pe_ratio.where(pe_ratio > 0)
    return 1.0 / safe_pe
