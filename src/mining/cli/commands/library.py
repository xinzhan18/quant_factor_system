"""CLI command: show library status."""

from __future__ import annotations

from mining.config import MiningConfig
from mining.registry import FactorLibrary


def cmd_library(args):
    """Show library status."""
    config = MiningConfig(library_dir=args.library_dir)
    lib = FactorLibrary(config)
    factors = lib.list_factors()
    print(f"Library: {len(factors)} factors")
    for f in factors:
        print(f"  [{f['id']}] {f['name']}: IC={f.get('ic_mean', 'N/A')}")
