"""Batch evaluation service.

Orchestrates a full batch evaluation run: read YAML, evaluate, persist
results and caches.  Extracted from cli/commands/batch.py so the logic
is reusable without the CLI layer.
"""

from __future__ import annotations

import logging
import pickle
from datetime import datetime
from pathlib import Path
import yaml

from mining.config import MiningConfig
from mining.evaluator import FactorMiningEvaluator, BatchResult
from mining.memory import ExperienceMemory

logger = logging.getLogger(__name__)


def run_batch(
    batch_path: Path,
    config: MiningConfig,
    skip_stage1: bool = False,
) -> BatchResult:
    """Run the full batch evaluation pipeline.

    Parameters
    ----------
    batch_path:
        Path to the batch YAML file (must exist).
    config:
        Fully-configured :class:`MiningConfig` (universe already set).
    skip_stage1:
        If *True*, skip the fast-screening stage.

    Returns
    -------
    BatchResult
        The evaluation result object.
    """
    # 1. Read batch YAML
    with open(batch_path, "r", encoding="utf-8") as f:
        batch = yaml.safe_load(f)

    candidates = batch.get("candidates", [])
    batch_id = batch.get("batch_id", batch_path.stem)
    if not candidates:
        raise ValueError("Batch file contains no candidates")

    logger.info("Batch %s: %d candidates", batch_id, len(candidates))

    # 2. Create evaluator and run evaluate_batch()
    evaluator = FactorMiningEvaluator(config)
    result = evaluator.evaluate_batch(candidates, skip_stage1=skip_stage1)

    # 3. Propagate batch_id to screened/replacement factors
    for f in result.screened:
        f["batch"] = batch_id
    for r in result.replacements:
        if "new_factor" in r:
            r["new_factor"]["batch"] = batch_id

    # 4. Log summary
    logger.info(
        "Screened: %d, Rejected: %d, Replacements: %d",
        len(result.screened),
        len(result.rejected),
        len(result.replacements),
    )
    for f in result.screened:
        s3 = f.get("stage3", {})
        rc = f.get("report_card", {})
        logger.info(
            "  PASS %s: IC=%.4f, OOS=%.4f, ICIR=%.2f, Mono=%.2f",
            f["name"],
            s3.get("ic_mean_is", 0) or 0,
            s3.get("ic_mean_oos", 0) or 0,
            rc.get("ic_ir", 0) or 0,
            rc.get("monotonicity_is", 0) or 0,
        )
    for f in result.rejected:
        s1 = f.get("stage1", {})
        logger.info("  REJECT %s: IC=%s", f["name"], s1.get("ic_mean", "?"))

    # 5. Save values cache (pickle)
    if result.screened:
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
            logger.info(
                "Factor values cache saved: %s (%d factors)",
                cache_path,
                len(values_cache),
            )

    # 6. Save result YAML
    result_path = batch_path.parent / f"{batch_path.stem}_result.yaml"
    output = result.to_dict()
    output["batch_id"] = batch_id
    output["timestamp"] = datetime.now().isoformat()
    with open(result_path, "w", encoding="utf-8") as fp:
        yaml.dump(output, fp, default_flow_style=False, allow_unicode=True)
    logger.info("Result saved: %s", result_path)

    # 7. Save eval history
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
            "hard_gated": len(
                [r for r in result.rejected if "hard_gate_reject" in r]
            ),
            "screened_names": [s["name"] for s in result.screened],
        }
        mem.save_eval_history(batch_id, eval_history)
        logger.info("Eval history saved: %s", batch_id)
    except Exception as e:
        logger.warning("Failed to save eval history: %s", e)

    # 8. Log hard-gated factors
    for f in result.rejected:
        if "hard_gate_reject" in f:
            logger.warning(
                "Hard-gated %s: %s",
                f["name"],
                [r["code"] for r in f["hard_gate_reject"]],
            )

    return result
