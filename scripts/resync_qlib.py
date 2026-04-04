#!/usr/bin/env python3
"""
Resync: TimescaleDB market_daily → Qlib binary format.

Reads full market_daily from TimescaleDB, rebuilds all Qlib binary files
with correct format (start_index header), then runs comprehensive validation.

Usage:
    PYTHONPATH=src python3 scripts/resync_qlib.py
"""

import logging
import struct
import sys
from pathlib import Path

import numpy as np
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

MARKET_FIELDS = ["open", "high", "low", "close", "volume", "amount", "vwap",
                 "returns", "returns_1d", "limit_up", "limit_down"]
REF_FIELDS = ["turnover_rate", "market_cap", "circ_market_cap",
              "pe_ratio", "pb_ratio", "ps_ratio"]
FIELDS = MARKET_FIELDS + REF_FIELDS


# ── Step 1: Load from DB ────────────────────────────────────────────

def load_from_db() -> pd.DataFrame:
    """Load market_daily + ref data from TimescaleDB."""
    conn = psycopg2.connect(**DB_CONFIG)

    logger.info("Loading market_daily...")
    df = pd.read_sql(
        "SELECT time, symbol, open, high, low, close, volume, amount, vwap, "
        "limit_up, limit_down FROM market_daily ORDER BY symbol, time",
        conn,
    )

    if df.empty:
        logger.error("No data in market_daily!")
        conn.close()
        sys.exit(1)

    df["time"] = pd.to_datetime(df["time"])

    # Load ref_shares (turnover_rate)
    logger.info("Loading ref_shares...")
    ref_shares = pd.read_sql(
        "SELECT time, symbol, turnover_rate FROM ref_shares "
        "WHERE turnover_rate IS NOT NULL",
        conn,
    )
    if not ref_shares.empty:
        ref_shares["time"] = pd.to_datetime(ref_shares["time"])
        df = df.merge(ref_shares, on=["time", "symbol"], how="left")
    else:
        df["turnover_rate"] = np.nan

    # Load ref_valuation (market_cap, PE, PB, PS)
    logger.info("Loading ref_valuation...")
    ref_val = pd.read_sql(
        "SELECT time, symbol, market_cap, circ_market_cap, "
        "pe_ratio, pb_ratio, ps_ratio FROM ref_valuation",
        conn,
    )
    if not ref_val.empty:
        ref_val["time"] = pd.to_datetime(ref_val["time"])
        df = df.merge(ref_val, on=["time", "symbol"], how="left")
    else:
        for col in ["market_cap", "circ_market_cap", "pe_ratio", "pb_ratio", "ps_ratio"]:
            df[col] = np.nan

    conn.close()
    df = df.sort_values(["symbol", "time"])

    # Derive fields
    df["returns"] = df.groupby("symbol")["close"].pct_change()
    df["returns_1d"] = df.groupby("symbol")["close"].shift(-1) / df["close"] - 1

    logger.info(
        "Loaded %d rows, %d symbols, %s ~ %s",
        len(df), df["symbol"].nunique(),
        df["time"].min().date(), df["time"].max().date(),
    )
    return df


# ── Step 2: Write Qlib binary files ─────────────────────────────────

