#!/usr/bin/env python3
"""Archive the old storage/ tree to storage_archive/.

Performs a simple move:  storage/ -> storage_archive/

Safety checks:
- Aborts if storage/ does not exist.
- Aborts if storage_archive/ already exists (to avoid clobbering).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    src = root / "storage"
    dst = root / "storage_archive"

    if not src.exists():
        print(f"[SKIP] {src} does not exist — nothing to archive.")
        sys.exit(0)

    if dst.exists():
        print(f"[ERROR] {dst} already exists — refusing to overwrite.")
        sys.exit(1)

    shutil.move(str(src), str(dst))
    print(f"[OK] Moved {src} -> {dst}")


if __name__ == "__main__":
    main()
