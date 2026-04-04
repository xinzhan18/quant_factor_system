"""CLI command: probe a single expression with lightweight IC evaluation."""

from __future__ import annotations

import sys

from mining.config import MiningConfig
from mining.evaluator import FactorMiningEvaluator


def cmd_probe(args):
    """Probe a single expression with lightweight IC evaluation."""
    import warnings
    warnings.filterwarnings('ignore')

    from mining.application.qlib_runtime import init_qlib, resolve_full_universe
    init_qlib(args.qlib_dir)
    all_instruments = resolve_full_universe(args.universe)

    config = MiningConfig(universe=args.universe, custom_universe=all_instruments)
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
