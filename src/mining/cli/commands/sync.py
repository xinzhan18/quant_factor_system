"""CLI command: sync TimescaleDB data to Qlib format."""

from __future__ import annotations

import sys

from data.qlib_sync import DataSynchronizer


def cmd_sync(args):
    """Sync TimescaleDB data to Qlib format."""
    try:
        from data.storage import TimescaleDB
    except ImportError:
        print("Error: data.storage module not found. Ensure the project's data layer is installed.")
        sys.exit(1)
    db = TimescaleDB()
    syncer = DataSynchronizer(db=db, qlib_dir=args.qlib_dir)
    syncer.sync_daily(start=args.start, end=args.end)
    print(f"Sync complete -> {args.qlib_dir}")
