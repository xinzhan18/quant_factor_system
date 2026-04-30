#!/usr/bin/env python3
"""Sync A-share ST status history into ``instrument_st_status``.

Reads the qlib instruments list (avoiding a full RQ all_instruments call), then
calls ``rq.is_st_stock`` per (date, symbol). Inserts ``(date, symbol, True)`` for
every (date, symbol) pair where the stock is ST.

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

    dates = pd.bdate_range(args.start, args.end).date
    logger.info("scanning %d trading days × %d symbols", len(dates), len(syms))

    rows: list[tuple] = []
    BATCH = 50_000
    for i, dt in enumerate(dates):
        # rq.is_st_stock is vectorized over symbols; one call per date
        try:
            mask = rq.is_st_stock(rq_ids, date=str(dt))
        except Exception as exc:
            logger.warning("is_st_stock failed @ %s: %s", dt, exc)
            continue
        if isinstance(mask, dict):
            iter_pairs = mask.items()
        else:
            iter_pairs = zip(rq_ids, mask)
        for rq_id, is_st in iter_pairs:
            if bool(is_st):
                rows.append((dt, sym_by_rq[rq_id], True))
        if len(rows) >= BATCH:
            cur.executemany(
                "INSERT INTO instrument_st_status (datetime, instrument, is_st) "
                "VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                rows,
            )
            conn.commit()
            rows.clear()
        if (i + 1) % 250 == 0:
            logger.info("scanned %d / %d dates", i + 1, len(dates))

    if rows:
        cur.executemany(
            "INSERT INTO instrument_st_status (datetime, instrument, is_st) "
            "VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
            rows,
        )
        conn.commit()

    cur.execute("SELECT COUNT(*) FROM instrument_st_status")
    n = cur.fetchone()[0]
    conn.close()
    logger.info("instrument_st_status now has %d rows", n)


if __name__ == "__main__":
    main()
