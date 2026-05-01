#!/usr/bin/env python3
"""
Sync rqdatac financial factors → ref_financials TimescaleDB table.

Pulls 20 TTM financial factors via rqdatac.get_factor() year-by-year, in
batches of 200 stocks. Idempotent ON CONFLICT update.

Fields fall in 5 groups:
    Profitability: roe / roa / roic / gross_margin / op_margin
    Solvency:      debt_to_asset / debt_to_equity / current_ratio
    Efficiency:    asset_turnover / inv_turnover / ar_turnover
    Growth:        rev_growth / profit_growth / asset_growth
    Per-share:     eps / bps / ocfps / div_yield
    Valuation:     pcf_total / peg

Usage:
    PYTHONPATH=src /Users/xinzhan/miniconda3/envs/quantfactor/bin/python \\
        scripts/sync_financials.py [--start YEAR] [--end YEAR]
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime

import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
import rqdatac as rq

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

DB_CONFIG = {
    "host": os.getenv("TIMESCALE_HOST", "localhost"),
    "port": int(os.getenv("TIMESCALE_PORT", "5432")),
    "database": os.getenv("TIMESCALE_DB", "quant_data"),
    "user": os.getenv("TIMESCALE_USER", "postgres"),
    "password": os.getenv("TIMESCALE_PASSWORD", "postgres"),
}

BATCH_SIZE = 200

RQ_FIELDS: list[str] = [
    # Profitability
    "return_on_equity_ttm",
    "return_on_asset_ttm",
    "return_on_invested_capital_ttm",
    "gross_profit_margin_ttm",
    "operating_profit_margin_ttm",
    # Solvency
    "debt_to_asset_ratio_ttm",
    "debt_to_equity_ratio_ttm",
    "current_ratio_ttm",
    # Efficiency
    "total_asset_turnover_ttm",
    "inventory_turnover_ttm",
    "account_receivable_turnover_rate_ttm",
    # Growth
    "operating_revenue_growth_ratio_ttm",
    "net_profit_growth_ratio_ttm",
    "net_asset_growth_ratio_ttm",
    # Per-share / Yield
    "eps_ttm",
    "book_value_per_share_ttm",
    "operating_cash_flow_per_share_ttm",
    "dividend_yield_ttm",
    # Valuation
    "pcf_ratio_total_ttm",
    "peg_ratio_ttm",
]


# ── DB setup ──────────────────────────────────────────────────────────


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS ref_financials (
    time TIMESTAMP NOT NULL,
    symbol TEXT NOT NULL,
    return_on_equity_ttm DOUBLE PRECISION,
    return_on_asset_ttm DOUBLE PRECISION,
    return_on_invested_capital_ttm DOUBLE PRECISION,
    gross_profit_margin_ttm DOUBLE PRECISION,
    operating_profit_margin_ttm DOUBLE PRECISION,
    debt_to_asset_ratio_ttm DOUBLE PRECISION,
    debt_to_equity_ratio_ttm DOUBLE PRECISION,
    current_ratio_ttm DOUBLE PRECISION,
    total_asset_turnover_ttm DOUBLE PRECISION,
    inventory_turnover_ttm DOUBLE PRECISION,
    account_receivable_turnover_rate_ttm DOUBLE PRECISION,
    operating_revenue_growth_ratio_ttm DOUBLE PRECISION,
    net_profit_growth_ratio_ttm DOUBLE PRECISION,
    net_asset_growth_ratio_ttm DOUBLE PRECISION,
    eps_ttm DOUBLE PRECISION,
    book_value_per_share_ttm DOUBLE PRECISION,
    operating_cash_flow_per_share_ttm DOUBLE PRECISION,
    dividend_yield_ttm DOUBLE PRECISION,
    pcf_ratio_total_ttm DOUBLE PRECISION,
    peg_ratio_ttm DOUBLE PRECISION
);

CREATE UNIQUE INDEX IF NOT EXISTS uix_ref_financials
    ON ref_financials(time, symbol);
CREATE INDEX IF NOT EXISTS ix_ref_financials_symbol
    ON ref_financials(symbol, time);
"""


def get_conn():
    return psycopg2.connect(**DB_CONFIG)


