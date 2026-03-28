#!/usr/bin/env python3
"""
Sync extended daily data from rqdatac → TimescaleDB.

Fetches data NOT in market_daily:
  1. Backfill amount (total_turnover) for 2015-2024 into market_daily
  2. Shares outstanding → daily_extra (for turnover calculation)
  3. Market cap + valuation (PE/PB/PS/PCF) → daily_extra
  4. Trade count (num_trades) → daily_extra
  5. Industry classification → industry_map

All data stored in TimescaleDB as golden source.

Usage:
    PYTHONPATH=/Users/xinzhan/.openclaw/workspace \
    /Users/xinzhan/miniconda3/envs/quantfactor/bin/python scripts/sync_extended_data.py
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

BATCH_SIZE = 200  # stocks per rqdatac request


def get_conn():
    conn = psycopg2.connect(**DB_CONFIG)
    # Disable TimescaleDB decompression limit for bulk DML
    with conn.cursor() as cur:
        cur.execute("SET timescaledb.max_tuples_decompressed_per_dml_transaction = 0")
    conn.commit()
    return conn


def get_all_symbols():
    """Get all A-share stock codes from rqdatac."""
    insts = rq.all_instruments("CS")
    return sorted(insts["order_book_id"].tolist())


def to_internal(order_book_id: str) -> str:
    """600000.XSHG → SH600000"""
    code, exchange = order_book_id.split(".")
    if exchange in ("XSHG", "SH"):
        return f"SH{code}"
    elif exchange in ("XSHE", "SZ"):
        return f"SZ{code}"
    return order_book_id


# ── 1. Backfill amount into market_daily ──────────────────────────────

def backfill_amount(symbols: list):
    """Backfill total_turnover (amount) for 2015-2024 into market_daily."""
    logger.info("=" * 60)
    logger.info("[1/4] Backfilling amount (2015-01-01 ~ 2024-12-31)")
    logger.info("=" * 60)

    conn = get_conn()
    cursor = conn.cursor()

    # Process year by year to manage memory
    years = range(2015, 2025)
    total_updated = 0

    for year in years:
        start = f"{year}0101"
        end = f"{year}1231"
        year_updated = 0

        n_batches = (len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE
        for i in range(0, len(symbols), BATCH_SIZE):
            batch = symbols[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1

            try:
                df = rq.get_price(
                    order_book_ids=batch,
                    start_date=start,
                    end_date=end,
                    frequency="1d",
                    fields=["total_turnover"],
                    adjust_type="pre",
                )
            except Exception as e:
                logger.warning("  Year %d batch %d/%d failed: %s", year, batch_num, n_batches, e)
                time.sleep(1)
                continue

            if df is None or df.empty:
                continue

            df = df.reset_index()
            records = []
            for _, row in df.iterrows():
                amt = row.get("total_turnover")
                if pd.isna(amt) or amt == 0:
                    continue
                sym = to_internal(str(row["order_book_id"]))
                t = pd.to_datetime(row["date"])
                records.append((float(amt), t, sym))

            if records:
                for j in range(0, len(records), 2000):
                    chunk = records[j:j + 2000]
                    execute_values(
                        cursor,
                        "UPDATE market_daily SET amount = data.amount "
                        "FROM (VALUES %s) AS data(amount, time, symbol) "
                        "WHERE market_daily.time = data.time AND market_daily.symbol = data.symbol",
                        chunk,
                        template="(%s, %s::timestamp, %s)",
                    )
                    conn.commit()
                year_updated += len(records)

        total_updated += year_updated
        logger.info("  Year %d: updated %d rows", year, year_updated)

    cursor.close()
    conn.close()
    logger.info("Amount backfill complete: %d total updates", total_updated)
    return total_updated


# ── 2. Shares + Market Cap + Valuation → daily_extra ─────────────────

def sync_daily_extra(symbols: list):
    """Fetch shares, market_cap, valuation, num_trades → daily_extra."""
    logger.info("=" * 60)
    logger.info("[2/4] Syncing daily_extra (2015-01-01 ~ now)")
    logger.info("=" * 60)

    conn = get_conn()
    cursor = conn.cursor()

    # Process year by year
    current_year = datetime.now().year
    years = range(2015, current_year + 1)
    total_inserted = 0

    for year in years:
        start = f"{year}0101"
        end = f"{year}1231" if year < current_year else datetime.now().strftime("%Y%m%d")
        year_inserted = 0

        n_batches = (len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE
        for i in range(0, len(symbols), BATCH_SIZE):
            batch = symbols[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1

            # --- Shares ---
            try:
                shares_df = rq.get_shares(
                    batch, start_date=start, end_date=end,
                    fields=["total", "circulation_a"],
                )
            except Exception as e:
                logger.warning("  Year %d batch %d shares failed: %s", year, batch_num, e)
                shares_df = None
                time.sleep(1)

            # --- Factor (market_cap, PE, PB, PS, PCF) ---
            try:
                factor_df = rq.get_factor(
                    batch, factor=["market_cap", "pe_ratio", "pb_ratio", "ps_ratio", "pcf_ratio"],
                    start_date=start, end_date=end,
                )
            except Exception as e:
                logger.warning("  Year %d batch %d factor failed: %s", year, batch_num, e)
                factor_df = None
                time.sleep(1)

            # --- Price (num_trades + volume for turnover calc) ---
            try:
                price_df = rq.get_price(
                    batch, start_date=start, end_date=end,
                    frequency="1d", fields=["volume", "num_trades"],
                    adjust_type="pre",
                )
            except Exception as e:
                logger.warning("  Year %d batch %d price failed: %s", year, batch_num, e)
                price_df = None
                time.sleep(1)

            # --- Merge all into records ---
            # Build a combined DataFrame keyed by (order_book_id, date)
            merged = {}

            if shares_df is not None and not shares_df.empty:
                sdf = shares_df.reset_index()
                for _, row in sdf.iterrows():
                    key = (str(row["order_book_id"]), pd.to_datetime(row["date"]))
                    if key not in merged:
                        merged[key] = {}
                    merged[key]["total_shares"] = row.get("total")
                    merged[key]["circ_shares"] = row.get("circulation_a")

            if factor_df is not None and not factor_df.empty:
                fdf = factor_df.reset_index()
                for _, row in fdf.iterrows():
                    key = (str(row["order_book_id"]), pd.to_datetime(row["date"]))
                    if key not in merged:
                        merged[key] = {}
                    merged[key]["market_cap"] = row.get("market_cap")
                    merged[key]["pe_ratio"] = row.get("pe_ratio")
                    merged[key]["pb_ratio"] = row.get("pb_ratio")
                    merged[key]["ps_ratio"] = row.get("ps_ratio")
                    merged[key]["pcf_ratio"] = row.get("pcf_ratio")

            if price_df is not None and not price_df.empty:
                pdf = price_df.reset_index()
                for _, row in pdf.iterrows():
                    key = (str(row["order_book_id"]), pd.to_datetime(row["date"]))
                    if key not in merged:
                        merged[key] = {}
                    merged[key]["volume"] = row.get("volume")
                    merged[key]["num_trades"] = row.get("num_trades")

            # Compute turnover_rate and build insert records
            records = []
            for (ob_id, dt), data in merged.items():
                sym = to_internal(ob_id)
                circ = data.get("circ_shares")
                vol = data.get("volume")
                turnover = None
                if circ and vol and circ > 0 and not pd.isna(circ) and not pd.isna(vol):
                    turnover = vol / circ

                circ_mcap = None
                close_price = None
                if circ and not pd.isna(circ) and data.get("market_cap") and data.get("total_shares"):
                    ts = data["total_shares"]
                    if not pd.isna(ts) and ts > 0:
                        circ_mcap = data["market_cap"] * circ / ts

                def _f(v):
                    if v is None or (isinstance(v, float) and np.isnan(v)):
                        return None
                    return float(v)

                records.append((
                    dt, sym,
                    _f(turnover),
                    _f(data.get("market_cap")),
                    _f(circ_mcap),
                    _f(data.get("pe_ratio")),
                    _f(data.get("pb_ratio")),
                    _f(data.get("ps_ratio")),
                    _f(data.get("pcf_ratio")),
                    _f(data.get("total_shares")),
                    _f(circ),
                    _f(data.get("num_trades")),
                ))

            if records:
                sql = """
                    INSERT INTO daily_extra
                    (time, symbol, turnover_rate, market_cap, circ_market_cap,
                     pe_ratio, pb_ratio, ps_ratio, pcf_ratio,
                     total_shares, circ_shares, num_trades)
                    VALUES %s
                    ON CONFLICT (time, symbol) DO UPDATE SET
                        turnover_rate = EXCLUDED.turnover_rate,
                        market_cap = EXCLUDED.market_cap,
                        circ_market_cap = EXCLUDED.circ_market_cap,
                        pe_ratio = EXCLUDED.pe_ratio,
                        pb_ratio = EXCLUDED.pb_ratio,
                        ps_ratio = EXCLUDED.ps_ratio,
                        pcf_ratio = EXCLUDED.pcf_ratio,
                        total_shares = EXCLUDED.total_shares,
                        circ_shares = EXCLUDED.circ_shares,
                        num_trades = EXCLUDED.num_trades
                """
                for j in range(0, len(records), 5000):
                    execute_values(cursor, sql, records[j:j + 5000])
                    conn.commit()
                year_inserted += len(records)

            if batch_num % 5 == 0:
                logger.info("  Year %d: batch %d/%d (%d records so far)",
                            year, batch_num, n_batches, year_inserted)

        total_inserted += year_inserted
        logger.info("  Year %d: inserted %d rows", year, year_inserted)

    cursor.close()
    conn.close()
    logger.info("Daily extra sync complete: %d total rows", total_inserted)
    return total_inserted


# ── 3. Industry classification → industry_map ────────────────────────

def sync_industry(symbols: list):
    """Fetch industry classification for all symbols."""
    logger.info("=" * 60)
    logger.info("[3/4] Syncing industry classification")
    logger.info("=" * 60)

    conn = get_conn()
    cursor = conn.cursor()

    records = []
    n_batches = (len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(symbols), BATCH_SIZE):
        batch = symbols[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        try:
            ind_df = rq.get_instrument_industry(batch, source="citics")
        except Exception as e:
            logger.warning("  Batch %d/%d failed: %s", batch_num, n_batches, e)
            time.sleep(1)
            continue

        if ind_df is None or ind_df.empty:
            continue

        ind_df = ind_df.reset_index()
        for _, row in ind_df.iterrows():
            sym = to_internal(str(row["order_book_id"]))
            code = str(row.get("first_industry_code", "")) if pd.notna(row.get("first_industry_code")) else None
            name = str(row.get("first_industry_name", "")) if pd.notna(row.get("first_industry_name")) else None
            records.append((sym, "citics", code, name))

        if batch_num % 10 == 0:
            logger.info("  Batch %d/%d", batch_num, n_batches)

    if records:
        sql = """
            INSERT INTO industry_map (symbol, source, industry_code, industry_name, updated_at)
            VALUES %s
            ON CONFLICT (symbol, source) DO UPDATE SET
                industry_code = EXCLUDED.industry_code,
                industry_name = EXCLUDED.industry_name,
                updated_at = NOW()
        """
        execute_values(cursor, sql, records, template="(%s, %s, %s, %s, NOW())")
        conn.commit()

    cursor.close()
    conn.close()
    logger.info("Industry sync complete: %d symbols", len(records))
    return len(records)


# ── 4. Validation ────────────────────────────────────────────────────

def validate():
    """Validate all extended data in DB."""
    logger.info("=" * 60)
    logger.info("[4/4] Validating")
    logger.info("=" * 60)

    conn = get_conn()
    cursor = conn.cursor()
    errors = []

    # 1. Amount backfill check
    cursor.execute("""
        SELECT EXTRACT(YEAR FROM time)::int as y,
               COUNT(*) as total,
               COUNT(CASE WHEN amount > 0 THEN 1 END) as amount_ok
        FROM market_daily
        WHERE time >= '2015-01-01'
        GROUP BY y ORDER BY y
    """)
    rows = cursor.fetchall()
    for year, total, amount_ok in rows:
        pct = amount_ok / total * 100 if total > 0 else 0
        status = "✓" if pct > 80 else "✗"
        logger.info("  %s Amount %d: %d/%d (%.1f%%)", status, year, amount_ok, total, pct)
        if pct < 50 and year >= 2016:
            errors.append(f"Amount coverage too low for {year}: {pct:.1f}%")

    # 2. Daily extra coverage
    cursor.execute("""
        SELECT COUNT(*) as total,
               COUNT(CASE WHEN turnover_rate IS NOT NULL THEN 1 END) as turnover_ok,
               COUNT(CASE WHEN market_cap IS NOT NULL THEN 1 END) as mcap_ok,
               COUNT(CASE WHEN pe_ratio IS NOT NULL THEN 1 END) as pe_ok,
               COUNT(DISTINCT symbol) as n_symbols,
               MIN(time)::date as min_date, MAX(time)::date as max_date
        FROM daily_extra
    """)
    row = cursor.fetchone()
    total, turnover_ok, mcap_ok, pe_ok, n_syms, min_d, max_d = row
    logger.info("  Daily extra: %d rows, %d symbols, %s ~ %s", total, n_syms, min_d, max_d)
    logger.info("    Turnover: %d (%.1f%%)", turnover_ok, turnover_ok / total * 100 if total > 0 else 0)
    logger.info("    Market cap: %d (%.1f%%)", mcap_ok, mcap_ok / total * 100 if total > 0 else 0)
    logger.info("    PE ratio: %d (%.1f%%)", pe_ok, pe_ok / total * 100 if total > 0 else 0)
    if total == 0:
        errors.append("daily_extra is empty!")

    # 3. Industry map
    cursor.execute("SELECT COUNT(*), COUNT(DISTINCT industry_code) FROM industry_map")
    n_ind, n_codes = cursor.fetchone()
    logger.info("  Industry map: %d symbols, %d unique codes", n_ind, n_codes)
    if n_ind == 0:
        errors.append("industry_map is empty!")

    # 4. Cross-check: daily_extra symbols should be subset of market_daily symbols
    cursor.execute("""
        SELECT COUNT(DISTINCT de.symbol)
        FROM daily_extra de
        LEFT JOIN (SELECT DISTINCT symbol FROM market_daily) pd ON pd.symbol = de.symbol
        WHERE pd.symbol IS NULL
    """)
    orphan = cursor.fetchone()[0]
    if orphan > 0:
        errors.append(f"{orphan} symbols in daily_extra not in market_daily")
    logger.info("  Orphan symbols in daily_extra: %d", orphan)

    cursor.close()
    conn.close()

    if errors:
        logger.error("VALIDATION ISSUES:")
        for e in errors:
            logger.error("  • %s", e)
        return False
    else:
        logger.info("✅ All validations passed")
        return True


# ── Main ─────────────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("Extended Data Sync: rqdatac → TimescaleDB")
    logger.info("=" * 60)

    logger.info("Initializing rqdatac...")
    rq.init()

    symbols = get_all_symbols()
    logger.info("Total A-share symbols: %d", len(symbols))

    # Step 1: Backfill amount
    backfill_amount(symbols)

    # Step 2: Daily extra (shares, market cap, valuation, trades)
    sync_daily_extra(symbols)

    # Step 3: Industry classification
    sync_industry(symbols)

    # Step 4: Validate
    ok = validate()

    if ok:
        logger.info("\n✅ Extended data sync complete and validated!")
    else:
        logger.warning("\n⚠️  Sync complete with validation issues (see above)")


if __name__ == "__main__":
    main()
