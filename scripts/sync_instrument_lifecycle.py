#!/usr/bin/env python3
"""Sync listing/delisting dates + board classification → ``instrument_lifecycle``.

Run after ``migrations/2026-05-01-backtest-tradability-tables.sql``.

Usage::

    PYTHONPATH=src python3 scripts/sync_instrument_lifecycle.py
"""
from __future__ import annotations

import logging
import os
import sys

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def _db_dsn() -> dict:
    return dict(
        host=os.environ.get("TIMESCALE_HOST", "localhost"),
        port=int(os.environ.get("TIMESCALE_PORT", 5432)),
        dbname=os.environ.get("TIMESCALE_DB", "quant_data"),
        user=os.environ.get("TIMESCALE_USER", "postgres"),
        password=os.environ.get("TIMESCALE_PASSWORD", "postgres"),
    )


def _to_internal_symbol(rq_id: str) -> str:
    if rq_id.endswith(".XSHG"):
        return f"SH{rq_id.split('.')[0]}"
    if rq_id.endswith(".XSHE"):
        return f"SZ{rq_id.split('.')[0]}"
    return rq_id


def _board_of(sym: str) -> str:
    if sym.startswith("SH688"):
        return "star"
    if sym.startswith("SZ300"):
        return "chinext"
    if sym.startswith("BJ8") or sym.startswith("BJ4"):
        return "bse"
    return "main"


def main() -> None:
    try:
        import psycopg2
        import rqdatac as rq  # type: ignore
    except ImportError as exc:
        logger.error("missing dependency: %s", exc)
        sys.exit(1)

    from dotenv import load_dotenv
    load_dotenv()
    if not os.environ.get("RQDATAC_CONF"):
        logger.error("RQDATAC_CONF env var not set")
        sys.exit(1)
    rq.init()

    inst = rq.all_instruments(type="CS")
    rows = []
    for _, r in inst.iterrows():
        sym = _to_internal_symbol(r.order_book_id)
        listing = r.listed_date if hasattr(r, "listed_date") else r.get("listed_date")
        delisting = r.de_listed_date if hasattr(r, "de_listed_date") else r.get("de_listed_date")
        # rq returns "0000-00-00" or NaT for not-yet-delisted; coerce to None
        if delisting in ("0000-00-00", None) or (hasattr(delisting, "date") and str(delisting) == "NaT"):
            delisting = None
        rows.append((sym, listing, delisting, _board_of(sym)))

    conn = psycopg2.connect(**_db_dsn())
    cur = conn.cursor()
    cur.executemany(
        "INSERT INTO instrument_lifecycle (instrument, listing_date, delisting_date, board) "
        "VALUES (%s,%s,%s,%s) "
        "ON CONFLICT (instrument) DO UPDATE "
        "SET listing_date=EXCLUDED.listing_date, "
        "    delisting_date=EXCLUDED.delisting_date, "
        "    board=EXCLUDED.board",
        rows,
    )
    conn.commit()
    cur.execute("SELECT COUNT(*) FROM instrument_lifecycle")
    n = cur.fetchone()[0]
    conn.close()
    logger.info("instrument_lifecycle now has %d rows", n)


if __name__ == "__main__":
    main()
