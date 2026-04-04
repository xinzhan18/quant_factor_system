"""CLI command: evaluate a single factor expression."""

from __future__ import annotations

import json

from mining.config import MiningConfig, SystemConfig
from mining.evaluator import FactorMiningEvaluator


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
