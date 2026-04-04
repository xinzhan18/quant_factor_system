"""CLI entry point for factor mining — argparse setup + lazy dispatch."""

from __future__ import annotations

import argparse
import logging


def main():
    parser = argparse.ArgumentParser(description="FactorMiner CLI")
    sub = parser.add_subparsers(dest="command")

    # sync
    p_sync = sub.add_parser("sync", help="同步数据到 Qlib 格式")
    p_sync.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    p_sync.add_argument("--start", default="2015-01-01")
    p_sync.add_argument("--end", default=None)

    # evaluate
    p_eval = sub.add_parser("evaluate", help="评估单个因子表达式")
    p_eval.add_argument("expression", help="Qlib 表达式, 如 Rank($close)")
    p_eval.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    p_eval.add_argument("--train-start", default="2015-01-01")
    p_eval.add_argument("--train-end", default="2023-12-31")
    p_eval.add_argument("--test-start", default="2024-01-01")
    p_eval.add_argument("--test-end", default="2024-12-31")

    # batch
    p_batch = sub.add_parser("batch", help="评估一个批次的候选因子")
    p_batch.add_argument("batch_file", help="批次 YAML 文件路径")
    p_batch.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    p_batch.add_argument("--train-start", default="2015-01-01")
    p_batch.add_argument("--train-end", default="2023-12-31")
    p_batch.add_argument("--test-start", default="2024-01-01")
    p_batch.add_argument("--test-end", default="2024-12-31")
    p_batch.add_argument("--screening-size", type=int, default=50)
    p_batch.add_argument("--skip-stage1", action="store_true",
                         help="跳过 Stage 1 快筛（候选已通过 Probe 验证时使用）")


    # library
    p_lib = sub.add_parser("library", help="查看因子库状态")
    p_lib.add_argument("--library-dir", default="storage/registry")

    # probe
    p_probe = sub.add_parser("probe", help="Probe a single expression (lightweight IC only)")
    p_probe.add_argument("expression", help="Qlib expression")
    p_probe.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    p_probe.add_argument("--start", default="2022-01-01")
    p_probe.add_argument("--end", default="2023-12-31")

    # memory
    p_mem = sub.add_parser("memory", help="查看挖掘记忆上下文")
    p_mem.add_argument("--memory-dir", default="storage/mining/memory")

    # logic
    p_logic = sub.add_parser("logic", help="Manage and inspect market logics")
    p_logic.add_argument("logic_action", choices=["list", "coverage", "schedule", "create"],
                         help="Action to perform: list, coverage, schedule, or create (stdin YAML)")
    p_logic.add_argument("--status", default=None,
                         help="Filter by status (active, saturated, dead) — used with 'list'")

    # forbidden
    p_forbidden = sub.add_parser("forbidden", help="Manage forbidden expression patterns")
    p_forbidden.add_argument("forbidden_action", choices=["suggest", "apply", "list"],
                             help="suggest: scan results; apply: write to forbidden.yaml; list: current")

    # retire
    p_retire = sub.add_parser("retire", help="Retire a factor from the library")
    p_retire.add_argument("factor_id", help="Factor ID (e.g., 013)")
    p_retire.add_argument("--library-dir", default="storage/registry")

    # audit
    p_audit = sub.add_parser("audit", help="Audit direction states (read-only report)")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(message)s')

    if args.command == "sync":
        from .commands.sync import cmd_sync
        cmd_sync(args)
    elif args.command == "evaluate":
        from .commands.evaluate import cmd_evaluate
        cmd_evaluate(args)
    elif args.command == "batch":
        from .commands.batch import cmd_batch
        cmd_batch(args)
    elif args.command == "library":
        from .commands.library import cmd_library
        cmd_library(args)
    elif args.command == "memory":
        from .commands.memory import cmd_memory
        cmd_memory(args)
    elif args.command == "probe":
        from .commands.probe import cmd_probe
        cmd_probe(args)
    elif args.command == "logic":
        from .commands.logic import cmd_logic
        cmd_logic(args)
    elif args.command == "forbidden":
        from .commands.forbidden import cmd_forbidden
        cmd_forbidden(args)
    elif args.command == "retire":
        from .commands.retire import cmd_retire
        cmd_retire(args)
    elif args.command == "audit":
        from .commands.audit import cmd_audit
        cmd_audit(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
