"""TradabilityMask + ExecutionPolicy.

The mask is the boolean fence between *desired* trades and *actually allowed*
trades. ``can_buy`` checks the buy-side conditions at execution date; ``can_sell``
checks the sell-side conditions plus the account's T+1 share lock.

Limit-up / limit-down detection compares the *open* price against
``prev_close × (1 ± limit_pct − ε)`` (with ε=1e-3 for tick-size noise) — this
matches the spec for ``match_price=open``. The match-price-close path uses the
``limit_up``/``limit_down`` columns directly.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

import pandas as pd

from research.backtest.calendar import TradeCalendar
from research.backtest.config import FilterConfig
from research.backtest.data_view import PriceView
from research.backtest.tradability import TradabilityProvider


LIMIT_DETECTION_EPS = 1e-3


@dataclass(frozen=True)
class ExecutionPolicy:
    blocked_buy: Literal["drop", "carry_over_n_days"] = "drop"
    blocked_sell: Literal["carry_over_n_days"] = "carry_over_n_days"
    blocked_sell_max_carry_days: int = 5
    capital_shortage: Literal["pro_rata", "drop_smallest"] = "pro_rata"
    lot_residual: Literal["floor"] = "floor"
    nan_factor: Literal["exclude_from_pool"] = "exclude_from_pool"


@dataclass(frozen=True)
class TradabilityMask:
    view: PriceView
    provider: TradabilityProvider
    config: FilterConfig
    calendar: TradeCalendar
    match_price: Literal["open", "close"] = "open"

    def _prices(self, exec_date: date, syms: list[str]) -> tuple[pd.Series, pd.Series]:
        """Return (today_open, prev_close) reindexed to syms."""
        df = self.view.slice_eod(exec_date, syms)
        try:
            prev_dt = self.calendar.add_trading_days(exec_date, -1)
            prev = self.view.slice_eod(prev_dt, syms)
            prev_close = prev["close"].reindex(syms).astype(float)
        except (IndexError, KeyError):
            prev_close = pd.Series(float("nan"), index=syms)
        opens = df["open"].reindex(syms).astype(float) if "open" in df.columns else pd.Series(float("nan"), index=syms)
        return opens, prev_close

    def _gapped_up_mask(self, exec_date: date, syms: list[str]) -> pd.Series:
        opens, prev_close = self._prices(exec_date, syms)
        limit_pcts = pd.Series(
            [self.provider.limit_pct(exec_date, s) for s in syms], index=syms
        )
        threshold = prev_close * (1 + limit_pcts - LIMIT_DETECTION_EPS)
        return (opens >= threshold).fillna(False).astype(bool)

    def _gapped_down_mask(self, exec_date: date, syms: list[str]) -> pd.Series:
        opens, prev_close = self._prices(exec_date, syms)
        limit_pcts = pd.Series(
            [self.provider.limit_pct(exec_date, s) for s in syms], index=syms
        )
        threshold = prev_close * (1 - limit_pcts + LIMIT_DETECTION_EPS)
        return (opens <= threshold).fillna(False).astype(bool)

    def can_buy(self, exec_date: date, symbols: list[str]) -> pd.Series:
        syms = list(symbols)
        if not syms:
            return pd.Series(dtype=bool)
        ok = pd.Series(True, index=syms)
        if self.config.block_st:
            ok &= ~self.provider.st_mask(exec_date, syms)
        if self.config.block_suspended:
            ok &= ~self.provider.suspended_mask(exec_date, syms)
        if self.config.block_limit_up_at_buy:
            ok &= ~self._gapped_up_mask(exec_date, syms)
        # newly listed
        newly = pd.Series(
            [
                self.provider.is_newly_listed(exec_date, s, self.config.newly_listed_days)
                for s in syms
            ],
            index=syms,
        )
        ok &= ~newly
        # cooldown after unsuspend
        if self.config.cooldown_days_after_unsuspend > 0:
            try:
                prev_dt = self.calendar.add_trading_days(exec_date, -1)
                was_suspended = self.provider.suspended_mask(prev_dt, syms)
                today_suspended = self.provider.suspended_mask(exec_date, syms)
                cooldown = was_suspended & ~today_suspended
                ok &= ~cooldown
            except (IndexError, KeyError):
                pass
        return ok

    def can_sell(
        self, exec_date: date, symbols: list[str], account
    ) -> pd.Series:
        syms = list(symbols)
        if not syms:
            return pd.Series(dtype=bool)
        ok = pd.Series(True, index=syms)
        if self.config.block_suspended:
            ok &= ~self.provider.suspended_mask(exec_date, syms)
        if self.config.block_limit_down_at_sell:
            ok &= ~self._gapped_down_mask(exec_date, syms)
        # T+1 share lock from account
        if account is not None:
            t1_locked = pd.Series(
                [account.available_shares(s, exec_date) == 0 for s in syms],
                index=syms,
            )
            ok &= ~t1_locked
        return ok
