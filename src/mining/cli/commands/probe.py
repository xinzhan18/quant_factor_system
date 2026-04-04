"""CLI command: probe a single expression with lightweight IC evaluation."""

from __future__ import annotations

import sys

from mining.config import MiningConfig
from mining.evaluator import FactorMiningEvaluator


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
