#!/usr/bin/env python3
"""Copy storage to new layout (non-destructive).

Old directories are NOT deleted -- they remain as backup until
manual cleanup after verification.

Usage:
    python3 scripts/migrate_storage.py --dry-run
    python3 scripts/migrate_storage.py --apply
"""
import argparse
import shutil
from pathlib import Path

COPIES = [
    ("storage/library", "storage/registry"),
    ("storage/candidates", "storage/mining/candidates"),
    ("storage/memory", "storage/mining/memory"),
    ("storage/logic", "storage/mining/logic"),
    ("storage/python_factors", "storage/mining/python_factors"),
    ("storage/vault", "storage/evidence/vault"),
    ("storage/reports", "storage/evidence/reports"),
    ("storage/cache", "storage/runtime/cache"),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    dry_run = not args.apply

    if dry_run:
        print("=== DRY RUN ===\n")

    for old, new in COPIES:
        old_p, new_p = Path(old), Path(new)
        if not old_p.exists():
            print(f"  SKIP {old} (not found)")
            continue
        if new_p.exists():
            print(f"  SKIP {old} -> {new} (destination exists)")
            continue
        if dry_run:
            print(f"  WOULD COPY {old} -> {new}")
        else:
            new_p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(str(old_p), str(new_p))
            print(f"  COPIED {old} -> {new}")

    if not dry_run:
        Path("storage/runtime").mkdir(parents=True, exist_ok=True)
        Path("storage/runtime/.gitkeep").touch()
        print("\nDone. Old directories preserved as backup.")
        print("After verification, manually delete old dirs.")


if __name__ == "__main__":
    main()
