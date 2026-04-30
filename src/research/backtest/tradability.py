"""TradabilityProvider — PIT facts about stock tradability.

Sources:
- ``instrument_st_status`` table (synced via ``scripts/sync_st_status.py``) —
  point-in-time ST flag.
- ``instrument_lifecycle`` table (synced via
  ``scripts/sync_instrument_lifecycle.py``) — listing/delisting dates + board.
- :class:`PriceView` — for the ``volume==0 OR amount==0`` suspended proxy.

Two construction paths:
- :meth:`from_db` reads the production tables.
- :meth:`from_data` accepts pre-built DataFrames (tests / offline).

Limit-pct schedule (resolved via :meth:`limit_pct`):
- ST: ±5% regardless of board
- ChiNext (SZ300xxx) / STAR (SH688xxx): ±10% before 2020-08-24, ±20% after
- Beijing Stock Exchange (BJ4xxxxx / BJ8xxxxx): ±30%
- Main board (everything else): ±10%
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date

import pandas as pd

from research.backtest.data_view import PriceView


CHINEXT_LIMIT_REGIME_CHANGE = date(2020, 8, 24)


def _db_dsn() -> dict:
    return dict(
        host=os.environ.get("TIMESCALE_HOST", "localhost"),
        port=int(os.environ.get("TIMESCALE_PORT", 5432)),
        dbname=os.environ.get("TIMESCALE_DB", "quant_data"),
        user=os.environ.get("TIMESCALE_USER", "postgres"),
        password=os.environ.get("TIMESCALE_PASSWORD", "postgres"),
    )


def _board_of_symbol(sym: str) -> str:
    if sym.startswith("SH688"):
        return "star"
    if sym.startswith("SZ300"):
        return "chinext"
    if sym.startswith("BJ8") or sym.startswith("BJ4"):
        return "bse"
    return "main"


@dataclass(frozen=True)
class TradabilityProvider:
    _st: pd.DataFrame              # MultiIndex (datetime, instrument), col is_st
    _lifecycle: pd.DataFrame       # index=instrument, cols listing_date / delisting_date / board
    _price_view: PriceView | None

    @classmethod
    def from_data(
        cls,
        st_table: pd.DataFrame,
        lifecycle_table: pd.DataFrame,
        price_view: PriceView | None = None,
    ) -> "TradabilityProvider":
        """``st_table`` indexed by (datetime, instrument) with column ``is_st`` (bool).
        ``lifecycle_table`` indexed by ``instrument`` with cols
        ``listing_date``/``delisting_date``/``board``."""
        return cls(_st=st_table, _lifecycle=lifecycle_table, _price_view=price_view)

    @classmethod
    def from_db(
        cls,
        price_view: PriceView | None = None,
        allow_missing_tables: bool = False,
    ) -> "TradabilityProvider":
        """Load ST + lifecycle tables from TimescaleDB.

        If ``allow_missing_tables`` is True, missing tables are silently
        replaced with empty frames — useful for development before
        ``scripts/sync_st_status.py`` / ``sync_instrument_lifecycle.py``
        have been run. The caller must also disable corresponding filter
        flags (``block_st``, ``newly_listed_days``) or it will be a no-op.
        """
        import psycopg2

        empty_st = pd.DataFrame(
            {"is_st": []},
            index=pd.MultiIndex.from_tuples(
                [], names=["datetime", "instrument"]
            ),
        )
        empty_lc = pd.DataFrame(
            columns=["listing_date", "delisting_date", "board"]
        )

        conn = psycopg2.connect(**_db_dsn())
        try:
            st = pd.read_sql(
                "SELECT datetime, instrument, is_st FROM instrument_st_status",
                conn,
            )
            st["datetime"] = pd.to_datetime(st["datetime"])
            st = st.set_index(["datetime", "instrument"])
        except Exception:
            if not allow_missing_tables:
                conn.close()
                raise
            st = empty_st
        try:
            lc = pd.read_sql(
                "SELECT instrument, listing_date, delisting_date, board "
                "FROM instrument_lifecycle",
                conn,
                index_col="instrument",
            )
        except Exception:
            if not allow_missing_tables:
                conn.close()
                raise
            lc = empty_lc
        conn.close()
        return cls.from_data(st, lc, price_view)

    # ── ST ──────────────────────────────────────────────────────────────
    def st_mask(self, dt: date, syms: list[str]) -> pd.Series:
        ts = pd.Timestamp(dt)
        try:
            day = self._st.xs(ts, level=0)
            present = day["is_st"].reindex(syms).fillna(False)
        except KeyError:
            present = pd.Series(False, index=syms)
        return present.astype(bool)

    def is_st(self, dt: date, sym: str) -> bool:
        return bool(self.st_mask(dt, [sym]).iloc[0])

    # ── suspended ───────────────────────────────────────────────────────
    def suspended_mask(self, dt: date, syms: list[str]) -> pd.Series:
        if self._price_view is None:
            return pd.Series(False, index=syms)
        df = self._price_view.slice_eod(dt, syms)
        v = df["volume"].reindex(syms).fillna(0) if "volume" in df.columns else pd.Series(0, index=syms)
        a = df["amount"].reindex(syms).fillna(0) if "amount" in df.columns else pd.Series(0, index=syms)
        return ((v == 0) | (a == 0)).astype(bool)

    def is_suspended(self, dt: date, sym: str) -> bool:
        return bool(self.suspended_mask(dt, [sym]).iloc[0])

    # ── lifecycle ───────────────────────────────────────────────────────
    def listing_date(self, sym: str) -> date | None:
        if sym not in self._lifecycle.index:
            return None
        d = self._lifecycle.loc[sym, "listing_date"]
        return None if pd.isna(d) else d

    def delisting_date(self, sym: str) -> date | None:
        if sym not in self._lifecycle.index:
            return None
        d = self._lifecycle.loc[sym, "delisting_date"]
        return None if pd.isna(d) else d

    def is_newly_listed(self, dt: date, sym: str, n_days: int = 60) -> bool:
        ld = self.listing_date(sym)
        if ld is None:
            return False
        return (dt - ld).days < n_days

    # ── board + limit_pct ───────────────────────────────────────────────
    def board_of(self, sym: str) -> str:
        if sym in self._lifecycle.index:
            board = self._lifecycle.loc[sym, "board"]
            if isinstance(board, str):
                return board
        return _board_of_symbol(sym)

    def _resolve_limit_pct(self, dt: date, board: str, is_st: bool) -> float:
        if is_st:
            return 0.05
        if board in ("chinext", "star"):
            return 0.20 if dt >= CHINEXT_LIMIT_REGIME_CHANGE else 0.10
        if board == "bse":
            return 0.30
        return 0.10

    def limit_pct(self, dt: date, sym: str) -> float:
        return self._resolve_limit_pct(dt, self.board_of(sym), self.is_st(dt, sym))
