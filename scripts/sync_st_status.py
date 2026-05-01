#!/usr/bin/env python3
"""Sync A-share ST status history into ``instrument_st_status``.

Reads the qlib instruments list (avoiding a full RQ all_instruments call), then
calls ``rq.is_st_stock(order_book_ids, start_date, end_date)`` once per yearly
chunk. Returns a DataFrame indexed by date with symbols as columns (bool).
Inserts ``(date, symbol, True)`` for every (date, symbol) cell that is True.

Run after ``migrations/2026-05-01-backtest-tradability-tables.sql``.

Usage::

    PYTHONPATH=src python3 scripts/sync_st_status.py
    PYTHONPATH=src python3 scripts/sync_st_status.py --start 2024-01-01 --end 2024-12-31
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import date
from pathlib import Path

import pandas as pd

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


def _rq_id(sym: str) -> str:
    if sym.startswith("SH"):
        return sym[2:] + ".XSHG"
    if sym.startswith("SZ"):
        return sym[2:] + ".XSHE"
    return sym


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2015-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument(
        "--instruments-file",
        default=str(Path("~/.qlib/qlib_data/cn_data_1d/instruments/all.txt").expanduser()),
    )
    args = parser.parse_args()

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

    inst_path = Path(args.instruments_file)
    if not inst_path.exists():
        logger.error("instruments file missing: %s", inst_path)
        sys.exit(1)
    syms = sorted({line.split("\t", 1)[0] for line in inst_path.read_text().splitlines() if line})
    rq_ids = [_rq_id(s) for s in syms]
    sym_by_rq = dict(zip(rq_ids, syms))

    conn = psycopg2.connect(**_db_dsn())
    cur = conn.cursor()

    start = pd.Timestamp(args.start)
    end = pd.Timestamp(args.end)
    logger.info("scanning %s → %s × %d symbols", start.date(), end.date(), len(syms))

    INSERT_SQL = (
        "INSERT INTO instrument_st_status (datetime, instrument, is_st) "
        "VALUES (%s,%s,%s) ON CONFLICT DO NOTHING"
    )

    # Yearly chunks: rq.is_st_stock(ids, start, end) returns wide DataFrame
    # (index=date, cols=symbols, bool). One call per year keeps memory bounded.
    cur_start = start
    while cur_start <= end:
        cur_end = min(cur_start + pd.DateOffset(years=1) - pd.Timedelta(days=1), end)
        try:
            df = rq.is_st_stock(rq_ids, start_date=cur_start.date(), end_date=cur_end.date())
        except Exception as exc:
            logger.warning("is_st_stock failed %s ~ %s: %s", cur_start.date(), cur_end.date(), exc)
            cur_start = cur_end + pd.Timedelta(days=1)
            continue
        if df is None or df.empty:
            cur_start = cur_end + pd.Timedelta(days=1)
            continue
        # Stack True cells: melt to long, filter is_st==True
        st_long = df.stack().reset_index()
        st_long.columns = ["datetime", "rq_id", "is_st"]
        st_long = st_long[st_long["is_st"]]
        st_long["instrument"] = st_long["rq_id"].map(sym_by_rq)
        st_long = st_long.dropna(subset=["instrument"])
        rows = list(zip(
            st_long["datetime"].dt.date,
            st_long["instrument"],
            [True] * len(st_long),
        ))
        if rows:
            cur.executemany(INSERT_SQL, rows)
            conn.commit()
        logger.info("chunk %s ~ %s: %d ST cells", cur_start.date(), cur_end.date(), len(rows))
        cur_start = cur_end + pd.Timedelta(days=1)

    cur.execute("SELECT COUNT(*) FROM instrument_st_status")
    n = cur.fetchone()[0]
    conn.close()
    logger.info("instrument_st_status now has %d rows", n)


if __name__ == "__main__":
    main()
