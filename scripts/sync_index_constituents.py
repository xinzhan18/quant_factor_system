#!/usr/bin/env python3
"""
Sync index constituent history: RiceQuant API → TimescaleDB → Qlib instruments file.

3-step pipeline:
  1. Fetch constituent snapshots from RiceQuant API (weekly sampling)
  2. Store in TimescaleDB `index_constituents` table
  3. Generate Qlib `instruments/{index_name}.txt` + validate

Usage:
    PYTHONPATH=src python3 scripts/sync_index_constituents.py csi1000
    PYTHONPATH=src python3 scripts/sync_index_constituents.py csi300
    PYTHONPATH=src python3 scripts/sync_index_constituents.py --all
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
import psycopg2

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

QLIB_DIR = Path("~/.qlib/qlib_data/cn_data_1d").expanduser()

UNIVERSE_MAP = {
    "csi300": "000300.XSHG",
    "csi500": "000905.XSHG",
    "csi1000": "000852.XSHG",
}

EXPECTED_COUNT = {
    "csi300": (290, 310),
    "csi500": (490, 510),
    "csi1000": (990, 1010),
}


# ── Helpers ────────────────────────────────────────────────────────────


def _rq_to_internal(order_book_id: str) -> str:
    """Convert RiceQuant order_book_id to internal format."""
    if "." not in order_book_id:
        return order_book_id
    code, exchange = order_book_id.split(".", 1)
    if exchange in ("XSHG", "SH"):
        return f"SH{code}"
    elif exchange in ("XSHE", "SZ"):
        return f"SZ{code}"
    return order_book_id


# ── Step 1: Fetch from RiceQuant ───────────────────────────────────────


def fetch_constituents(
    index_name: str,
    start_date: str = "2015-01-01",
    end_date: str = "2026-03-27",
) -> pd.DataFrame:
    """Fetch index constituent history in one API call.

    ``rq.index_components(start_date=, end_date=)`` returns a dict keyed
    by membership-change dates (typically ~rebalance events). One call
    covers the whole window — fully replacing the previous per-day loop.

    Returns DataFrame with columns [date, symbol, index_name]. Each
    membership-change date contributes one row per constituent on that
    date; downstream interval merging fills in the in-between days.
    """
    try:
        import rqdatac as rq
        rq.init()
    except Exception as e:
        logger.error("Failed to init rqdatac: %s", e)
        sys.exit(1)

    rq_code = UNIVERSE_MAP[index_name]
    logger.info("Fetching %s via single bulk call (%s → %s)",
                index_name, start_date, end_date)
    snapshots = rq.index_components(rq_code, start_date=start_date, end_date=end_date)
    if not snapshots:
        logger.error("Empty result for %s", index_name)
        return pd.DataFrame(columns=["date", "symbol", "index_name"])

    rows = []
    for snap_date, ob_ids in snapshots.items():
        day_str = pd.Timestamp(snap_date).strftime("%Y-%m-%d")
        for ob_id in ob_ids or []:
            rows.append((day_str, _rq_to_internal(ob_id), index_name))

    df = pd.DataFrame(rows, columns=["date", "symbol", "index_name"])
    logger.info(
        "Fetched %s: %d rebalance dates, %d rows, %d unique symbols",
        index_name, len(snapshots), len(df), df["symbol"].nunique(),
    )
    return df


# ── Step 2: Store to DB ────────────────────────────────────────────────


def store_to_db(df: pd.DataFrame) -> int:
    """Insert constituent data into TimescaleDB."""
    if df.empty:
        return 0

    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Create table if not exists
    cur.execute("""
        CREATE TABLE IF NOT EXISTS index_constituents (
            time DATE NOT NULL,
            symbol TEXT NOT NULL,
            index_name TEXT NOT NULL,
            UNIQUE(time, symbol, index_name)
        );
    """)
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_ic_index_time
        ON index_constituents(index_name, time);
    """)
    conn.commit()

    # Batch insert
    batch_size = 5000
    total = 0
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i + batch_size]
        values = []
        for _, row in batch.iterrows():
            values.append(cur.mogrify(
                "(%s, %s, %s)", (row["date"], row["symbol"], row["index_name"])
            ).decode())
        if values:
            cur.execute(
                "INSERT INTO index_constituents (time, symbol, index_name) VALUES "
                + ",".join(values)
                + " ON CONFLICT (time, symbol, index_name) DO NOTHING"
            )
            total += cur.rowcount
    conn.commit()
    cur.close()
    conn.close()

    logger.info("Stored %d new rows to index_constituents", total)
    return total


# ── Step 3: Generate instruments file + validate ───────────────────────


