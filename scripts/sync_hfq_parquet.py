#!/usr/bin/env python3
"""Sync HFQ (后复权) OHLCV+limit parquet for the backtest engine.

Writes ``storage/cache/market_daily_hfq.parquet`` with MultiIndex
``(datetime, instrument)`` and columns:
    open, high, low, close, volume, amount, market_cap, turnover_rate,
    limit_up, limit_down, returns_1d

This is a one-shot, idempotent script. Re-running it overwrites the parquet
in place. Default range: 2015-01-01 → 2024-12-31 (extends past existing qfq
parquet which currently ends 2023-12-29 in this repo).

Why a separate parquet (not DB):
- TimescaleDB market_daily already holds qfq; mixing schemes in one table
  invites silent bugs.
- The backtest engine reads the parquet directly (per spec §3.2).
- Phase 1-3 mining stays untouched on qfq.

Usage::

    PYTHONPATH=src python3 scripts/sync_hfq_parquet.py
    PYTHONPATH=src python3 scripts/sync_hfq_parquet.py --start 2024-01-01 --end 2024-12-31

Requires ``RQDATAC_CONF`` in ``.env``. Without a license the script exits 1.
"""
from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

OUT_PATH = Path("storage/cache/market_daily_hfq.parquet")

FIELDS = [
    "open", "high", "low", "close", "volume", "total_turnover",
    "limit_up", "limit_down",
]


def _to_qlib_symbol(order_book_id: str) -> str:
    """Convert RiceQuant order_book_id to internal symbol."""
    if order_book_id.endswith(".XSHG"):
        return f"SH{order_book_id.split('.')[0]}"
    if order_book_id.endswith(".XSHE"):
        return f"SZ{order_book_id.split('.')[0]}"
    return order_book_id


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sync HFQ parquet from RiceQuant."
    )
    parser.add_argument("--start", default="2015-01-01")
    parser.add_argument("--end", default="2024-12-31")
    parser.add_argument(
        "--out", default=str(OUT_PATH),
        help=f"Output parquet path (default: {OUT_PATH}).",
    )
    parser.add_argument(
        "--instruments-source", default="qlib",
        choices=("qlib", "rqdatac"),
        help="Source for instrument list. 'qlib' reads "
             "~/.qlib/qlib_data/cn_data_1d/instruments/all.txt; 'rqdatac' "
             "calls rq.all_instruments(type='CS').",
    )
    args = parser.parse_args()

    # Import rqdatac late so the script's --help works without the license.
    try:
        import rqdatac as rq  # type: ignore
    except ImportError:
        logger.error("rqdatac not installed; pip install rqdatac")
        sys.exit(1)

    rqconf = os.environ.get("RQDATAC_CONF")
    if not rqconf:
        from dotenv import load_dotenv
        load_dotenv()
        rqconf = os.environ.get("RQDATAC_CONF")
    if not rqconf:
        logger.error(
            "RQDATAC_CONF env var not set; configure RiceQuant license in .env"
        )
        sys.exit(1)
    rq.init()

    if args.instruments_source == "qlib":
        qlib_inst = Path("~/.qlib/qlib_data/cn_data_1d/instruments/all.txt").expanduser()
        if not qlib_inst.exists():
            logger.error("qlib instruments file missing: %s", qlib_inst)
            sys.exit(1)
        symbols = sorted({
            line.split("\t", 1)[0] for line in qlib_inst.read_text().splitlines() if line
        })
    else:
        all_inst = rq.all_instruments(type="CS")
        symbols = sorted({_to_qlib_symbol(s) for s in all_inst.order_book_id.tolist()})
    logger.info("symbols: %d", len(symbols))

    # rq expects order_book_ids in its own format
    order_book_ids = [
        sym.replace("SH", "") + ".XSHG" if sym.startswith("SH")
        else sym.replace("SZ", "") + ".XSHE" if sym.startswith("SZ")
        else sym
        for sym in symbols
    ]

    logger.info("fetching daily HFQ %s → %s", args.start, args.end)
    data = rq.get_price(
        order_book_ids=order_book_ids,
        start_date=args.start,
        end_date=args.end,
        frequency="1d",
        fields=FIELDS,
        adjust_type="post",  # ← HFQ
    )
    if data is None or data.empty:
        logger.error("rq.get_price returned empty")
        sys.exit(1)

    # MultiIndex (order_book_id, date) → (datetime, instrument)
    data = data.reset_index()
    data["instrument"] = data["order_book_id"].apply(_to_qlib_symbol)
    data["datetime"] = pd.to_datetime(data["date"])
    data = data.drop(columns=["order_book_id", "date"])
    data = data.rename(columns={"total_turnover": "amount"})

    # Add market_cap + turnover_rate from valuation snapshots (best-effort)
    logger.info("fetching market_cap + turnover_rate")
    val = rq.get_factor(
        order_book_ids,
        ["market_cap_3", "turnover_rate"],
        start_date=args.start,
        end_date=args.end,
    )
    if val is not None and not val.empty:
        val = val.reset_index()
        val["instrument"] = val["order_book_id"].apply(_to_qlib_symbol)
        val["datetime"] = pd.to_datetime(val["date"])
        val = val.drop(columns=["order_book_id", "date"])
        val = val.rename(columns={"market_cap_3": "market_cap"})
        data = data.merge(val, on=["datetime", "instrument"], how="left")
    else:
        data["market_cap"] = pd.NA
        data["turnover_rate"] = pd.NA

    # returns_1d (forward return over current close) for limit-detection consistency
    data = data.sort_values(["instrument", "datetime"])
    data["returns_1d"] = data.groupby("instrument")["close"].shift(-1) / data["close"] - 1

    # MultiIndex + downcast for size
    data = data.set_index(["datetime", "instrument"]).sort_index()
    for col in ["open", "high", "low", "close", "limit_up", "limit_down",
                "amount", "volume", "market_cap", "turnover_rate", "returns_1d"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce").astype("float32")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(out.suffix + ".tmp")
    data.to_parquet(tmp)
    os.replace(tmp, out)
    logger.info(
        "wrote %s — %d rows, %d symbols, %s ~ %s",
        out, len(data),
        data.index.get_level_values("instrument").nunique(),
        data.index.get_level_values("datetime").min().date(),
        data.index.get_level_values("datetime").max().date(),
    )


if __name__ == "__main__":
    main()
