"""CLI command: evaluate a batch of candidate factors from a YAML file."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

import yaml

from mining.config import MiningConfig
from mining.evaluator import FactorMiningEvaluator
from mining.memory import ExperienceMemory

logger = logging.getLogger(__name__)


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