def generate_instruments(index_name: str) -> dict:
    """Read constituents from DB, merge intervals, write instruments file."""
    conn = psycopg2.connect(**DB_CONFIG)
    df = pd.read_sql(
        "SELECT time, symbol FROM index_constituents "
        "WHERE index_name = %s ORDER BY symbol, time",
        conn, params=(index_name,),
    )
    conn.close()

    if df.empty:
        logger.error("No constituent data in DB for %s", index_name)
        return {}

    df["time"] = pd.to_datetime(df["time"])

    # Merge consecutive dates into intervals (gap > 15 days → new interval)
    # Weekly sampling + CNY/National Day holidays can span ~14 calendar days
    gap_threshold = pd.Timedelta(days=15)
    intervals = []
    for symbol, grp in df.groupby("symbol"):
        dates = grp["time"].sort_values().reset_index(drop=True)
        interval_start = dates.iloc[0]
        prev = dates.iloc[0]
        for i in range(1, len(dates)):
            curr = dates.iloc[i]
            if curr - prev > gap_threshold:
                intervals.append((symbol, interval_start, prev))
                interval_start = curr
            prev = curr
        intervals.append((symbol, interval_start, prev))

    # Write instruments file
    inst_dir = QLIB_DIR / "instruments"
    inst_dir.mkdir(parents=True, exist_ok=True)
    inst_path = inst_dir / f"{index_name}.txt"

    lines = []
    for sym, start, end in sorted(intervals):
        lines.append(f"{sym}\t{start.strftime('%Y-%m-%d')}\t{end.strftime('%Y-%m-%d')}")
    inst_path.write_text("\n".join(lines) + "\n")

    n_symbols = len(set(sym for sym, _, _ in intervals))
    stats = {
        "n_symbols": n_symbols,
        "n_intervals": len(intervals),
        "file": str(inst_path),
    }
    logger.info("Generated %s: %d symbols, %d intervals", inst_path, n_symbols, len(intervals))
    return stats


def validate(index_name: str, stats: dict) -> bool:
    """Validate the generated instruments file."""
    errors = []

    if not stats:
        errors.append("No stats returned from generation")
        return False

    # 1. File exists
    inst_path = QLIB_DIR / "instruments" / f"{index_name}.txt"
    if not inst_path.exists():
        errors.append(f"File not found: {inst_path}")
    else:
        lines = inst_path.read_text().strip().split("\n")
        logger.info("  File: %d lines", len(lines))

    # 2. Expected symbol count (cumulative across all rebalances — much larger than per-date)
    # CSI 1000 over 10 years may have ~2500-3000 unique symbols due to turnover
    lo, hi = EXPECTED_COUNT.get(index_name, (100, 5000))
    n_sym = stats.get("n_symbols", 0)
    if n_sym < lo:
        errors.append(f"Too few symbols: {n_sym} (expected >= {lo})")

    # 3. All symbols have feature data
    all_inst_path = QLIB_DIR / "instruments" / "all.txt"
    if all_inst_path.exists():
        all_symbols = set()
        for line in all_inst_path.read_text().strip().split("\n"):
            parts = line.split("\t")
            if parts:
                all_symbols.add(parts[0])

        index_symbols = set()
        for line in inst_path.read_text().strip().split("\n"):
            parts = line.split("\t")
            if parts:
                index_symbols.add(parts[0])

        missing = index_symbols - all_symbols
        if missing:
            errors.append(f"{len(missing)} symbols have no feature data: {list(missing)[:5]}")
    else:
        logger.warning("  Cannot cross-check: all.txt not found")

    # 4. Per-date count spot-check (read from DB)
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        sample_counts = pd.read_sql(
            "SELECT time, COUNT(DISTINCT symbol) as cnt "
            "FROM index_constituents WHERE index_name = %s "
            "GROUP BY time ORDER BY time",
            conn, params=(index_name,),
        )
        conn.close()

        if not sample_counts.empty:
            lo_exp, hi_exp = EXPECTED_COUNT.get(index_name, (100, 5000))
            median_cnt = sample_counts["cnt"].median()
            logger.info("  Per-date median count: %.0f (expected %d-%d)", median_cnt, lo_exp, hi_exp)
            if not (lo_exp * 0.9 <= median_cnt <= hi_exp * 1.1):
                errors.append(f"Median per-date count {median_cnt:.0f} outside expected range")
    except Exception as e:
        logger.warning("  DB spot-check failed: %s", e)

    # Summary
    if errors:
        logger.error("VALIDATION FAILED for %s:", index_name)
        for e in errors:
            logger.error("  - %s", e)
        return False
    else:
        logger.info("VALIDATION PASSED for %s", index_name)
        return True


# ── Main ───────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(
        description="Sync index constituent history to DB and Qlib instruments files",
    )
    parser.add_argument("index", nargs="?", help="Index name: csi300, csi500, csi1000")
    parser.add_argument("--all", action="store_true", help="Sync all indices")
    parser.add_argument("--start", default="2015-01-01", help="Start date (default: 2015-01-01)")
    parser.add_argument("--end", default="2026-03-27", help="End date (default: 2026-03-27)")
    parser.add_argument("--skip-fetch", action="store_true",
                        help="Skip API fetch, only regenerate instruments from DB")

    args = parser.parse_args()

    indices = list(UNIVERSE_MAP.keys()) if args.all else [args.index]
    if not args.all and not args.index:
        parser.error("Specify an index name (csi300/csi500/csi1000) or --all")

    for idx in indices:
        if idx not in UNIVERSE_MAP:
            logger.error("Unknown index: %s (valid: %s)", idx, list(UNIVERSE_MAP.keys()))
            continue

        logger.info("=" * 60)
        logger.info("Syncing %s", idx)
        logger.info("=" * 60)

        if not args.skip_fetch:
            # Step 1: Fetch
            logger.info("[Step 1/3] Fetching from RiceQuant API...")
            df = fetch_constituents(idx, start_date=args.start, end_date=args.end)

            # Step 2: Store
            logger.info("[Step 2/3] Storing to TimescaleDB...")
            store_to_db(df)
        else:
            logger.info("[Step 1-2] Skipped (--skip-fetch)")

        # Step 3: Generate + Validate
        logger.info("[Step 3/3] Generating instruments file...")
        stats = generate_instruments(idx)
        ok = validate(idx, stats)

        if ok:
            logger.info("Done: %s", idx)
        else:
            logger.error("FAILED: %s", idx)
            sys.exit(1)


if __name__ == "__main__":
    main()
