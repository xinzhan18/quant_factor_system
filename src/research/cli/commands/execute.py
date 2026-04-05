"""CLI command: execute — run research pipeline on a frozen batch."""

from __future__ import annotations

import argparse
import logging

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("execute", help="Run research execute pipeline on batch")
    p.add_argument("batch_file", help="Path to batch_XXX.yaml")
    p.add_argument("--universe", default="csi1000")
    p.add_argument("--profile", default="storage/evaluation_profiles/research_eval_v1.yaml")
    p.set_defaults(func=cmd_execute)


def cmd_execute(args: argparse.Namespace) -> None:
    from research.execute.batch_runner import BatchRunner

    print(f"Executing batch: {args.batch_file}")
    print(f"Universe: {args.universe}")

    runner = BatchRunner(
        profile_path=args.profile,
        results_dir="storage/results",
        packets_dir="storage/packets",
    )
    result = runner.run(args.batch_file)

    summary = result.get("summary", {})
    print(f"\nTotal candidates: {summary.get('total_candidates', 0)}")
    print(f"Gate pass:        {summary.get('gate_pass', 0)}")
    print(f"Gate warn:        {summary.get('gate_warn', 0)}")
    print(f"Gate fail:        {summary.get('gate_fail_technical', 0)}")
    print(f"Precheck failed:  {summary.get('precheck_failed', 0)}")
