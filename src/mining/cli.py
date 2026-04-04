"""CLI entry points for factor mining."""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

import yaml

from .config import MiningConfig, SystemConfig
from data.qlib_sync import DataSynchronizer
from .evaluator import FactorMiningEvaluator
from .library import FactorLibrary
from .memory import ExperienceMemory

logger = logging.getLogger(__name__)


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


def cmd_evaluate(args):
    """Evaluate a single factor expression."""
    system = SystemConfig(qlib_data_dir=args.qlib_dir)
    config = MiningConfig(
        system=system,
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



def cmd_batch(args):
    """Evaluate a batch of candidate factors from a YAML file."""
    import warnings
    warnings.filterwarnings('ignore')
    import os
    os.environ['JOBLIB_START_METHOD'] = 'fork'
    import multiprocessing
    try:
        multiprocessing.set_start_method('fork', force=True)
    except RuntimeError:
        pass

    from datetime import datetime

    batch_path = Path(args.batch_file)
    if not batch_path.exists():
        print(f"错误：批次文件不存在: {batch_path}")
        sys.exit(1)

    with open(batch_path, 'r', encoding='utf-8') as f:
        batch = yaml.safe_load(f)

    candidates = batch.get('candidates', [])
    batch_id = batch.get('batch_id', batch_path.stem)
    if not candidates:
        print("错误：批次文件中没有候选因子")
        sys.exit(1)

    logger.info("批次 %s: %d 个候选因子", batch_id, len(candidates))

    # 初始化 Qlib
    import qlib
    from qlib.config import REG_CN, C
    qlib.init(provider_uri=args.qlib_dir, region=REG_CN)
    C.kernels = 1
    from qlib.data import D

    # 解析股票池
    inst_dict = D.instruments('all')
    df_temp = D.features(
        instruments=inst_dict, fields=['$close'],
        start_time='2024-06-01', end_time='2024-06-30',
    )
    all_instruments = df_temp.index.get_level_values('instrument').unique().tolist()

    config = MiningConfig(
        custom_universe=all_instruments,
        train_start=args.train_start,
        train_end=args.train_end,
        test_start=args.test_start,
        test_end=args.test_end,
        fast_screening_universe_size=args.screening_size,
    )
    evaluator = FactorMiningEvaluator(config)
    result = evaluator.evaluate_batch(candidates, skip_stage1=args.skip_stage1)

    # Propagate batch_id to screened/replacement factors for library admission
    for f in result.screened:
        f["batch"] = batch_id
    for r in result.replacements:
        if "new_factor" in r:
            r["new_factor"]["batch"] = batch_id

    # 打印结果
    logger.info("筛选通过: %d, 淘汰: %d, 替换候选: %d",
                len(result.screened), len(result.rejected), len(result.replacements))
    for f in result.screened:
        s3 = f.get('stage3', {})
        rc = f.get('report_card', {})
        logger.info("  通过 %s: IC=%.4f, OOS=%.4f, ICIR=%.2f, 单调性=%.2f",
                     f['name'],
                     s3.get('ic_mean_is', 0) or 0,
                     s3.get('ic_mean_oos', 0) or 0,
                     rc.get('ic_ir', 0) or 0,
                     rc.get('monotonicity_is', 0) or 0)
    for f in result.rejected:
        s1 = f.get('stage1', {})
        logger.info("  淘汰 %s: IC=%s", f['name'], s1.get('ic_mean', '?'))

    # 保存 screened 因子的值为 pickle 缓存（供 judge admit 时加载写入 DB）
    if result.screened:
        import pickle
        values_cache = {}
        for f in result.screened:
            if "_factor_values" in f and "_factor_values_oos" in f:
                values_cache[f["name"]] = {
                    "is": f["_factor_values"],
                    "oos": f["_factor_values_oos"],
                }
        if values_cache:
            cache_path = batch_path.parent / f"{batch_path.stem}_values.pkl"
            with open(cache_path, "wb") as fp:
                pickle.dump(values_cache, fp)
            logger.info("因子值缓存已保存: %s (%d 个因子)", cache_path, len(values_cache))

    # 保存结果（白名单序列化）
    result_path = batch_path.parent / f"{batch_path.stem}_result.yaml"
    output = result.to_dict()
    output['batch_id'] = batch_id
    output['timestamp'] = datetime.now().isoformat()
    with open(result_path, 'w', encoding='utf-8') as fp:
        yaml.dump(output, fp, default_flow_style=False, allow_unicode=True)
    logger.info("结果已保存: %s", result_path)

    # Save eval history (programmatic, always runs)
    try:
        mem = ExperienceMemory(config)
        eval_history = {
            "batch_id": batch_id,
            "timestamp": datetime.now().isoformat(),
            "phase": "evaluate",
            "candidates": len(candidates),
            "screened": len(result.screened),
            "rejected": len(result.rejected),
            "replacements": len(result.replacements),
            "hard_gated": len([r for r in result.rejected if "hard_gate_reject" in r]),
            "screened_names": [s["name"] for s in result.screened],
        }
        mem.save_eval_history(batch_id, eval_history)
        logger.info("Eval history saved: %s", batch_id)
    except Exception as e:
        logger.warning("Failed to save eval history: %s", e)

    # Log hard-gated factors
    for f in result.rejected:
        if "hard_gate_reject" in f:
            logger.warning("Hard-gated %s: %s", f['name'],
                           [r["code"] for r in f['hard_gate_reject']])



def cmd_probe(args):
    """Probe a single expression with lightweight IC evaluation."""
    import warnings
    warnings.filterwarnings('ignore')

    import qlib
    from qlib.config import REG_CN, C
    qlib.init(provider_uri=args.qlib_dir, region=REG_CN)
    C.kernels = 1
    from qlib.data import D

    # Get full universe
    inst_dict = D.instruments('all')
    df_temp = D.features(
        instruments=inst_dict, fields=['$close'],
        start_time='2024-06-01', end_time='2024-06-30',
    )
    all_instruments = df_temp.index.get_level_values('instrument').unique().tolist()

    config = MiningConfig(custom_universe=all_instruments)
    evaluator = FactorMiningEvaluator(config)
    result = evaluator.probe_single(
        expression=args.expression,
        start=args.start,
        end=args.end,
    )

    if "error" in result:
        print(f"ERROR: {result['error']}")
        sys.exit(1)
    else:
        ic = result.get("ic_mean", 0)
        print(f"IC={ic:.4f}  ICIR={result.get('ic_ir', 0):.3f}  "
              f"WinRate={result.get('ic_win_rate', 0):.1%}  "
              f"Days={result.get('n_days', 0)}")


def cmd_memory(args):
    """Show Experience Memory status."""
    config = MiningConfig(memory_dir=args.memory_dir)
    mem = ExperienceMemory(config)
    ctx = mem.compose_search_context()
    print(ctx)


def cmd_logic(args):
    """Manage and inspect market logics."""
    from mining.logic_library import MarketLogicLibrary
    from mining.scheduler import Scheduler

    config = MiningConfig()
    lib = MarketLogicLibrary(config.logic_dir)

    if args.logic_action == "list":
        status_filter = getattr(args, "status", None)
        logics = lib.list_logics(status=status_filter)
        if not logics:
            print("No logics found.")
            return
        for l in logics:
            s = l.get("stats", {})
            print(f"  {l['id']} [{l['status']}] {l['name']} "
                  f"(cat={l['category']}, gen={s.get('factors_generated', 0)}, "
                  f"adm={s.get('factors_admitted', 0)})")

    elif args.logic_action == "coverage":
        coverage = lib.coverage_map()
        if not coverage:
            print("No taxonomy loaded.")
            return
        for cat, count in sorted(coverage.items()):
            bar = "#" * count
            print(f"  {cat:20s} {count:3d} {bar}")

    elif args.logic_action == "schedule":
        sched = Scheduler()
        logics = lib.list_logics(status="active")
        if not logics:
            print("No active logics.")
            return
        coverage = lib.coverage_map()
        # Compute avg IC from library
        flib = FactorLibrary(config)
        factors = flib.list_factors()
        avg_ic = sum(abs(f.get("ic_mean", 0)) for f in factors) / max(len(factors), 1)
        scores = sched.score_logics(logics, coverage, avg_ic)
        print("Logic priority scores:")
        for lid, score in scores:
            logic = lib.get(lid)
            name = logic["name"] if logic else "?"
            print(f"  {lid} {name:30s} score={score:+.1f}")
        if sched.should_trigger_outer_loop(logics, coverage, avg_ic):
            print("\n  All scores non-positive — recommend running /logic new (outer loop)")

    elif args.logic_action == "create":
        logic_yaml = yaml.safe_load(sys.stdin)
        if not isinstance(logic_yaml, dict):
            print("ERROR: expected YAML dict from stdin, got:", type(logic_yaml))
            sys.exit(1)
        required = ["name", "category", "hypothesis"]
        missing = [k for k in required if k not in logic_yaml]
        if missing:
            print(f"ERROR: missing required fields: {missing}")
            print(f"Required: {required}")
            sys.exit(1)
        record = lib.create(**logic_yaml)
        print(f"Created logic: {record['id']}")


def cmd_forbidden(args):
    """Manage forbidden expression patterns."""
    config = MiningConfig()
    mem = ExperienceMemory(config)

    if args.forbidden_action == "list":
        regions = mem.read_forbidden()
        if not regions:
            print("No forbidden regions.")
            return
        for r in regions:
            print(f"  {r.get('pattern', '?')} — {r.get('reason', '?')}")

    elif args.forbidden_action in ("suggest", "apply"):
        suggestions = _forbidden_suggest(config)
        if not suggestions:
            print("No forbidden patterns suggested.")
            return
        for s in suggestions:
            print(f"  {s['skeleton']}  (blocker={s['blocker']}, "
                  f"batches={s['batch_count']}, category={s['category']})")
        if args.forbidden_action == "apply":
            for s in suggestions:
                mem.add_forbidden(s["skeleton"], f"auto: blocker={s['blocker']}, "
                                  f"{s['batch_count']} batches")
            print(f"\n{len(suggestions)} patterns written to forbidden.yaml.")


def _forbidden_suggest(config: MiningConfig):
    """Scan result files for Stage 2 corr rejects, find repeated patterns."""
    from collections import defaultdict
    candidates_dir = Path(config.candidates_dir)
    # key = (skeleton, blocker) → set of batch_ids
    pattern_batches: dict = defaultdict(lambda: {"batches": set(), "category": None})

    for result_file in sorted(candidates_dir.glob("*_result.yaml")):
        try:
            with open(result_file, 'r') as f:
                data = yaml.unsafe_load(f) or {}
        except Exception:
            continue
        batch_id = data.get("batch_id", result_file.stem)
        for r in data.get("rejected", []):
            # Check for Stage 2 corr reject (new structured or old format)
            meta = r.get("reject_meta", {})
            if meta.get("code") == "stage2_corr":
                blocker = meta.get("blocker", "?")
                corr = meta.get("corr", 0)
            elif r.get("stage2", {}).get("passed") is False:
                blocker = r.get("stage2", {}).get("max_corr_factor", "?")
                corr = r.get("stage2", {}).get("max_corr", 0)
            else:
                continue
            expr = r.get("expression", "")
            if not expr:
                continue
            skeleton = re.sub(r'\d+\.?\d*', '*', expr)
            category = r.get("category", "?")
            key = (skeleton, blocker)
            pattern_batches[key]["batches"].add(batch_id)
            pattern_batches[key]["category"] = category

    suggestions = []
    for (skeleton, blocker), info in pattern_batches.items():
        if len(info["batches"]) >= 3:
            suggestions.append({
                "skeleton": skeleton,
                "blocker": blocker,
                "batch_count": len(info["batches"]),
                "category": info["category"],
            })
    return sorted(suggestions, key=lambda s: -s["batch_count"])


def cmd_audit(args):
    """Audit direction states (read-only report)."""
    config = MiningConfig()
    mem = ExperienceMemory(config)
    mismatches = mem.audit_directions(config.candidates_dir)
    if not mismatches:
        print("All direction states consistent.")
        return
    print(f"Found {len(mismatches)} mismatches:")
    for m in mismatches:
        print(f"  [{m['flag']}] {m['direction']}: "
              f"recorded={m['recorded_attempts']}, observed={m['observed_attempts']}, "
              f"status={m['status']}")


def cmd_retire(args):
    """Retire a factor from the library."""
    config = MiningConfig(library_dir=args.library_dir)
    lib = FactorLibrary(config)
    lib.retire(args.factor_id)
    print(f"Factor {args.factor_id} retired")


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
    p_lib.add_argument("--library-dir", default="storage/library")

    # probe
    p_probe = sub.add_parser("probe", help="Probe a single expression (lightweight IC only)")
    p_probe.add_argument("expression", help="Qlib expression")
    p_probe.add_argument("--qlib-dir", default="~/.qlib/qlib_data/cn_data_1d")
    p_probe.add_argument("--start", default="2022-01-01")
    p_probe.add_argument("--end", default="2023-12-31")

    # memory
    p_mem = sub.add_parser("memory", help="查看挖掘记忆上下文")
    p_mem.add_argument("--memory-dir", default="storage/memory")

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
    p_retire.add_argument("--library-dir", default="storage/library")

    # audit
    p_audit = sub.add_parser("audit", help="Audit direction states (read-only report)")

    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format='%(name)s - %(message)s')

    if args.command == "sync":
        cmd_sync(args)
    elif args.command == "evaluate":
        cmd_evaluate(args)
    elif args.command == "batch":
        cmd_batch(args)
    elif args.command == "library":
        cmd_library(args)
    elif args.command == "memory":
        cmd_memory(args)
    elif args.command == "probe":
        cmd_probe(args)
    elif args.command == "logic":
        cmd_logic(args)
    elif args.command == "forbidden":
        cmd_forbidden(args)
    elif args.command == "retire":
        cmd_retire(args)
    elif args.command == "audit":
        cmd_audit(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
