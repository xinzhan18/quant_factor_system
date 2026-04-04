"""CLI command: evaluate a batch of candidate factors from a YAML file."""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from mining.config import MiningConfig

logger = logging.getLogger(__name__)


def cmd_batch(args):
    """Evaluate a batch of candidate factors from a YAML file."""
    # 1. Parse args, check batch_file exists
    batch_path = Path(args.batch_file)
    if not batch_path.exists():
        print(f"错误：批次文件不存在: {batch_path}")
        sys.exit(1)

    # 2. Set up warnings/multiprocessing
    import warnings
    warnings.filterwarnings('ignore')
    import os
    os.environ['JOBLIB_START_METHOD'] = 'fork'
    import multiprocessing
    try:
        multiprocessing.set_start_method('fork', force=True)
    except RuntimeError:
        pass

    # 3. Call init_qlib() and resolve_full_universe()
    from mining.application.qlib_runtime import init_qlib, resolve_full_universe
    init_qlib(args.qlib_dir)
    all_instruments = resolve_full_universe(args.universe)

    # 4. Build MiningConfig
    config = MiningConfig(
        universe=args.universe,
        custom_universe=all_instruments,
        train_start=args.train_start,
        train_end=args.train_end,
        test_start=args.test_start,
        test_end=args.test_end,
        fast_screening_universe_size=args.screening_size,
    )

    # 5. Call run_batch()
    from mining.application.batch_service import run_batch
    run_batch(batch_path, config, skip_stage1=args.skip_stage1)
