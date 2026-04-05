"""CLI command: execute — run the evaluation pipeline on a batch of candidates.

Reads a batch YAML file, runs multi-stage evaluation (precheck, dedup,
correlation, hard gates, metrics), and writes the result + judge_packet.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def cmd_execute(args):
    """Execute the evaluation pipeline on a candidate batch."""
    batch_path = Path(args.batch_file)
    if not batch_path.exists():
        print(f"ERROR: batch file not found: {batch_path}")
        sys.exit(1)

    import warnings
    warnings.filterwarnings("ignore")

    import os
    os.environ["JOBLIB_START_METHOD"] = "fork"
    import multiprocessing
    try:
        multiprocessing.set_start_method("fork", force=True)
    except RuntimeError:
        pass

    from mining.application.qlib_runtime import init_qlib, resolve_full_universe
    from mining.config import MiningConfig

    init_qlib(args.qlib_dir)
    all_instruments = resolve_full_universe()

    config = MiningConfig(
        custom_universe=all_instruments,
        train_start=args.train_start,
        train_end=args.train_end,
        test_start=args.test_start,
        test_end=args.test_end,
    )

    from mining.application.batch_service import run_batch
    run_batch(batch_path, config, skip_stage1=args.skip_stage1)
