#!/usr/bin/env python3
"""Archive the old storage/ directory to storage_archive/.

Run from project root:
    python scripts/archive_old_storage.py
"""

import shutil
import sys
from pathlib import Path


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
