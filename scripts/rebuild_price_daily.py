#!/usr/bin/env python3
"""
Rebuild market_daily: drop all data, re-fetch from rqdatac with unified format.

Rules:
  - Symbol format: SH600000 / SZ000001 (consistent with Qlib)
  - Price adjustment: pre-adjusted (前复权)
  - Fields: OHLCV + amount + limit_up/down
  - Date range: 2015-01-01 ~ today

Usage:
    PYTHONPATH=/Users/xinzhan/.openclaw/workspace \
    /Users/xinzhan/miniconda3/envs/quantfactor/bin/python scripts/rebuild_market_daily.py
"""

import logging
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import rqdatac as rq

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "quant_data",
    "user": "postgres",
    "password": "postgres",
}

BATCH_SIZE = 200
START_DATE = "20150101"


def get_conn():
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute("SET timescaledb.max_tuples_decompressed_per_dml_transaction = 0")
    conn.commit()
    return conn


def to_internal(order_book_id: str) -> str:
    """600000.XSHG → SH600000, 000001.XSHE → SZ000001"""
    code, exchange = order_book_id.split(".")
    if exchange in ("XSHG", "SH"):
        return f"SH{code}"
    elif exchange in ("XSHE", "SZ"):
        return f"SZ{code}"
    return order_book_id


# ── Step 1: Truncate ─────────────────────────────────────────────────

def truncate_market_daily():
    """Delete all data from market_daily."""
    conn = get_conn()
    cur = conn.cursor()
    logger.info("[Step 1] Truncating market_daily...")
    # For hypertables, use DELETE instead of TRUNCATE to avoid issues
    cur.execute("DELETE FROM market_daily")
    conn.commit()
    cur.close()
    conn.close()
    logger.info("  market_daily cleared")


# ── Step 2: Fetch & Insert ───────────────────────────────────────────

