"""CLI entry point for research — argparse setup + lazy dispatch."""

from __future__ import annotations

import argparse
import logging


def main():
    parser = argparse.ArgumentParser(
        prog="research",
        description="Research CLI — next-generation factor mining system",
    )
    sub = parser.add_subparsers(dest="command")

    # probe
    p_probe = sub.add_parser("probe", help="Lightweight IC check (train only)")
    p_probe.add_argument("expression", help="Qlib expression")
    p_probe.add_argument("--universe", default="all",
                         help="Universe: all | csi1000 (default: all)")
    p_probe.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    p_probe.add_argument("--start", default="2019-01-01",
                         help="Probe start date (train period only, default: 2019-01-01)")
    p_probe.add_argument("--end", default="2023-12-31",
                         help="Probe end date (train period only, default: 2023-12-31)")

    # execute
    p_exec = sub.add_parser("execute", help="Run execute pipeline on a batch")
    p_exec.add_argument("batch_file", help="Batch YAML file path")
    p_exec.add_argument("--universe", default="all",
                        help="Universe: all | csi1000 (default: all)")
    p_exec.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    p_exec.add_argument("--train-start", default="2015-01-01")
    p_exec.add_argument("--train-end", default="2023-12-31")
    p_exec.add_argument("--test-start", default="2024-01-01")
    p_exec.add_argument("--test-end", default="2024-12-31")
    p_exec.add_argument("--skip-stage1", action="store_true",
                        help="Skip Stage 1 fast screen (candidates already probed)")

    # logic
    p_logic = sub.add_parser("logic", help="Logic management: list, schedule, propose, review")
    p_logic.add_argument("logic_action",
                         choices=["list", "schedule", "propose", "review"],
                         help="Action to perform")
    p_logic.add_argument("--status", default=None,
                         help="Filter by status (active, warm, saturated, dead)")
    p_logic.add_argument("--logic-id", default=None,
                         help="Specific logic ID for review")

    # batch
    p_batch = sub.add_parser("batch", help="Batch lifecycle: list, next-id, status")
    p_batch.add_argument("batch_action",
                         choices=["list", "next-id", "status"],
                         help="Action to perform")
    p_batch.add_argument("--batch-id", default=None,
                         help="Specific batch ID for status")

    # library
    p_lib = sub.add_parser("library", help="Factor library status overview")
    p_lib.add_argument("--verbose", "-v", action="store_true",
                       help="Show detailed per-factor info")

    # state
    _p_state = sub.add_parser("state", help="Research state overview")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(name)s - %(message)s")

    if args.command == "probe":
        from research.cli.commands.probe import cmd_probe
        cmd_probe(args)
    elif args.command == "execute":
        from research.cli.commands.execute import cmd_execute
        cmd_execute(args)
    elif args.command == "logic":
        from research.cli.commands.logic import cmd_logic
        cmd_logic(args)
    elif args.command == "batch":
        from research.cli.commands.batch import cmd_batch
        cmd_batch(args)
    elif args.command == "library":
        from research.cli.commands.library import cmd_library
        cmd_library(args)
    elif args.command == "state":
        from research.cli.commands.state import cmd_state
        cmd_state(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
