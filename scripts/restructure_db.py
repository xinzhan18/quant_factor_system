#!/usr/bin/env python3
"""
Restructure quant_data database.

Before:
  19 tables, mixed naming, one table per factor, messy.

After:
  market_daily        ← OHLCV + amount + limit (renamed from price_daily)
  market_1min         ← minute bars (renamed from price_1min)
  ref_valuation       ← PE/PB/PS/PCF/market_cap (from daily_extra)
  ref_shares          ← total_shares/circ_shares/turnover_rate (from daily_extra)
  ref_industry        ← industry classification (renamed from industry_map)
  ref_ex_factor       ← dividend adjustment factors (new, for future)
  factor_values       ← all computed factor values in one table (new)
  factor_meta         ← factor metadata (renamed from mining_factors)

Dropped:
  factor_return_*, factor_momentum_*, factor_dist_*, factor_volatility_*,
  factor_sentiment_*, factor_intraday_*, factor_config,
  mining_factor_values, price_5min, daily_extra

Usage:
    PYTHONPATH=src python3 scripts/restructure_db.py
"""

import logging
import psycopg2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "quant_data",
    "user": "postgres",
    "password": "postgres",
}


def get_conn():
    conn = psycopg2.connect(**DB_CONFIG)
    with conn.cursor() as cur:
        cur.execute("SET timescaledb.max_tuples_decompressed_per_dml_transaction = 0")
    conn.commit()
    return conn


def run(conn, sql, desc=""):
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()
        logger.info("✓ %s", desc)
    except Exception as e:
        conn.rollback()
        if "does not exist" in str(e) or "already exists" in str(e):
            logger.info("⏭ %s (skipped: %s)", desc, str(e).split("\n")[0])
        else:
            logger.error("✗ %s: %s", desc, e)
            raise


def main():
    conn = get_conn()

    logger.info("=" * 60)
    logger.info("Step 1: Rename core tables")
    logger.info("=" * 60)

    run(conn, "ALTER TABLE price_daily RENAME TO market_daily",
        "price_daily → market_daily")
    run(conn, "ALTER TABLE price_1min RENAME TO market_1min",
        "price_1min → market_1min")
    run(conn, "ALTER TABLE industry_map RENAME TO ref_industry",
        "industry_map → ref_industry")

    logger.info("=" * 60)
    logger.info("Step 2: Create new reference tables from daily_extra")
    logger.info("=" * 60)

    # ref_valuation: PE/PB/PS/PCF/market_cap
    run(conn, """
        CREATE TABLE ref_valuation AS
        SELECT time, symbol, market_cap, circ_market_cap,
               pe_ratio, pb_ratio, ps_ratio, pcf_ratio
        FROM daily_extra
        WHERE market_cap IS NOT NULL
    """, "Create ref_valuation from daily_extra")

    run(conn, """
        ALTER TABLE ref_valuation
        ADD CONSTRAINT uix_ref_valuation UNIQUE (time, symbol)
    """, "Add unique constraint to ref_valuation")

    run(conn, """
        CREATE INDEX ix_ref_valuation_symbol ON ref_valuation(symbol, time)
    """, "Index ref_valuation")

    # ref_shares: shares + turnover
    run(conn, """
        CREATE TABLE ref_shares AS
        SELECT time, symbol, total_shares, circ_shares, turnover_rate, num_trades
        FROM daily_extra
        WHERE total_shares IS NOT NULL OR turnover_rate IS NOT NULL
    """, "Create ref_shares from daily_extra")

    run(conn, """
        ALTER TABLE ref_shares
        ADD CONSTRAINT uix_ref_shares UNIQUE (time, symbol)
    """, "Add unique constraint to ref_shares")

    run(conn, """
        CREATE INDEX ix_ref_shares_symbol ON ref_shares(symbol, time)
    """, "Index ref_shares")

    # ref_ex_factor: for future use
    run(conn, """
        CREATE TABLE IF NOT EXISTS ref_ex_factor (
            symbol      TEXT NOT NULL,
            ex_date     DATE NOT NULL,
            ex_factor   DOUBLE PRECISION NOT NULL,
            UNIQUE(symbol, ex_date)
        )
    """, "Create ref_ex_factor (empty, for future)")

    run(conn, """
        CREATE INDEX IF NOT EXISTS ix_ref_ex_factor_symbol ON ref_ex_factor(symbol, ex_date)
    """, "Index ref_ex_factor")

    logger.info("=" * 60)
    logger.info("Step 3: Create unified factor_values table")
    logger.info("=" * 60)

    run(conn, """
        CREATE TABLE IF NOT EXISTS factor_values (
            time        TIMESTAMP NOT NULL,
            symbol      TEXT NOT NULL,
            factor_name TEXT NOT NULL,
            value       DOUBLE PRECISION,
            UNIQUE(time, symbol, factor_name)
        )
    """, "Create factor_values")

    run(conn, """
        CREATE INDEX IF NOT EXISTS ix_factor_values_factor ON factor_values(factor_name, time)
    """, "Index factor_values")

    # Rename mining_factors → factor_meta
    run(conn, "ALTER TABLE mining_factors RENAME TO factor_meta",
        "mining_factors → factor_meta")

    logger.info("=" * 60)
    logger.info("Step 4: Drop old tables")
    logger.info("=" * 60)

    old_tables = [
        "daily_extra",
        "price_5min",
        "factor_config",
        "factor_return_1d",
        "factor_return_5d",
        "factor_return_20d",
        "factor_return_60d",
        "factor_momentum_20",
        "factor_momentum_60",
        "factor_volatility_20",
        "factor_dist_ma10",
        "factor_dist_ma20",
        "factor_sentiment_overflow",
        "factor_intraday_momentum",
        "mining_factor_values",
    ]

    for table in old_tables:
        run(conn, f"DROP TABLE IF EXISTS {table} CASCADE", f"Drop {table}")

    logger.info("=" * 60)
    logger.info("Step 5: Verify final state")
    logger.info("=" * 60)

    with conn.cursor() as cur:
        cur.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        tables = [r[0] for r in cur.fetchall()]

    logger.info("Final tables (%d):", len(tables))
    for t in tables:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {t}")
            count = cur.fetchone()[0]
        logger.info("  %-25s %d rows", t, count)

    conn.close()

    expected = {"market_daily", "market_1min", "ref_valuation", "ref_shares",
                "ref_industry", "ref_ex_factor", "factor_values", "factor_meta"}
    actual = set(tables)
    extra = actual - expected
    missing = expected - actual

    if missing:
        logger.error("Missing tables: %s", missing)
    if extra:
        logger.warning("Unexpected tables (may be OK): %s", extra)
    if not missing:
        logger.info("✅ Restructure complete!")


if __name__ == "__main__":
    main()
