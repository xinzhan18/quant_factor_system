"""CLI command: retire a factor from the library."""

from __future__ import annotations

from mining.config import MiningConfig
from mining.registry import FactorLibrary


def cmd_retire(args):
    """Retire a factor from the library."""
    config = MiningConfig(library_dir=args.library_dir)
    lib = FactorLibrary(config)
    lib.retire(args.factor_id)
    print(f"Factor {args.factor_id} retired")