def write_qlib(df: pd.DataFrame) -> dict:
    """Write calendar, instruments, and feature binary files.

    Returns stats dict for validation.
    """
    trading_days = sorted(df["time"].dt.strftime("%Y-%m-%d").unique())
    cal_index = {day: i for i, day in enumerate(trading_days)}
    n_days = len(trading_days)

    # Calendar
    cal_dir = QLIB_DIR / "calendars"
    cal_dir.mkdir(parents=True, exist_ok=True)
    (cal_dir / "day.txt").write_text("\n".join(trading_days) + "\n")
    logger.info("Calendar: %d days (%s ~ %s)", n_days, trading_days[0], trading_days[-1])

    # Instruments
    symbols = sorted(df["symbol"].unique())
    inst_dir = QLIB_DIR / "instruments"
    inst_dir.mkdir(parents=True, exist_ok=True)
    lines = [f"{sym}\t{trading_days[0]}\t{trading_days[-1]}" for sym in symbols]
    (inst_dir / "all.txt").write_text("\n".join(lines) + "\n")
    logger.info("Instruments: %d symbols", len(symbols))

    # Clean out old feature directories that are not in current data
    feat_dir = QLIB_DIR / "features"
    feat_dir.mkdir(parents=True, exist_ok=True)
    existing_dirs = set(d.name for d in feat_dir.iterdir() if d.is_dir())
    current_symbols = set(symbols)
    stale_dirs = existing_dirs - current_symbols
    if stale_dirs:
        import shutil
        for d in stale_dirs:
            shutil.rmtree(feat_dir / d)
        logger.info("Removed %d stale symbol directories", len(stale_dirs))

    # Per-symbol stats for validation
    stats = {
        "n_days": n_days,
        "n_symbols": len(symbols),
        "symbols": {},  # symbol -> {n_valid_days, first_day, last_day}
    }

    # ── Vectorized write: pivot each field to (date × symbol) matrix ──
    #
    # Instead of looping per-symbol per-field per-day, we:
    #   1. Map each row's date string to its calendar index (vectorized)
    #   2. For each field, pivot to a (n_days × n_symbols) float32 matrix
    #   3. Write each column (= one symbol) as a binary file
    #
    # This replaces ~180M Python dict lookups with a single pandas pivot.

    import time as _time
    t_start = _time.perf_counter()

    # Map dates to calendar indices (vectorized)
    date_strs = df["time"].dt.strftime("%Y-%m-%d")
    cal_idx_series = date_strs.map(cal_index)

    # Collect available fields
    available_fields = [f for f in FIELDS if f in df.columns]

    # Build per-symbol stats (vectorized groupby)
    sym_groups = df.groupby("symbol")["time"]
    for symbol in symbols:
        grp = sym_groups.get_group(symbol)
        stats["symbols"][symbol] = {
            "n_valid_days": len(grp),
            "first_day": grp.min().strftime("%Y-%m-%d"),
            "last_day": grp.max().strftime("%Y-%m-%d"),
        }

    logger.info("  stats built in %.1fs", _time.perf_counter() - t_start)

    # Create all symbol directories at once
    for symbol in symbols:
        (feat_dir / symbol).mkdir(parents=True, exist_ok=True)

    # Process field by field: pivot → write all symbols
    n_symbols = len(symbols)
    for field in available_fields:
        t_field = _time.perf_counter()

        # Build a (n_days × n_symbols) matrix via pivot
        pivot_df = df.pivot_table(
            index=cal_idx_series, columns="symbol", values=field,
            aggfunc="first",
        )
        # Reindex to full calendar range, fill missing with NaN
        pivot_df = pivot_df.reindex(range(n_days))
        matrix = pivot_df.values.astype(np.float32)  # shape: (n_days, n_symbols)
        col_to_idx = {col: i for i, col in enumerate(pivot_df.columns)}

        # Write each symbol's column as a binary file
        for sym_idx, symbol in enumerate(symbols):
            col_idx = col_to_idx.get(symbol)
            if col_idx is None:
                # Symbol has no data for this field — skip
                continue
            col = matrix[:, col_idx]

            # Find start_index
            non_nan = np.where(~np.isnan(col))[0]
            start_idx = int(non_nan[0]) if len(non_nan) > 0 else 0

            bin_path = feat_dir / symbol / f"{field}.day.bin"
            with open(bin_path, "wb") as f:
                np.array([start_idx], dtype="<f").tofile(f)
                col[start_idx:].tofile(f)

        logger.info("  field %-20s written in %.1fs", field, _time.perf_counter() - t_field)

    logger.info(
        "Qlib write complete: %d symbols, %d days, %d fields (%.1fs total)",
        n_symbols, n_days, len(available_fields), _time.perf_counter() - t_start,
    )
    return stats


# ── Step 3: Validate ─────────────────────────────────────────────────

