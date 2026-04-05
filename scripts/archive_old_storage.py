#!/usr/bin/env python3
"""Archive the existing ``storage/`` directory to ``storage_archive/``.

This is a one-shot migration helper.  It refuses to run if
``storage_archive/`` already exists so that nothing is silently overwritten.

Usage::

    python scripts/archive_old_storage.py          # default paths
    python scripts/archive_old_storage.py --src storage --dst storage_archive
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


def main(src: str = "storage", dst: str = "storage_archive") -> None:
    src_path = Path(src)
    dst_path = Path(dst)

    if not src_path.exists():
        print(f"Source directory does not exist: {src_path}")
        sys.exit(1)

    if dst_path.exists():
        print(f"Destination already exists: {dst_path}  (aborting to avoid data loss)")
        sys.exit(1)

    shutil.move(str(src_path), str(dst_path))
    print(f"Archived {src_path} -> {dst_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Archive old storage directory")
    parser.add_argument("--src", default="storage", help="Source directory (default: storage)")
    parser.add_argument("--dst", default="storage_archive", help="Destination (default: storage_archive)")
    args = parser.parse_args()
    main(src=args.src, dst=args.dst)
