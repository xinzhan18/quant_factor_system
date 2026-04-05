#!/usr/bin/env python3
"""Archive old storage/ to storage_archive/."""

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
