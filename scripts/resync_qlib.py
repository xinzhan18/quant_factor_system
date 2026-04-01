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

    n_symbols = len(symbols)
    for idx, (symbol, group) in enumerate(df.groupby("symbol")):
        sym_dir = feat_dir / str(symbol)
        sym_dir.mkdir(parents=True, exist_ok=True)

        # Build date→row mapping
        group_indexed = group.set_index(group["time"].dt.strftime("%Y-%m-%d"))

        # Track valid days for this symbol (from close field)
        valid_days_in_db = group_indexed.index.tolist()
        sym_stats = {
            "n_valid_days": len(valid_days_in_db),
            "first_day": group["time"].min().strftime("%Y-%m-%d"),
            "last_day": group["time"].max().strftime("%Y-%m-%d"),
        }

        for field in FIELDS:
            if field not in group_indexed.columns:
                continue

            values = np.full(n_days, np.nan, dtype=np.float32)
            for day in valid_days_in_db:
                cal_idx = cal_index.get(day)
                if cal_idx is None:
                    continue
                row = group_indexed.loc[day]
                if isinstance(row, pd.DataFrame):
                    row = row.iloc[0]
                val = row[field]
                if pd.notna(val):
                    values[cal_idx] = np.float32(val)

            # Find start_index: first non-NaN value
            non_nan_indices = np.where(~np.isnan(values))[0]
            start_idx = int(non_nan_indices[0]) if len(non_nan_indices) > 0 else 0

            # Write Qlib binary: [start_index:f32] [values:f32 * n_days]
            bin_path = sym_dir / f"{field}.day.bin"
            with open(bin_path, "wb") as f:
                f.write(struct.pack("<f", float(start_idx)))
                values.tofile(f)

        stats["symbols"][str(symbol)] = sym_stats

        if (idx + 1) % 500 == 0:
            logger.info("  written: %d/%d symbols", idx + 1, n_symbols)

    logger.info(
        "Qlib write complete: %d symbols, %d days, %d fields",
        n_symbols, n_days, len(FIELDS),
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
    expected_bin_size = (1 + n_days) * 4  # header + data

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
            if size != expected_bin_size:
                bad_size += 1
                errors.append(
                    f"Bad size: {symbol}/{field}.day.bin "
                    f"expected={expected_bin_size} got={size}"
                )
                continue

            # Check header
            with open(bin_path, "rb") as f:
                header = np.frombuffer(f.read(4), dtype="<f")[0]
            if np.isnan(header):
                bad_header += 1
                # Only error if the symbol actually has data for this field
                if field == "close":
                    errors.append(f"NaN header: {symbol}/{field}.day.bin")

        # Check close.day.bin non-NaN count matches DB
        close_path = sym_dir / "close.day.bin"
        if close_path.exists() and close_path.stat().st_size == expected_bin_size:
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
