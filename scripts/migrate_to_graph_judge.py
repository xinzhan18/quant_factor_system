"""One-shot cleanup: wipe old Phase 3 judge artifacts ahead of graph-judge schema.

Runs exactly once. For every ``storage/vault/batches/batch_*/``:
- delete ``_packets/`` (old packet scratch)
- delete ``judge.md`` (monolithic old-schema file)

Leaves ``manifest.yaml`` / ``result.yaml`` / ``python_candidates/`` /
``signals/`` untouched. Admissions in ``vault/factors/`` and evidence trails in
``vault/directions/*.md`` are preserved (stale ``[[batches/.../judge]]`` links
will go dead but that's accepted per the refactor plan).

Usage::

    python3 scripts/migrate_to_graph_judge.py [--dry-run]
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BATCHES_DIR = REPO_ROOT / "storage" / "vault" / "batches"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be deleted without touching files",
    )
    args = parser.parse_args()

    if not BATCHES_DIR.exists():
        print(f"batches dir not found at {BATCHES_DIR} — nothing to migrate")
        return 0

    batches = sorted(p for p in BATCHES_DIR.iterdir() if p.is_dir() and p.name.startswith("batch_"))
    if not batches:
        print(f"no batches under {BATCHES_DIR}")
        return 0

    to_delete: list[Path] = []
    for bdir in batches:
        packets = bdir / "_packets"
        judge = bdir / "judge.md"
        if packets.exists():
            to_delete.append(packets)
        if judge.exists():
            to_delete.append(judge)

    if not to_delete:
        print(f"Scanned {len(batches)} batches; nothing to delete")
        return 0

    print(f"Scanned {len(batches)} batches; {len(to_delete)} targets:")
    for p in to_delete:
        kind = "dir" if p.is_dir() else "file"
        print(f"  [{kind}] {p.relative_to(REPO_ROOT)}")

    if args.dry_run:
        print("\n(dry run — nothing removed)")
        return 0

    for p in to_delete:
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()

    print(f"\nRemoved {len(to_delete)} items.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