def fetch_and_insert():
    """Fetch all data from rqdatac year-by-year, insert into market_daily."""
    logger.info("[Step 2] Fetching from rqdatac and inserting...")

    insts = rq.all_instruments("CS")
    symbols = sorted(insts["order_book_id"].tolist())
    logger.info("  Total instruments: %d", len(symbols))

    conn = get_conn()
    cur = conn.cursor()

    end_date = datetime.now().strftime("%Y%m%d")
    current_year = datetime.now().year
    total_inserted = 0

    for year in range(2015, current_year + 1):
        y_start = f"{year}0101"
        y_end = f"{year}1231" if year < current_year else end_date
        year_inserted = 0

        n_batches = (len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE
        for i in range(0, len(symbols), BATCH_SIZE):
            batch = symbols[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1

            try:
                df = rq.get_price(
                    order_book_ids=batch,
                    start_date=y_start,
                    end_date=y_end,
                    frequency="1d",
                    fields=["open", "high", "low", "close", "volume",
                            "total_turnover", "limit_up", "limit_down"],
                    adjust_type="pre",
                )
            except Exception as e:
                logger.warning("  Year %d batch %d/%d failed: %s",
                               year, batch_num, n_batches, e)
                time.sleep(2)
                continue

            if df is None or df.empty:
                continue

            df = df.reset_index()

            records = []
            for _, row in df.iterrows():
                sym = to_internal(str(row["order_book_id"]))
                t = pd.to_datetime(row["date"])

                def _f(col):
                    v = row.get(col)
                    if v is None or (isinstance(v, float) and np.isnan(v)):
                        return None
                    return float(v)

                records.append((
                    t, sym,
                    _f("open"), _f("high"), _f("low"), _f("close"),
                    _f("volume"), _f("total_turnover"),
                    0.0,  # vwap placeholder
                    _f("limit_up"), _f("limit_down"),
                ))

            if records:
                sql = """
                    INSERT INTO market_daily
                    (time, symbol, open, high, low, close, volume, amount, vwap, limit_up, limit_down)
                    VALUES %s
                    ON CONFLICT (time, symbol) DO UPDATE SET
                        open = EXCLUDED.open,
                        high = EXCLUDED.high,
                        low = EXCLUDED.low,
                        close = EXCLUDED.close,
                        volume = EXCLUDED.volume,
                        amount = EXCLUDED.amount,
                        limit_up = EXCLUDED.limit_up,
                        limit_down = EXCLUDED.limit_down
                """
                for j in range(0, len(records), 5000):
                    execute_values(cur, sql, records[j:j + 5000])
                    conn.commit()
                year_inserted += len(records)

            if batch_num % 10 == 0:
                logger.info("  Year %d: batch %d/%d (%d rows)",
                            year, batch_num, n_batches, year_inserted)

        total_inserted += year_inserted
        logger.info("  Year %d complete: %d rows", year, year_inserted)

    cur.close()
    conn.close()
    logger.info("  Total inserted: %d rows", total_inserted)
    return total_inserted


# ── Step 3: Validate ─────────────────────────────────────────────────

def validate():
    """Validate the rebuilt market_daily table."""
    logger.info("[Step 3] Validating...")

    conn = get_conn()
    cur = conn.cursor()
    errors = []

    # 1. Basic counts
    cur.execute("""
        SELECT COUNT(*) as total,
               COUNT(DISTINCT symbol) as n_symbols,
               MIN(time)::date as min_date,
               MAX(time)::date as max_date
        FROM market_daily
    """)
    total, n_symbols, min_date, max_date = cur.fetchone()
    logger.info("  Total: %d rows, %d symbols, %s ~ %s", total, n_symbols, min_date, max_date)

    if total < 5_000_000:
        errors.append(f"Too few rows: {total} (expected >5M)")
    if n_symbols < 5000:
        errors.append(f"Too few symbols: {n_symbols} (expected >5000)")

    # 2. No duplicate naming formats
    cur.execute("""
        SELECT
          COUNT(CASE WHEN symbol LIKE 'SH%' OR symbol LIKE 'SZ%' THEN 1 END) as new_fmt,
          COUNT(CASE WHEN symbol LIKE '%.XSHG' OR symbol LIKE '%.XSHE' OR symbol LIKE '%.SH' THEN 1 END) as old_fmt
        FROM (SELECT DISTINCT symbol FROM market_daily) s
    """)
    new_fmt, old_fmt = cur.fetchone()
    logger.info("  Symbol formats: new=%d, old=%d", new_fmt, old_fmt)
    if old_fmt > 0:
        errors.append(f"Old format symbols still exist: {old_fmt}")

    # 3. Amount coverage per year
    cur.execute("""
        SELECT EXTRACT(YEAR FROM time)::int as y,
               COUNT(*) as total,
               COUNT(CASE WHEN amount > 0 THEN 1 END) as amount_ok,
               COUNT(CASE WHEN close IS NOT NULL THEN 1 END) as close_ok
        FROM market_daily
        GROUP BY y ORDER BY y
    """)
    for year, yr_total, amount_ok, close_ok in cur.fetchall():
        amt_pct = amount_ok / yr_total * 100 if yr_total > 0 else 0
        close_pct = close_ok / yr_total * 100 if yr_total > 0 else 0
        status = "✓" if amt_pct > 90 else "⚠" if amt_pct > 70 else "✗"
        logger.info("  %s %d: %d rows, amount=%.1f%%, close=%.1f%%",
                     status, year, yr_total, amt_pct, close_pct)
        if amt_pct < 70:
            errors.append(f"Amount coverage low for {year}: {amt_pct:.1f}%")

    # 4. Spot-check against rqdatac
    logger.info("  Spot-checking against rqdatac...")
    spot_checks = [
        ("600000.XSHG", "SH600000", "20240102"),
        ("000001.XSHE", "SZ000001", "20250101"),
        ("600519.XSHG", "SH600519", "20230601"),
    ]
    for rq_sym, db_sym, date in spot_checks:
        rq_df = rq.get_price(rq_sym, start_date=date, end_date=date,
                              frequency="1d", fields=["close", "volume", "total_turnover"],
                              adjust_type="pre")
        if rq_df is None or rq_df.empty:
            continue

        rq_close = float(rq_df["close"].iloc[0])
        rq_vol = float(rq_df["volume"].iloc[0])
        rq_amt = float(rq_df["total_turnover"].iloc[0])

        cur.execute(
            "SELECT close, volume, amount FROM market_daily WHERE symbol = %s AND time::date = %s::date",
            (db_sym, date)
        )
        row = cur.fetchone()
        if row is None:
            logger.warning("    %s %s: NOT FOUND in DB", db_sym, date)
            continue

        db_close, db_vol, db_amt = row
        close_ok = abs(rq_close - db_close) / rq_close < 0.001 if db_close else False
        vol_ok = abs(rq_vol - db_vol) / rq_vol < 0.001 if db_vol and rq_vol > 0 else False
        amt_ok = abs(rq_amt - db_amt) / rq_amt < 0.01 if db_amt and rq_amt > 0 else False

        status = "✓" if (close_ok and vol_ok) else "✗"
        logger.info("    %s %s %s: close=%s vol=%s amt=%s",
                     status, db_sym, date,
                     "OK" if close_ok else f"MISMATCH(rq={rq_close:.4f} db={db_close})",
                     "OK" if vol_ok else f"MISMATCH(rq={rq_vol:.0f} db={db_vol})",
                     "OK" if amt_ok else f"MISMATCH(rq={rq_amt:.0f} db={db_amt})")

        if not close_ok:
            errors.append(f"Spot-check failed: {db_sym} {date} close mismatch")

    cur.close()
    conn.close()

    if errors:
        logger.error("VALIDATION FAILED:")
        for e in errors:
            logger.error("  • %s", e)
        return False
    else:
        logger.info("✅ VALIDATION PASSED")
        return True


# ── Main ─────────────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("REBUILD market_daily: clean slate from rqdatac")
    logger.info("=" * 60)

    rq.init()
    logger.info("rqdatac initialized")

    truncate_market_daily()
    fetch_and_insert()
    ok = validate()

    if ok:
        logger.info("\n✅ Rebuild complete and validated!")
        logger.info("Next: run scripts/resync_qlib.py to rebuild Qlib binary files")
    else:
        logger.error("\n❌ Rebuild complete but validation FAILED")
        sys.exit(1)


if __name__ == "__main__":
    main()