def ensure_table():
    conn = get_conn()
    with conn.cursor() as cur:
        cur.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()
    logger.info("ref_financials table ready")


# ── Symbol helpers ────────────────────────────────────────────────────


def get_all_symbols() -> list[str]:
    insts = rq.all_instruments("CS")
    return sorted(insts["order_book_id"].tolist())


def to_internal(order_book_id: str) -> str:
    """600000.XSHG → SH600000"""
    code, exchange = order_book_id.split(".")
    if exchange in ("XSHG", "SH"):
        return f"SH{code}"
    if exchange in ("XSHE", "SZ"):
        return f"SZ{code}"
    return order_book_id


# ── Sync ──────────────────────────────────────────────────────────────


UPSERT_COLS = ["time", "symbol"] + RQ_FIELDS
UPSERT_SQL = f"""
INSERT INTO ref_financials ({', '.join(UPSERT_COLS)}) VALUES %s
ON CONFLICT (time, symbol) DO UPDATE SET
{', '.join(f'{c}=EXCLUDED.{c}' for c in RQ_FIELDS)}
"""


def sync_year(symbols: list[str], year: int) -> int:
    """Pull one calendar year of financial factors → ref_financials."""
    start = f"{year}0101"
    today = datetime.now()
    end = f"{year}1231" if year < today.year else today.strftime("%Y%m%d")

    conn = get_conn()
    cur = conn.cursor()
    inserted = 0

    n_batches = (len(symbols) + BATCH_SIZE - 1) // BATCH_SIZE
    for i in range(0, len(symbols), BATCH_SIZE):
        batch = symbols[i:i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        try:
            df = rq.get_factor(
                batch, factor=RQ_FIELDS,
                start_date=start, end_date=end,
            )
        except Exception as e:
            logger.warning("  Year %d batch %d/%d failed: %s",
                           year, batch_num, n_batches, e)
            time.sleep(1)
            continue

        if df is None or df.empty:
            continue

        # MultiIndex (order_book_id, date) → flat
        df = df.reset_index()
        # Build records list[(time, symbol, *RQ_FIELDS)]
        records = []
        for _, row in df.iterrows():
            sym = to_internal(str(row["order_book_id"]))
            t = pd.to_datetime(row["date"])
            vals = [row.get(c) for c in RQ_FIELDS]
            # Skip if all values NaN
            if all(pd.isna(v) for v in vals):
                continue
            cleaned = [None if pd.isna(v) else float(v) for v in vals]
            records.append((t, sym, *cleaned))

        if not records:
            continue

        # Chunked upsert
        for j in range(0, len(records), 2000):
            chunk = records[j:j + 2000]
            execute_values(cur, UPSERT_SQL, chunk, page_size=2000)
            conn.commit()
        inserted += len(records)

        if batch_num % 5 == 0 or batch_num == n_batches:
            logger.info("  Year %d batch %d/%d: cumulative %d rows",
                        year, batch_num, n_batches, inserted)

    cur.close()
    conn.close()
    logger.info("Year %d done: %d rows", year, inserted)
    return inserted


# ── Main ──────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int, default=2015)
    parser.add_argument("--end", type=int, default=datetime.now().year)
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("Sync financials: rqdatac → ref_financials")
    logger.info("Years: %d ~ %d, fields: %d", args.start, args.end, len(RQ_FIELDS))
    logger.info("=" * 60)

    logger.info("Initializing rqdatac...")
    rq.init()

    ensure_table()

    logger.info("Fetching symbol list...")
    symbols = get_all_symbols()
    logger.info("  %d symbols", len(symbols))

    total = 0
    t0 = time.perf_counter()
    for year in range(args.start, args.end + 1):
        try:
            total += sync_year(symbols, year)
        except KeyboardInterrupt:
            logger.warning("Interrupted by user — partial sync persisted")
            sys.exit(130)
        except Exception as e:
            logger.error("Year %d FAILED: %s", year, e, exc_info=True)

    elapsed = time.perf_counter() - t0
    logger.info("=" * 60)
    logger.info("DONE: %d total rows in %.1f min", total, elapsed / 60)


if __name__ == "__main__":
    main()
