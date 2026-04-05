"""FeasibilityEngine — orchestrator for all feasibility proxy checks.

Accepts raw signal plus market data, builds the proxy portfolio once,
then delegates to each metric module.  Returns a flat dict suitable
for embedding in a judge packet.
"""

from __future__ import annotations

import pandas as pd

from research.feasibility.concentration import (
    compute_small_cap_concentration,
    compute_tail_concentration,
)
from research.feasibility.liquidity import compute_liquidity_coverage
from research.feasibility.proxy_portfolio import build_proxy_portfolio
from research.feasibility.stress import (
    compute_half_life,
    compute_holding_period_proxy,
    compute_rebalance_stress,
)


class FeasibilityEngine:
    """Run all feasibility proxy checks on a factor signal.

    Parameters
    ----------
    long_pct, short_pct : float
        Portfolio leg sizes (default 20% each).
    liquidity_window : int
        Rolling window for the liquidity proxy (default 20).
    liquidity_pct : float
        Percentile threshold for the liquid flag (default 0.30).
    tail_top_k : int
        Number of top positions for tail concentration (default 10).
    small_cap_pct : float
        Percentile threshold for small-cap definition (default 0.30).
    """

    def __init__(
        self,
        *,
        long_pct: float = 0.20,
        short_pct: float = 0.20,
        liquidity_window: int = 20,
        liquidity_pct: float = 0.30,
        tail_top_k: int = 10,
        small_cap_pct: float = 0.30,
    ):
        self.long_pct = long_pct
        self.short_pct = short_pct
        self.liquidity_window = liquidity_window
        self.liquidity_pct = liquidity_pct
        self.tail_top_k = tail_top_k
        self.small_cap_pct = small_cap_pct

    def analyze(
        self,
        signal: pd.DataFrame,
        market_cap: pd.DataFrame,
        amount: pd.DataFrame,
        tradable_mask: pd.DataFrame,
    ) -> dict:
        """Run all feasibility checks.

        Parameters
        ----------
        signal : DataFrame
            MultiIndex (datetime, instrument), single value column.
        market_cap : DataFrame
            Same index, single column with market capitalisation.
        amount : DataFrame
            Same index, single column with daily turnover amount.
        tradable_mask : DataFrame
            Same index, boolean column (True = tradable).

        Returns
        -------
        dict
            Flat dict with all feasibility metrics.
        """
        portfolio = build_proxy_portfolio(
            signal,
            tradable_mask,
            long_pct=self.long_pct,
            short_pct=self.short_pct,
        )

        mean_turnover = float(portfolio.turnover.mean())

        lcr = compute_liquidity_coverage(
            portfolio.abs_weights,
            amount,
            window=self.liquidity_window,
            pct=self.liquidity_pct,
        )

        tail = compute_tail_concentration(
            portfolio.abs_weights,
            top_k=self.tail_top_k,
        )

        small_cap = compute_small_cap_concentration(
            portfolio.abs_weights,
            market_cap,
            pct=self.small_cap_pct,
        )

        half_life = compute_half_life(signal)
        holding = compute_holding_period_proxy(half_life)

        stress = compute_rebalance_stress(mean_turnover, tail, lcr)

        # Coverage: fraction of tradable universe with non-NaN signal
        sig_col = signal.columns[0]
        mask_col = tradable_mask.columns[0]
        tradable_count = tradable_mask[mask_col].groupby(level=0).sum()
        valid_count = (
            signal[sig_col]
            .notna()
            .astype(int)
            .multiply(tradable_mask[mask_col].astype(int))
            .groupby(level=0)
            .sum()
        )
        coverage = float((valid_count / tradable_count.clip(lower=1)).mean())

        return {
            "turnover": mean_turnover,
            "coverage": coverage,
            "half_life": half_life,
            "holding_period_proxy": holding,
            "liquidity_coverage_ratio": lcr,
            "tail_trade_concentration": tail,
            "small_cap_concentration": small_cap,
            **stress,
        }
