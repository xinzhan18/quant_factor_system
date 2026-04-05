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

    All inputs: pd.Series with MultiIndex (level order may vary).
    Returns: DataFrame with the same MultiIndex as *close* and 7 columns.
    """
    canonical_index = close.index
    level_names = canonical_index.names  # e.g. ("instrument", "datetime")

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
        # Ensure index level order matches canonical before reindex
        if s.index.names != list(level_names):
            s = s.reorder_levels(level_names)
        s = s.reindex(canonical_index)
        normalized[name] = cross_sectional_normalize(s, sigma=sigma)

    return pd.DataFrame(normalized)


def _compute_size(circ_market_cap: pd.Series) -> pd.Series:
    return np.log(circ_market_cap.where(circ_market_cap > 0))


def _compute_value(pb_ratio: pd.Series) -> pd.Series:
    safe_pb = pb_ratio.where(pb_ratio > 0)
    return 1.0 / safe_pb


def _compute_momentum(close: pd.Series) -> pd.Series:
    """12-1 month momentum: close 21 days ago / close 252 days ago - 1."""
    wide = close.unstack(level="instrument")
    close_21 = wide.shift(21)
    close_252 = wide.shift(252)
    mom = (close_21 / close_252.where(close_252 > 0)) - 1
    return mom.stack(dropna=False)


def _compute_reversal(close: pd.Series) -> pd.Series:
    """1-month return: current close / close 21 days ago - 1."""
    wide = close.unstack(level="instrument")
    close_21 = wide.shift(21)
    rev = (wide / close_21.where(close_21 > 0)) - 1
    return rev.stack(dropna=False)


def _compute_volatility(close: pd.Series) -> pd.Series:
    """20-day realized volatility of daily returns.

    Uses unstack/stack to avoid groupby+rolling index corruption.
    """
    wide = close.unstack(level="instrument")
    ret_wide = wide.pct_change()
    vol_wide = ret_wide.rolling(20, min_periods=10).std()
    return vol_wide.stack(dropna=False)


def _compute_liquidity(turnover_rate: pd.Series) -> pd.Series:
    """20-day mean turnover rate.

    Uses unstack/stack to avoid groupby+rolling index corruption.
    """
    wide = turnover_rate.unstack(level="instrument")
    liq_wide = wide.rolling(20, min_periods=10).mean()
    return liq_wide.stack(dropna=False)


def _compute_earnings_yield(pe_ratio: pd.Series) -> pd.Series:
    safe_pe = pe_ratio.where(pe_ratio > 0)
    return 1.0 / safe_pe
