"""CLI command: execute — run research pipeline on a frozen batch."""

from __future__ import annotations

import argparse
import logging

logger = logging.getLogger(__name__)


def cmd_execute(args: argparse.Namespace) -> None:
    from research.execute.batch_runner import BatchRunner

    from research.execute.config import load_research_config
    config = load_research_config()
    qlib_dir = getattr(args, "qlib_dir", None) or config.get("qlib_data_dir", "~/.qlib/qlib_data/cn_data_1d")
    runner = BatchRunner(
        profile_path=args.profile,
        batches_dir="storage/batches",
        universe_override=args.universe,  # None means read from profile
        qlib_dir=qlib_dir,
    )

    universe_src = f"override={args.universe}" if args.universe else f"profile={runner._profile.get('universe', 'csi1000')}"
    print(f"Executing batch: {args.batch_file}")
    print(f"Universe: {universe_src}")

    result = runner.run(args.batch_file)

    summary = result.get("summary", {})
    print(f"\nTotal candidates: {summary.get('total_candidates', 0)}")
    print(f"Gate pass:        {summary.get('gate_pass', 0)}")
    print(f"Gate warn:        {summary.get('gate_warn', 0)}")
    print(f"Gate fail:        {summary.get('gate_fail_technical', 0)}")
    print(f"Precheck failed:  {summary.get('precheck_failed', 0)}")
