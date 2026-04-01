#!/usr/bin/env python3
"""Backfill factor_values table for all admitted factors.

Parallel computation (ThreadPoolExecutor) + COPY bulk insert for speed.

Usage:
    cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
    PYTHONPATH=src python3 scripts/backfill_factor_values.py [--dry-run] [--workers 4]
"""

from __future__ import annotations

import argparse
import io
import logging
import time
import sys
import warnings

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger(__name__)


def compute_one_factor(factor_id, expression, instruments, train_start, train_end, test_start):
    """Compute factor values for one factor. Runs in thread."""
    from qlib.data import D
    import pandas as pd

    vals_is = D.features(
        instruments=instruments, fields=[expression],
        start_time=train_start, end_time=train_end,
    )
    vals_oos = D.features(
        instruments=instruments, fields=[expression],
        start_time=test_start, end_time=None,
    )
    combined = pd.concat([vals_is, vals_oos])
    combined = combined[~combined.index.duplicated(keep="last")]
    return factor_id, combined


def copy_to_db(conn, factor_id, factor_values):
    """Bulk write factor values using COPY (much faster than INSERT)."""
    import pandas as pd

    factor_name = f"factor_{factor_id}"

    # Flatten MultiIndex (instrument, datetime) → (symbol, time, value)
    df = factor_values.iloc[:, [0]].reset_index()
    df.columns = ["symbol", "time", "value"]
    df = df.dropna(subset=["value"])
    df["factor_name"] = factor_name

    # Delete old values
    with conn.cursor() as cur:
        cur.execute("DELETE FROM factor_values WHERE factor_name = %s", (factor_name,))

    # COPY from StringIO buffer (10-50x faster than execute_values)
    buf = io.StringIO()
    for _, row in df.iterrows():
        buf.write(f"{row['time']}\t{row['symbol']}\t{factor_name}\t{row['value']}\n")
    buf.seek(0)

    with conn.cursor() as cur:
        cur.copy_from(buf, "factor_values", columns=("time", "symbol", "factor_name", "value"))

    conn.commit()
    return len(df)


def main():
    parser = argparse.ArgumentParser(description="Backfill factor_values (parallel + COPY)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--workers", type=int, default=4, help="Parallel computation threads")
    parser.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    parser.add_argument("--train-start", default="2020-01-01")
    parser.add_argument("--train-end", default="2024-12-31")
    parser.add_argument("--test-start", default="2024-07-01")
    args = parser.parse_args()

    import psycopg2
    import qlib
    from qlib.config import REG_CN, C

    qlib.init(provider_uri=args.qlib_dir, region=REG_CN)
    C.kernels = 1

    from qlib.data import D
    from mining.config import MiningConfig, SystemConfig
    from mining.library import FactorLibrary
    from mining.operators import register_custom_operators

    register_custom_operators()

    system = SystemConfig(qlib_data_dir=args.qlib_dir)
    config = MiningConfig(
        system=system,
        train_start=args.train_start,
        train_end=args.train_end,
        test_start=args.test_start,
    )

    # Check existing
    conn = psycopg2.connect(config.system.database.connection_string)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT factor_name FROM factor_values")
    existing = {row[0] for row in cur.fetchall()}
    conn.close()

    # Get factors to backfill
    lib = FactorLibrary(config)
    factors = lib.list_factors()

    inst_dict = D.instruments("all")
    df_temp = D.features(
        instruments=inst_dict, fields=["$close"],
        start_time="2024-06-01", end_time="2024-06-30",
    )
    all_instruments = df_temp.index.get_level_values("instrument").unique().tolist()

    to_backfill = [f for f in factors if f"factor_{f['id']}" not in existing]
    print(f"{len(to_backfill)} factors to backfill, {len(existing)} already in DB")

    if args.dry_run:
        for f in to_backfill:
            print(f"  factor_{f['id']} ({f['name']})")
        return

    # Phase 1: Parallel computation
    from concurrent.futures import ThreadPoolExecutor, as_completed

    print(f"\n=== Phase 1: Computing {len(to_backfill)} factors ({args.workers} threads) ===")
    t0 = time.time()
    computed = {}
    errors = []

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {
            pool.submit(
                compute_one_factor,
                f["id"], f["expression"], all_instruments,
                args.train_start, args.train_end, args.test_start,
            ): f
            for f in to_backfill
        }
        for future in as_completed(futures):
            f = futures[future]
            try:
                factor_id, values = future.result()
                computed[factor_id] = values
                print(f"  ✓ factor_{factor_id} ({f['name']}) — {len(values):,} rows")
            except Exception as e:
                errors.append(f)
                print(f"  ✗ factor_{f['id']} ({f['name']}): {e}")

    t_compute = time.time() - t0
    print(f"\nComputed: {len(computed)}, Errors: {len(errors)}, Time: {t_compute:.0f}s")

    # Phase 2: Sequential DB write (COPY is fast, DB connection not thread-safe)
    print(f"\n=== Phase 2: Writing to DB (COPY) ===")
    t1 = time.time()
    conn = psycopg2.connect(config.system.database.connection_string)
    total_rows = 0

    for factor_id, values in computed.items():
        try:
            n = copy_to_db(conn, factor_id, values)
            total_rows += n
            print(f"  ✓ factor_{factor_id}: {n:,} rows")
        except Exception as e:
            print(f"  ✗ factor_{factor_id}: {e}")
            conn.rollback()

    conn.close()
    t_write = time.time() - t1
    print(f"\nTotal: {total_rows:,} rows, Write time: {t_write:.0f}s")
    print(f"Grand total: {t_compute + t_write:.0f}s (compute: {t_compute:.0f}s + write: {t_write:.0f}s)")


if __name__ == "__main__":
    main()