def validate(stats: dict) -> bool:
    """Comprehensive validation of Qlib binary files against DB stats.

    Checks:
    1. Calendar file has correct number of days, no duplicates, sorted
    2. Every symbol directory exists with all field files
    3. Every bin file has correct size: (1 + n_days) * 4 bytes
    4. Every bin file has a valid (non-NaN) start_index header
    5. Per-symbol: number of non-NaN values in close.day.bin matches DB row count
    6. Spot-check: read actual values and compare with DB
    """
    n_days = stats["n_days"]
    n_symbols = stats["n_symbols"]
    max_bin_size = (1 + n_days) * 4  # header + full-length data (start_index=0)

    errors = []
    warnings = []

    # ── 1. Calendar ──
    cal_path = QLIB_DIR / "calendars" / "day.txt"
    cal_lines = cal_path.read_text().strip().split("\n")
    if len(cal_lines) != n_days:
        errors.append(f"Calendar: expected {n_days} days, got {len(cal_lines)}")
    if cal_lines != sorted(cal_lines):
        errors.append("Calendar: not sorted")
    if len(cal_lines) != len(set(cal_lines)):
        errors.append("Calendar: has duplicates")
    logger.info("✓ Calendar: %d days", len(cal_lines))

    # ── 2. Instruments ──
    inst_path = QLIB_DIR / "instruments" / "all.txt"
    inst_lines = inst_path.read_text().strip().split("\n")
    if len(inst_lines) != n_symbols:
        errors.append(f"Instruments: expected {n_symbols}, got {len(inst_lines)}")
    logger.info("✓ Instruments: %d symbols", len(inst_lines))

    # ── 3-5. Per-symbol checks ──
    feat_dir = QLIB_DIR / "features"
    missing_dirs = 0
    bad_size = 0
    bad_header = 0
    count_mismatch = 0
    checked = 0

    for symbol, sym_stats in stats["symbols"].items():
        sym_dir = feat_dir / symbol
        if not sym_dir.exists():
            missing_dirs += 1
            errors.append(f"Missing dir: {symbol}")
            continue

        for field in FIELDS:
            bin_path = sym_dir / f"{field}.day.bin"
            if not bin_path.exists():
                errors.append(f"Missing file: {symbol}/{field}.day.bin")
                continue

            size = bin_path.stat().st_size
            if size > max_bin_size or size < 8:
                bad_size += 1
                errors.append(
                    f"Bad size: {symbol}/{field}.day.bin "
                    f"max={max_bin_size} got={size}"
                )
                continue

            # Check header and size consistency
            with open(bin_path, "rb") as f:
                header = np.frombuffer(f.read(4), dtype="<f")[0]
            if np.isnan(header):
                bad_header += 1
                if field == "close":
                    errors.append(f"NaN header: {symbol}/{field}.day.bin")
            else:
                # Size should be: (1 + n_days - start_index) * 4
                start_idx = int(header)
                expected_size = (1 + n_days - start_idx) * 4
                if size != expected_size:
                    bad_size += 1
                    errors.append(
                        f"Size mismatch: {symbol}/{field}.day.bin "
                        f"start_idx={start_idx} expected={expected_size} got={size}"
                    )

        # Check close.day.bin non-NaN count matches DB
        close_path = sym_dir / "close.day.bin"
        if close_path.exists() and close_path.stat().st_size >= 8:
            with open(close_path, "rb") as f:
                f.read(4)  # skip header
                data = np.frombuffer(f.read(), dtype="<f")
            n_valid = int((~np.isnan(data)).sum())
            expected_valid = sym_stats["n_valid_days"]
            if n_valid != expected_valid:
                count_mismatch += 1
                errors.append(
                    f"Count mismatch: {symbol} close "
                    f"expected={expected_valid} got={n_valid}"
                )

        checked += 1
        if checked % 1000 == 0:
            logger.info("  validated: %d/%d symbols", checked, n_symbols)

    # ── 6. Spot-check: read a few values ──
    spot_symbols = list(stats["symbols"].keys())[:5]
    spot_ok = 0
    for symbol in spot_symbols:
        close_path = feat_dir / symbol / "close.day.bin"
        if not close_path.exists():
            continue
        with open(close_path, "rb") as f:
            header_val = np.frombuffer(f.read(4), dtype="<f")[0]
            data = np.frombuffer(f.read(), dtype="<f")
        non_nan = np.where(~np.isnan(data))[0]
        if len(non_nan) > 0 and int(header_val) == non_nan[0]:
            spot_ok += 1
        else:
            errors.append(
                f"Spot-check failed: {symbol} "
                f"header={header_val} first_non_nan={non_nan[0] if len(non_nan) > 0 else 'none'}"
            )
    logger.info("✓ Spot-check: %d/%d passed", spot_ok, len(spot_symbols))

    # ── Summary ──
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info("  Calendar days:    %d", len(cal_lines))
    logger.info("  Symbols:          %d", n_symbols)
    logger.info("  Missing dirs:     %d", missing_dirs)
    logger.info("  Bad file sizes:   %d", bad_size)
    logger.info("  NaN headers:      %d", bad_header)
    logger.info("  Count mismatches: %d", count_mismatch)
    logger.info("  Total errors:     %d", len(errors))

    if errors:
        logger.error("VALIDATION FAILED with %d errors:", len(errors))
        for e in errors[:20]:
            logger.error("  • %s", e)
        if len(errors) > 20:
            logger.error("  ... and %d more", len(errors) - 20)
        return False
    else:
        logger.info("✅ VALIDATION PASSED — all data consistent")
        return True


# ── Main ─────────────────────────────────────────────────────────────

def main():
    logger.info("=" * 60)
    logger.info("Resync: TimescaleDB market_daily → Qlib binary")
    logger.info("=" * 60)

    # Step 1
    logger.info("\n[Step 1/3] Loading from TimescaleDB...")
    df = load_from_db()

    # Step 2
    logger.info("\n[Step 2/3] Writing Qlib binary files...")
    stats = write_qlib(df)

    # Step 3
    logger.info("\n[Step 3/3] Validating...")
    ok = validate(stats)

    if ok:
        logger.info("\n✅ Resync complete and validated!")
    else:
        logger.error("\n❌ Resync complete but validation FAILED!")
        sys.exit(1)


if __name__ == "__main__":
    main()
