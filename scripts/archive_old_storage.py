#!/usr/bin/env python3
<<<<<<< HEAD
"""Archive the existing ``storage/`` directory to ``storage_archive/``.

This is a one-shot migration helper.  It refuses to run if
``storage_archive/`` already exists so that nothing is silently overwritten.

Usage::

    python scripts/archive_old_storage.py          # default paths
    python scripts/archive_old_storage.py --src storage --dst storage_archive
"""

from __future__ import annotations

import argparse
=======
"""Archive the old storage/ directory to storage_archive/.

Run from project root:
    python scripts/archive_old_storage.py
"""

>>>>>>> worktree-agent-a1d4eeec
import shutil
import sys
from pathlib import Path


<<<<<<< HEAD
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
=======
def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "storage"
    dst = root / "storage_archive"

    if not src.exists():
        print(f"ERROR: {src} does not exist — nothing to archive.")
        sys.exit(1)

    if dst.exists():
        print(f"ERROR: {dst} already exists — refusing to overwrite.")
        sys.exit(1)

    shutil.move(str(src), str(dst))
    print(f"Archived {src} -> {dst}")


if __name__ == "__main__":
    main()
>>>>>>> worktree-agent-a1d4eeec
