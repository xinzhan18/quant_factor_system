"""TradeCalendar — trading days, csi1000 dynamic universe, rebalance schedule.

Two construction paths:
- :meth:`from_db` reads from TimescaleDB (production).
- :meth:`from_data` accepts pre-built mappings (tests / offline).

The csi1000 ``index_constituents`` table stores point-in-time daily membership
rows ``(time, symbol, index_name)`` — one row per (date, symbol) where ``symbol``
was a member of ``csi1000`` on ``date``. We index that into a ``date → set[str]``
lookup at construction time.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import pandas as pd


def _db_dsn() -> dict:
    return dict(
        host=os.environ.get("TIMESCALE_HOST", "localhost"),
        port=int(os.environ.get("TIMESCALE_PORT", 5432)),
        dbname=os.environ.get("TIMESCALE_DB", "quant_data"),
        user=os.environ.get("TIMESCALE_USER", "postgres"),
        password=os.environ.get("TIMESCALE_PASSWORD", "postgres"),
    )


@dataclass(frozen=True)
class TradeCalendar:
    _trading_days: tuple[date, ...]              # sorted
    _universe_index: dict[date, frozenset[str]]  # date → csi1000 members on that date

    @classmethod
    def from_data(
        cls,
        trading_days: list[date],
        universe_index: dict[date, set[str]],
    ) -> "TradeCalendar":
        td = tuple(sorted(trading_days))
        ui = {d: frozenset(syms) for d, syms in universe_index.items()}
        return cls(_trading_days=td, _universe_index=ui)

    @classmethod
    def from_db(cls, index_name: str = "csi1000") -> "TradeCalendar":
        import psycopg2

        conn = psycopg2.connect(**_db_dsn())
        cur = conn.cursor()
        cur.execute("SELECT DISTINCT time::date FROM market_daily ORDER BY 1")
        td = [r[0] for r in cur.fetchall()]
        cur.execute(
            "SELECT time::date, symbol FROM index_constituents WHERE index_name = %s",
            (index_name,),
        )
        ui: dict[date, set[str]] = {}
        for d, sym in cur.fetchall():
            ui.setdefault(d, set()).add(sym)
        conn.close()
        return cls.from_data(td, ui)

    def trading_days(self, start: date, end: date) -> list[date]:
        return [d for d in self._trading_days if start <= d <= end]

    def add_trading_days(self, base: date, n: int) -> date:
        days = self._trading_days
        if base in days:
            idx = days.index(base)
        else:
            # bisect right: index of first d > base
            lo, hi = 0, len(days)
            while lo < hi:
                mid = (lo + hi) // 2
                if days[mid] <= base:
                    lo = mid + 1
                else:
                    hi = mid
            idx = lo - 1   # last d <= base
        target = idx + n
        if not (0 <= target < len(days)):
            raise IndexError(f"add_trading_days({base},{n}) out of range")
        return days[target]

    def universe_at(self, dt: date) -> set[str]:
        return set(self._universe_index.get(dt, frozenset()))

    def rebalance_schedule(
        self,
        start: date,
        end: date,
        freq_days: int,
        anchor: str | date,
    ) -> list[date]:
        days = self.trading_days(start, end)
        if not days:
            return []
        if anchor == "monday":
            first = next((d for d in days if d.weekday() == 0), days[0])
        elif anchor == "first_trade_day":
            first = days[0]
        elif isinstance(anchor, date):
            first = anchor if anchor in days else days[0]
        else:
            raise ValueError(f"bad anchor: {anchor}")
        first_idx = days.index(first)
        return [days[i] for i in range(first_idx, len(days), freq_days)]
