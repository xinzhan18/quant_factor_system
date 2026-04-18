"""Thin CLI wrapper -- delegates to ``report.render.render_factor``.

All heavy lifting (analyzers, charts) moved to ``report/render.py`` and
``report/charts/``. This file exists only so ``python -m report.builder
--factor-id F001 --vault`` keeps working for manual invocation.
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from report.render import render_factor

logger = logging.getLogger(__name__)


def main() -> int:
    parser = argparse.ArgumentParser(description="Render a factor report")
    parser.add_argument("--factor-id", required=True, help="e.g. F001")
    parser.add_argument(
        "--storage-root", default="storage",
        help="Path to storage root (default: storage)",
    )
    parser.add_argument(
        "--vault", action="store_true",
        help="Kept for compatibility; vault mode is always on now.",
    )
    args = parser.parse_args()
    manifest = render_factor(args.factor_id, storage_root=Path(args.storage_root))
    print(f"Rendered {args.factor_id}: {len(manifest['charts'])} charts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
