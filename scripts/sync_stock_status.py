#!/usr/bin/env python3
"""Sync PIT ST / suspension status from RiceQuant to TimescaleDB.

Writes ``ref_stock_status``:

    time DATE, symbol TEXT, is_st BOOL, is_suspended BOOL

The research pipeline treats this as an optional enhancement.  When the
table is present, Phase 2 masks ST / suspended stock-days before computing
IC and quintile metrics.
"""

from __future__ import annotations

import argparse
import logging
import time
from datetime import datetime

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values

logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "quant_data",
    "user": "postgres",
    "password": "postgres",
}


def _to_rq_symbol(symbol: str) -> str:
    if symbol.startswith("SH"):
        return f"{symbol[2:]}.XSHG"
    if symbol.startswith("SZ"):
        return f"{symbol[2:]}.XSHE"
    return symbol


def _to_internal_symbol(order_book_id: str) -> str:
    code, exchange = order_book_id.split(".", 1)
    if exchange in {"XSHG", "SH"}:
        return f"SH{code}"
    if exchange in {"XSHE", "SZ"}:
        return f"SZ{code}"
    return order_book_id


def ensure_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ref_stock_status (
                time DATE NOT NULL,
                symbol TEXT NOT NULL,
                is_st BOOLEAN NOT NULL DEFAULT FALSE,
                is_suspended BOOLEAN,
                UNIQUE(time, symbol)
            )
            """
        )
        cur.execute(
            """
            CREATE INDEX IF NOT EXISTS ix_ref_stock_status_time_symbol
            ON ref_stock_status(time, symbol)
            """
        )
    conn.commit()


def load_symbols(conn, limit: int | None = None) -> list[str]:
    sql = "SELECT DISTINCT symbol FROM market_daily ORDER BY symbol"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return list(pd.read_sql(sql, conn)["symbol"])


def _status_frame_to_rows(
    st_df: pd.DataFrame | None,
    suspended_df: pd.DataFrame | None,
) -> list[tuple[pd.Timestamp, str, bool, bool | None]]:
    frames: list[pd.DataFrame] = []
    if st_df is not None and not st_df.empty:
        st_long = st_df.stack().rename("is_st").reset_index()
        st_long.columns = ["time", "order_book_id", "is_st"]
        frames.append(st_long)
    if suspended_df is not None and not suspended_df.empty:
        sus_long = suspended_df.stack().rename("is_suspended").reset_index()
        sus_long.columns = ["time", "order_book_id", "is_suspended"]
        frames.append(sus_long)
    if not frames:
        return []

    merged = frames[0]
    for frame in frames[1:]:
        merged = merged.merge(frame, on=["time", "order_book_id"], how="outer")
    merged["symbol"] = merged["order_book_id"].map(_to_internal_symbol)
    merged["is_st"] = merged.get("is_st", False).fillna(False).astype(bool)
    if "is_suspended" in merged:
        merged["is_suspended"] = merged["is_suspended"].where(
            merged["is_suspended"].notna(), None
        )
    else:
        merged["is_suspended"] = None

    rows = []
    for _, row in merged.iterrows():
        rows.append(
            (
                pd.Timestamp(row["time"]).date(),
                row["symbol"],
                bool(row["is_st"]),
                None if pd.isna(row["is_suspended"]) else bool(row["is_suspended"]),
            )
        )
    return rows


def upsert_rows(conn, rows: list[tuple[pd.Timestamp, str, bool, bool | None]]) -> int:
    if not rows:
        return 0
    with conn.cursor() as cur:
        execute_values(
            cur,
            """
            INSERT INTO ref_stock_status (time, symbol, is_st, is_suspended)
            VALUES %s
            ON CONFLICT (time, symbol) DO UPDATE SET
                is_st = EXCLUDED.is_st,
                is_suspended = EXCLUDED.is_suspended
            """,
            rows,
            page_size=5000,
        )
    conn.commit()
    return len(rows)


def sync_status(
    *,
    start: str,
    end: str,
    batch_size: int,
    sleep_seconds: float,
    symbol_limit: int | None = None,
) -> int:
    import rqdatac as rq

    rq.init()
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        ensure_table(conn)
        symbols = load_symbols(conn, limit=symbol_limit)
        rq_symbols = [_to_rq_symbol(s) for s in symbols]
        total = 0

        logger.info(
            "Syncing ref_stock_status: %d symbols, %s ~ %s",
            len(rq_symbols),
            start,
            end,
        )
        for i in range(0, len(rq_symbols), batch_size):
            batch = rq_symbols[i : i + batch_size]
            batch_no = i // batch_size + 1
            try:
                st_df = rq.is_st_stock(batch, start_date=start, end_date=end)
                suspended_df = rq.is_suspended(batch, start_date=start, end_date=end)
            except Exception as exc:  # noqa: BLE001 - keep long sync moving
                logger.warning("batch %d failed (%d symbols): %s", batch_no, len(batch), exc)
                time.sleep(max(sleep_seconds, 1.0))
                continue

            rows = _status_frame_to_rows(st_df, suspended_df)
            n = upsert_rows(conn, rows)
            total += n
            logger.info(
                "batch %d: %d symbols, %d rows upserted (%d total)",
                batch_no,
                len(batch),
                n,
                total,
            )
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)

        return total
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="20150101")
    parser.add_argument("--end", default=datetime.now().strftime("%Y%m%d"))
    parser.add_argument("--batch-size", type=int, default=100)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--symbol-limit", type=int, default=None)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    total = sync_status(
        start=args.start,
        end=args.end,
        batch_size=args.batch_size,
        sleep_seconds=args.sleep,
        symbol_limit=args.symbol_limit,
    )
    logger.info("Done: %d rows upserted", total)


if __name__ == "__main__":
    main()

