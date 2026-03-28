#!/usr/bin/env python3
"""Backfill factor_values table for all admitted factors.

Computes factor values via Qlib and writes to DB for all factors
in library.yaml that don't yet have values in factor_values table.

Usage:
    cd /Users/xinzhan/.openclaw/workspace/quant_factor_system
    PYTHONPATH=src python3 scripts/backfill_factor_values.py [--dry-run]
"""

from __future__ import annotations

import argparse
import logging
import sys
import warnings

warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description="Backfill factor_values for all library factors")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done")
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
    from mining.publisher import FactorPublisher

    register_custom_operators()

    system = SystemConfig(qlib_data_dir=args.qlib_dir)
    config = MiningConfig(
        system=system,
        train_start=args.train_start,
        train_end=args.train_end,
        test_start=args.test_start,
    )

    # Check which factors already have values in DB
    conn = psycopg2.connect(config.system.database.connection_string)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT factor_name FROM factor_values")
    existing = {row[0] for row in cur.fetchall()}
    conn.close()

    # Get all library factors
    lib = FactorLibrary(config)
    factors = lib.list_factors()

    # Get full universe
    inst_dict = D.instruments("all")
    df_temp = D.features(
        instruments=inst_dict, fields=["$close"],
        start_time="2024-06-01", end_time="2024-06-30",
    )
    all_instruments = df_temp.index.get_level_values("instrument").unique().tolist()

    to_backfill = []
    for f in factors:
        factor_name = f"factor_{f['id']}"
        if factor_name in existing:
            logger.info("SKIP %s (%s) — already in DB", factor_name, f["name"])
        else:
            to_backfill.append(f)

    print(f"\n{len(to_backfill)} factors to backfill, {len(existing)} already in DB\n")

    if args.dry_run:
        for f in to_backfill:
            print(f"  Would backfill: factor_{f['id']} ({f['name']}): {f['expression'][:60]}...")
        print("\n(dry run — no values written)")
        return

    with FactorPublisher(config) as publisher:
        for i, f in enumerate(to_backfill):
            factor_id = f["id"]
            expr = f["expression"]
            print(f"[{i+1}/{len(to_backfill)}] Computing factor_{factor_id} ({f['name']})...")

            try:
                # Compute IS values
                vals_is = D.features(
                    instruments=all_instruments, fields=[expr],
                    start_time=args.train_start, end_time=args.train_end,
                )
                # Compute OOS values
                vals_oos = D.features(
                    instruments=all_instruments, fields=[expr],
                    start_time=args.test_start, end_time=None,
                )

                # Load factor detail for publisher
                factor_dict = lib.load_factor(factor_id)

                # Publish (writes to factor_meta + factor_values)
                publisher.publish(
                    factor_id=factor_id,
                    factor_dict=factor_dict,
                    factor_values_is=vals_is,
                    factor_values_oos=vals_oos,
                )
                print(f"  ✓ Done")

            except Exception as e:
                print(f"  ✗ Error: {e}")
                continue

    print(f"\nBackfill complete.")


if __name__ == "__main__":
    main()
