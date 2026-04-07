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
    p_probe.add_argument("--universe", default=None,
                         help="Override universe (default: from config)")
    p_probe.add_argument("--qlib-dir", default=None)
    p_probe.add_argument("--start", default=None,
                         help="Override probe start date (default: from config)")
    p_probe.add_argument("--end", default=None,
                         help="Override probe end date (default: from config)")

    # execute
    p_exec = sub.add_parser("execute", help="Run execute pipeline on a batch")
    p_exec.add_argument("batch_file", help="Batch YAML file path")
    p_exec.add_argument("--universe", default=None,
                        help="Override universe (default: from config)")
    p_exec.add_argument("--qlib-dir", default=None)
    p_exec.add_argument("--profile", default=None,
                        help="Override evaluation profile YAML")
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
    p_state = sub.add_parser("state", help="Research state overview + mutations")
    state_sub = p_state.add_subparsers(dest="state_action")
    p_state_set = state_sub.add_parser("set", help="Set a state key")
    p_state_set.add_argument("key", help="Key to set (e.g. current_batch)")
    p_state_set.add_argument("value", help="Value (e.g. batch_042, null, 3)")
    state_sub.add_parser("clear-batch", help="Clear batch fields after cycle")
    state_sub.add_parser("sync-holdout", help="Sync ledger holdout_reviews → queue + state count")
    p_finalize = state_sub.add_parser("finalize-batch", help="Apply judge report back into logic/state")
    p_finalize.add_argument("batch_id", help="Batch ID to finalize")
    p_validate = state_sub.add_parser("validate-consistency", help="Validate storage truth sources")
    p_validate.add_argument("--batch-id", default=None, help="Optional batch ID for judge/state validation")

    # capabilities
    _p_caps = sub.add_parser("capabilities", help="Available operators, fields, constraints")

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
    elif args.command == "capabilities":
        from research.cli.commands.capabilities import cmd_capabilities
        cmd_capabilities(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
