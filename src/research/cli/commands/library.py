"""CLI command: library — factor library status overview."""

from __future__ import annotations

import argparse
import logging

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml

logger = logging.getLogger(__name__)


def add_parser(subparsers: argparse._SubParsersAction) -> None:
    p = subparsers.add_parser("library", help="Factor library status")
    p.set_defaults(func=cmd_library)


def cmd_library(args: argparse.Namespace) -> None:
    paths = StoragePaths()
    index = load_yaml(paths.factor_index_file)
    factors = index.get("factors", [])

    print(f"Factor Library: {len(factors)} factors")
    if not factors:
        print("  (empty)")
        return

    for f in factors:
        fid = f.get("factor_id", "?")
        name = f.get("name", "?")
        cat = f.get("category", "?")
        print(f"  {fid}: {name} [{cat}]")
