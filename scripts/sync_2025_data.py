#!/usr/bin/env python3
"""
Sync 2025 data: rqdatac → TimescaleDB (market_daily) → Qlib binary format.

Usage:
    # From project root with conda env:
    PYTHONPATH=/Users/xinzhan/.openclaw/workspace \
    /Users/xinzhan/miniconda3/envs/quantfactor/bin/python scripts/sync_2025_data.py

Steps:
    1. Fetch all A-share daily data for 2025 from rqdatac (batched)
    2. Insert into TimescaleDB market_daily table
    3. Re-sync full date range (2015-2025) to Qlib binary format
"""

import logging
import struct
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
import rqdatac as rq

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ── Config ──��───────────────────────────────────────────────────────
SYNC_START = "20250101"
SYNC_END = datetime.now().strftime("%Y%m%d")

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "quant_data",
    "user": "postgres",
    "password": "postgres",
}

QLIB_DIR = Path("~/.qlib/qlib_data/cn_data_1d").expanduser()

# rqdatac batch size (stocks per request to avoid timeout)
BATCH_SIZE = 200


# ── Step 1: Fetch from rqdatac ──────────────────────────────────────

def fetch_2025_daily() -> pd.DataFrame:
    """Fetch all A-share daily data for 2025 from rqdatac."""
    logger.info("Initializing rqdatac...")
    rq.init()

    # Get all A-share stocks
    instruments = rq.all_instruments("CS")
    order_book_ids = sorted(instruments["order_book_id"].tolist())
    logger.info(f"Total A-share stocks: {len(order_book_ids)}")

    all_data = []
    n_batches = (len(order_book_ids) + BATCH_SIZE - 1) // BATCH_SIZE

    for i in range(0, len(order_book_ids), BATCH_SIZE):
        batch = order_book_ids[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1
        logger.info(f"Fetching batch {batch_num}/{n_batches} ({len(batch)} stocks)...")

        try:
            df = rq.get_price(
                order_book_ids=batch,
                start_date=SYNC_START,
                end_date=SYNC_END,
                frequency="1d",
                fields=["open", "high", "low", "close", "volume",
                         "total_turnover", "limit_up", "limit_down"],
                adjust_type="pre",
            )
        except Exception as e:
            logger.error(f"Batch {batch_num} failed: {e}")
            continue

        if df is None or df.empty:
            logger.warning(f"Batch {batch_num}: no data returned")
            continue

        df = df.reset_index()
        all_data.append(df)
        logger.info(f"  → {len(df)} rows")

    if not all_data:
        logger.error("No data fetched at all!")
        sys.exit(1)

    result = pd.concat(all_data, ignore_index=True)

    # Normalize columns
    if "date" in result.columns:
        result["time"] = pd.to_datetime(result["date"])
    elif "datetime" in result.columns:
        result["time"] = pd.to_datetime(result["datetime"])

    if "order_book_id" in result.columns:
        result["symbol"] = result["order_book_id"].apply(_to_internal_symbol)

    # Rename amount
    if "total_turnover" in result.columns:
        result["amount"] = result["total_turnover"]

    # Fill missing vwap
    if "vwap" not in result.columns:
        result["vwap"] = 0.0

    logger.info(f"Total fetched: {len(result)} rows, "
                f"{result['symbol'].nunique()} stocks, "
                f"{result['time'].min().date()} ~ {result['time'].max().date()}")
    return result


def _to_internal_symbol(order_book_id: str) -> str:
    """600000.XSHG → SH600000, 000001.XSHE → SZ000001"""
    code, exchange = order_book_id.split(".")
    if exchange in ("XSHG", "SH"):
        return f"SH{code}"
    elif exchange in ("XSHE", "SZ"):
        return f"SZ{code}"
    return order_book_id


# ── Step 2: Insert into TimescaleDB ────���────────────────────────────

def insert_to_db(df: pd.DataFrame) -> int:
    """Insert into market_daily table via psycopg2."""
    import psycopg2
    from psycopg2.extras import execute_values

    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cursor = conn.cursor()

    # Prepare records
    cols = ["time", "symbol", "open", "high", "low", "close", "volume",
            "amount", "vwap", "limit_up", "limit_down"]

    for col in cols:
        if col not in df.columns:
            df[col] = 0.0

    df["time"] = pd.to_datetime(df["time"])

    records = [
        (
            row["time"], row["symbol"],
            float(row["open"]) if pd.notna(row["open"]) else None,
            float(row["high"]) if pd.notna(row["high"]) else None,
            float(row["low"]) if pd.notna(row["low"]) else None,
            float(row["close"]) if pd.notna(row["close"]) else None,
            float(row["volume"]) if pd.notna(row["volume"]) else 0,
            float(row["amount"]) if pd.notna(row["amount"]) else 0,
            float(row["vwap"]) if pd.notna(row["vwap"]) else 0,
            float(row["limit_up"]) if pd.notna(row["limit_up"]) else 0,
            float(row["limit_down"]) if pd.notna(row["limit_down"]) else 0,
        )
        for _, row in df.iterrows()
    ]

    logger.info(f"Inserting {len(records)} rows into market_daily...")

    sql = """
        INSERT INTO market_daily (time, symbol, open, high, low, close, volume, amount, vwap, limit_up, limit_down)
        VALUES %s
        ON CONFLICT (time, symbol) DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume,
            amount = EXCLUDED.amount,
            vwap = EXCLUDED.vwap,
            limit_up = EXCLUDED.limit_up,
            limit_down = EXCLUDED.limit_down
    """

    batch_size = 5000
    total = 0
    for i in range(0, len(records), batch_size):
        batch = records[i : i + batch_size]
        execute_values(cursor, sql, batch)
        conn.commit()
        total += len(batch)
        if (i // batch_size) % 20 == 0:
            logger.info(f"  inserted {total}/{len(records)}")

    cursor.close()
    conn.close()
    logger.info(f"DB insert complete: {total} rows")
    return total


# ── Step 3: Re-sync to Qlib binary ───────���──────────────────────────

def sync_to_qlib():
    """Read full market_daily (2015-2025) and rebuild Qlib binary files."""
    import psycopg2

    conn = psycopg2.connect(**DB_CONFIG)
    logger.info("Reading full market_daily from DB for Qlib sync...")

    df = pd.read_sql(
        "SELECT time, symbol, open, high, low, close, volume, amount, vwap, "
        "limit_up, limit_down FROM market_daily ORDER BY symbol, time",
        conn,
    )
    conn.close()

    if df.empty:
        logger.error("No data in market_daily!")
        return

    logger.info(f"Loaded {len(df)} rows, {df['symbol'].nunique()} symbols, "
                f"{df['time'].min()} ~ {df['time'].max()}")

    df["time"] = pd.to_datetime(df["time"])
    df = df.sort_values(["symbol", "time"])

    # Derive fields
    df["returns"] = df.groupby("symbol")["close"].pct_change()
    df["returns_1d"] = df.groupby("symbol")["close"].shift(-1) / df["close"] - 1

    # Convert symbol format: 000001.XSHE → SZ000001 (already in SH/SZ format in DB)

    # ── Calendar ──
    trading_days = sorted(df["time"].dt.strftime("%Y-%m-%d").unique())
    cal_dir = QLIB_DIR / "calendars"
    cal_dir.mkdir(parents=True, exist_ok=True)
    (cal_dir / "day.txt").write_text("\n".join(trading_days) + "\n")
    logger.info(f"Calendar: {len(trading_days)} days ({trading_days[0]} ~ {trading_days[-1]})")

    # ── Instruments ──
    symbols = sorted(df["symbol"].unique())
    inst_dir = QLIB_DIR / "instruments"
    inst_dir.mkdir(parents=True, exist_ok=True)
    lines = [f"{sym}\t{trading_days[0]}\t{trading_days[-1]}" for sym in symbols]
    (inst_dir / "all.txt").write_text("\n".join(lines) + "\n")
    logger.info(f"Instruments: {len(symbols)} symbols")

    # ── Features ──
    feat_dir = QLIB_DIR / "features"
    feat_dir.mkdir(parents=True, exist_ok=True)

    fields = ["open", "high", "low", "close", "volume", "amount", "vwap",
              "returns", "returns_1d", "limit_up", "limit_down"]

    # Build calendar index for fast lookup
    cal_index = {day: i for i, day in enumerate(trading_days)}
    n_days = len(trading_days)

    n_symbols = len(symbols)
    for idx, (symbol, group) in enumerate(df.groupby("symbol")):
        sym_dir = feat_dir / str(symbol)
        sym_dir.mkdir(parents=True, exist_ok=True)

        # Build date→row mapping for this symbol
        group = group.set_index(group["time"].dt.strftime("%Y-%m-%d"))

        for field in fields:
            if field not in group.columns:
                continue

            values = np.full(n_days, np.nan, dtype=np.float32)
            for day, cal_idx in cal_index.items():
                if day in group.index:
                    row = group.loc[day]
                    if isinstance(row, pd.DataFrame):
                        row = row.iloc[0]
                    val = row[field]
                    if pd.notna(val):
                        values[cal_idx] = float(val)

            bin_path = sym_dir / f"{field}.day.bin"
            values.tofile(str(bin_path))

        if (idx + 1) % 500 == 0:
            logger.info(f"  features written: {idx + 1}/{n_symbols}")

    logger.info(f"Qlib sync complete: {n_symbols} symbols, {n_days} days, "
                f"{len(fields)} fields")


# ── Main ───────���─────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("Sync 2025 data: rqdatac → TimescaleDB → Qlib")
    logger.info("=" * 60)

    # Step 1
    logger.info("\n[Step 1/3] Fetching 2025 daily data from rqdatac...")
    df = fetch_2025_daily()

    # Step 2
    logger.info("\n[Step 2/3] Inserting into TimescaleDB market_daily...")
    insert_to_db(df)

    # Step 3
    logger.info("\n[Step 3/3] Re-syncing full dataset to Qlib binary format...")
    sync_to_qlib()

    logger.info("\n" + "=" * 60)
    logger.info("All done!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
