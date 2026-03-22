"""CLI entry points for factor mining."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

import yaml

from .config import MiningConfig
from .data_sync import DataSynchronizer
from .evaluator import FactorMiningEvaluator
from .library import FactorLibrary
from .memory import ExperienceMemory

logger = logging.getLogger(__name__)


def cmd_sync(args):
    """Sync TimescaleDB data to Qlib format."""
    from data.storage import TimescaleDB
    db = TimescaleDB()
    syncer = DataSynchronizer(db=db, qlib_dir=args.qlib_dir)
    syncer.sync_daily(start=args.start, end=args.end)
    print(f"Sync complete -> {args.qlib_dir}")


def cmd_evaluate(args):
    """Evaluate a single factor expression."""
    config = MiningConfig(
        qlib_data_dir=args.qlib_dir,
        train_start=args.train_start,
        train_end=args.train_end,
        test_start=args.test_start,
        test_end=args.test_end,
    )
    evaluator = FactorMiningEvaluator(config)
    candidates = [{"name": "cli_factor", "expression": args.expression, "category": "other"}]
    result = evaluator.evaluate_batch(candidates)

    for c in result.admitted:
        print(f"ADMITTED: {c['name']}")
        print(f"  IC: {c.get('full_ic', {}).get('ic_mean', 'N/A')}")
        if "stage3" in c:
            print(f"  Stage 3: {json.dumps(c['stage3'], indent=2, default=str)}")

    for c in result.rejected:
        print(f"REJECTED: {c['name']}")
        if "stage1" in c:
            print(f"  Stage 1 IC: {c['stage1'].get('ic_mean', 'N/A')}")


def cmd_library(args):
    """Show library status."""
    config = MiningConfig(library_dir=args.library_dir)
    lib = FactorLibrary(config)
    factors = lib.list_factors()
    print(f"Library: {len(factors)} factors")
    for f in factors:
        print(f"  [{f['id']}] {f['name']}: IC={f.get('ic_mean', 'N/A')}")


def cmd_memory(args):
    """Show Experience Memory status."""
    config = MiningConfig(memory_dir=args.memory_dir)
    mem = ExperienceMemory(config)
    ctx = mem.compose_search_context()
    print(ctx)


def main():
    parser = argparse.ArgumentParser(description="FactorMiner CLI")
    sub = parser.add_subparsers(dest="command")

    # sync
    p_sync = sub.add_parser("sync", help="Sync data to Qlib format")
    p_sync.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    p_sync.add_argument("--start", default="2015-01-01")
    p_sync.add_argument("--end", default=None)

    # evaluate
    p_eval = sub.add_parser("evaluate", help="Evaluate a factor expression")
    p_eval.add_argument("expression", help="Qlib expression, e.g. Rank($close)")
    p_eval.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    p_eval.add_argument("--train-start", default="2020-01-01")
    p_eval.add_argument("--train-end", default="2024-12-31")
    p_eval.add_argument("--test-start", default="2025-01-01")
    p_eval.add_argument("--test-end", default=None)

    # library
    p_lib = sub.add_parser("library", help="Show library status")
    p_lib.add_argument("--library-dir", default="mining/library")

    # memory
    p_mem = sub.add_parser("memory", help="Show memory context")
    p_mem.add_argument("--memory-dir", default="mining/memory")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO)

    if args.command == "sync":
        cmd_sync(args)
    elif args.command == "evaluate":
        cmd_evaluate(args)
    elif args.command == "library":
        cmd_library(args)
    elif args.command == "memory":
        cmd_memory(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
