"""One-shot backfill: add flat count keys to every judge.md frontmatter.

Running this script makes the ``recent_batches.base`` file queryable
against historical batches (before ``ensure_judge_bases_fields`` was
wired into Phase 4). Idempotent.

Usage::

    PYTHONPATH=src python3 scripts/backfill_judge_bases_fields.py
"""

from __future__ import annotations

import sys

from research.archive.backfill import ensure_judge_bases_fields
from research.storage.paths import StoragePaths


def main() -> int:
    paths = StoragePaths()
    if not paths.batches_dir.exists():
        print("No batches directory found.", file=sys.stderr)
        return 1

    total = 0
    touched = 0
    for batch_dir in sorted(paths.batches_dir.iterdir()):
        if not batch_dir.is_dir():
            continue
        judge_path = batch_dir / "judge.md"
        if not judge_path.exists():
            continue
        total += 1
        before = judge_path.read_text(encoding="utf-8")
        ensure_judge_bases_fields(judge_path)
        after = judge_path.read_text(encoding="utf-8")
        if before != after:
            touched += 1
            print(f"  ✓ {batch_dir.name}")
        else:
            print(f"  · {batch_dir.name} (already filled)")

    print(f"\nBackfilled {touched}/{total} judge.md files.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
