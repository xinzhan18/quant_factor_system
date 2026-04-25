"""Account — cash + positions with strict A-share T+1 settlement.

Two key invariants that drive the data model:

1. **T+1 share lock**: shares purchased on date ``T`` are not sellable until ``T+1``.
   Each :class:`Position` carries a ``locked_until`` date; :meth:`available_shares`
   returns ``shares`` only when ``exec_date >= locked_until``.

2. **T+1 cash settlement**: proceeds from a sell on date ``T`` enter
   :attr:`pending_cash` and become spendable on ``T+1`` after :meth:`settle_cash`
   has been called. Forced liquidations of delisted positions
   (``reason='delisted_writeoff'``) bypass T+1 because there is no real
   counterparty — the cash credit is a pure accounting adjustment.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

import pandas as pd


WRITEOFF_REASONS = frozenset({"delisted_writeoff"})


@dataclass
class Position:
    symbol: str
    shares: int = 0
    locked_until: date | None = None
    avg_cost: float = 0.0
    last_close: float = 0.0


@dataclass(frozen=True)
class Fill:
    side: Literal["buy", "sell"]
    date: date
    symbol: str
    shares: int
    fill_price: float
    cost_cny: float
    reason: str


class Account:
    def __init__(self, initial_capital: float):
        self._cash: float = float(initial_capital)
        self._pending: dict[date, float] = defaultdict(float)
        self._positions: dict[str, Position] = {}

    @property
    def cash(self) -> float:
        return self._cash

    @property
    def pending_cash(self) -> float:
        return sum(self._pending.values())

    def settle_cash(self, on_date: date) -> None:
        """Release pending cash from sells executed on dates strictly < ``on_date``."""
        ready = [d for d in self._pending if d < on_date]
        for d in ready:
            self._cash += self._pending.pop(d)

    def held_symbols(self) -> set[str]:
        return {s for s, p in self._positions.items() if p.shares > 0}

    def available_shares(self, sym: str, exec_date: date) -> int:
        p = self._positions.get(sym)
        if p is None or p.shares == 0:
            return 0
        if p.locked_until is not None and exec_date < p.locked_until:
            return 0
        return p.shares

    def transact(self, fill: Fill) -> None:
        """Apply a fill. ``shares == 0`` (e.g. blocked log entries) is a no-op."""
        if fill.shares == 0:
            return
        p = self._positions.setdefault(fill.symbol, Position(symbol=fill.symbol))
        if fill.side == "buy":
            new_total = p.shares + fill.shares
            p.avg_cost = (
                p.avg_cost * p.shares + fill.fill_price * fill.shares
            ) / max(new_total, 1)
            p.shares = new_total
            # T+1 lock: not sellable until next calendar day at the earliest.
            # Engine clears the lock naturally via subsequent settle_cash + available_shares
            # checks on real trading days.
            p.locked_until = fill.date + timedelta(days=1)
            self._cash -= fill.fill_price * fill.shares + fill.cost_cny
        else:  # sell
            if fill.shares > p.shares:
                raise ValueError(
                    f"sell exceeds holdings: {fill.shares} > {p.shares} for {fill.symbol}"
                )
            p.shares -= fill.shares
            proceeds = fill.fill_price * fill.shares - fill.cost_cny
            if fill.reason in WRITEOFF_REASONS:
                # Pure accounting writeoff; no real settlement.
                self._cash += proceeds
            else:
                self._pending[fill.date] += proceeds
            if p.shares == 0:
                p.locked_until = None
                p.avg_cost = 0.0

    def mark_to_market(self, dt: date, prices: pd.Series) -> float:
        for sym, p in self._positions.items():
            if sym in prices.index and pd.notna(prices.loc[sym]):
                p.last_close = float(prices.loc[sym])
        holdings = sum(p.shares * p.last_close for p in self._positions.values())
        return self._cash + self.pending_cash + holdings

    def positions_snapshot(self, dt: date) -> pd.DataFrame:
        rows = [
            dict(
                date=dt,
                symbol=s,
                shares=p.shares,
                locked_until=p.locked_until,
                avg_cost=p.avg_cost,
                last_close=p.last_close,
                mkt_value=p.shares * p.last_close,
            )
            for s, p in self._positions.items()
            if p.shares > 0
        ]
        return pd.DataFrame(rows)
