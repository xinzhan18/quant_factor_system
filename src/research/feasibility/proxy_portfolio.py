"""Build proxy long-short portfolio from a cross-sectional signal.

Per rebalance date
  - rank the signal cross-sectionally among tradable stocks
  - long top ``long_pct`` fraction, short bottom ``short_pct`` fraction
  - equal-weight within each leg
  - return weight DataFrames and turnover Series
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class ProxyPortfolio:
    """Container for proxy portfolio outputs."""

    long_weights: pd.DataFrame
    """Per-date, per-instrument long-leg weight (>=0)."""
    short_weights: pd.DataFrame
    """Per-date, per-instrument short-leg weight (<=0)."""
    abs_weights: pd.DataFrame
    """Absolute weight = |long| + |short|."""
    turnover: pd.Series
    """Per-date two-sided turnover."""


def build_proxy_portfolio(
    signal: pd.DataFrame,
    tradable_mask: pd.DataFrame,
    *,
    long_pct: float = 0.20,
    short_pct: float = 0.20,
) -> ProxyPortfolio:
    """Construct equal-weight long-short proxy portfolio.

    Parameters
    ----------
    signal : DataFrame
        MultiIndex (datetime, instrument) with a single value column.
    tradable_mask : DataFrame
        Same index as *signal*.  Truthy where the stock is tradable.
    long_pct, short_pct : float
        Fraction of the tradable universe for each leg.

    Returns
    -------
    ProxyPortfolio
    """
    sig_col = signal.columns[0]
    mask_col = tradable_mask.columns[0]

    df = pd.DataFrame(
        {
            "signal": signal[sig_col],
            "tradable": tradable_mask[mask_col].astype(bool),
        }
    )

    df = df[df["tradable"] & df["signal"].notna()].copy()

    def _assign_weights(group: pd.DataFrame) -> pd.DataFrame:
        n = len(group)
        if n < 2:
            group["long_w"] = 0.0
            group["short_w"] = 0.0
            return group

        ranks = group["signal"].rank(method="first")
        n_long = max(int(np.floor(n * long_pct)), 1)
        n_short = max(int(np.floor(n * short_pct)), 1)

        long_flag = ranks > (n - n_long)
        short_flag = ranks <= n_short

        group["long_w"] = np.where(long_flag, 1.0 / n_long, 0.0)
        group["short_w"] = np.where(short_flag, -1.0 / n_short, 0.0)
        return group

    df["long_w"] = 0.0
    df["short_w"] = 0.0
    df = df.groupby(level=0, group_keys=False).apply(_assign_weights)

    long_weights = df[["long_w"]].rename(columns={"long_w": "weight"})
    short_weights = df[["short_w"]].rename(columns={"short_w": "weight"})
    abs_weights = pd.DataFrame(
        {"weight": df["long_w"].abs() + df["short_w"].abs()},
        index=df.index,
    )

    # Turnover: sum of absolute weight changes between consecutive dates
    dates = sorted(abs_weights.index.get_level_values(0).unique())
    turnover_vals = {}
    prev_total = None
    for dt in dates:
        cur = (long_weights.loc[dt, "weight"] + short_weights.loc[dt, "weight"])
        if prev_total is not None:
            combined = prev_total.reindex(cur.index.union(prev_total.index), fill_value=0.0)
            cur_aligned = cur.reindex(combined.index, fill_value=0.0)
            turnover_vals[dt] = (cur_aligned - combined).abs().sum()
        else:
            # First date — full investment counts as turnover
            turnover_vals[dt] = cur.abs().sum()
        prev_total = cur

    turnover = pd.Series(turnover_vals, name="turnover")
    turnover.index.name = "datetime"

    return ProxyPortfolio(
        long_weights=long_weights,
        short_weights=short_weights,
        abs_weights=abs_weights,
        turnover=turnover,
    )
