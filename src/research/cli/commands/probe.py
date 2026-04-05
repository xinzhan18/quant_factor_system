"""CLI command: probe — lightweight IC check on train period only.

Probes a single Qlib expression against the full universe (or a subset)
using only train-period data. Outputs IC, ICIR, win rate, and day count.
This is the cheapest possible signal quality check.
"""

from __future__ import annotations

import sys


def cmd_probe(args):
    """Run a lightweight IC-only probe on a single expression."""
    import warnings
    warnings.filterwarnings("ignore")

    from mining.application.qlib_runtime import init_qlib, resolve_full_universe
    from mining.config import MiningConfig
    from mining.evaluator import FactorMiningEvaluator

    init_qlib(args.qlib_dir)
    all_instruments = resolve_full_universe()

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

    ic = result.get("ic_mean", 0)
    ic_ir = result.get("ic_ir", 0)
    win_rate = result.get("ic_win_rate", 0)
    n_days = result.get("n_days", 0)

    # Classify signal strength
    abs_ic = abs(ic)
    if abs_ic >= 0.03:
        tag = "STRONG"
    elif abs_ic >= 0.01:
        tag = "MODERATE"
    else:
        tag = "WEAK"

    print(f"IC={ic:.4f}  ICIR={ic_ir:.3f}  "
          f"WinRate={win_rate:.1%}  Days={n_days}  [{tag}]")
