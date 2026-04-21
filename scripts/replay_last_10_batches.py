"""One-shot drift correction for the last N batches.

Runs after the Bug 1-7 fixes land. It uses the newly-added Python sync
primitives to bring the vault back into a consistent state without
touching historical batch artefacts:

1. For each of the last ``N`` batches, parse its ``judge.md`` and apply
   :func:`sync_status_from_judge` to the direction file. This fixes the
   three known drifts (``asymmetric_momentum`` / ``return_momentum_acceleration``
   left at status ``exploring`` despite dead judges; ``overnight_intraday_split``
   left at ``productive`` despite the ``→ saturated`` batch_027 judge).

2. Call :func:`refresh_index` — picks up the new statuses in the auto-section
   + regenerates the narrative sentinel blocks (最近 Batch, 活跃方向) via
   :func:`refresh_narrative`. Also bumps ``round`` / ``last_batch`` in the
   frontmatter to match ``state.yaml``.

3. Report any orphan factor-report artefacts on disk — they need to be
   committed via ``research commit-report F{id}`` separately (run in the
   caller shell, not this script, because the commit touches git).

Usage::

    PYTHONPATH=src python3 scripts/replay_last_10_batches.py --dry-run
    PYTHONPATH=src python3 scripts/replay_last_10_batches.py --apply
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from research.memory.direction_updater import sync_status_from_judge
from research.memory.index_refresher import refresh_index
from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml


def _find_recent_batches(batches_dir: Path, n: int) -> list[Path]:
    batches = sorted(
        (
            d
            for d in batches_dir.iterdir()
            if d.is_dir() and re.match(r"^batch_\d+$", d.name)
        ),
        key=lambda p: int(re.search(r"(\d+)$", p.name).group(1)),
        reverse=True,
    )
    return batches[:n]


def _direction_from_manifest(manifest_path: Path) -> str | None:
    if not manifest_path.exists():
        return None
    data = load_yaml(manifest_path) or {}
    return data.get("direction")


def _find_orphan_reports(paths: StoragePaths) -> list[str]:
    """Return F{id}s whose factor.md / assets are on disk but may be uncommitted.

    We report anything that has BOTH a factor.yaml AND a factor.md but
    whose md frontmatter contains ``composite_grade`` (= the report
    subagent has run). Git-tracked vs not is a separate check the caller
    runs — this script just surfaces candidates.
    """
    out: list[str] = []
    for yp in sorted(paths.factors_dir.glob("F*.yaml")):
        fid = yp.stem
        mp = paths.factor_md_file(fid)
        if not mp.exists():
            continue
        text = mp.read_text(encoding="utf-8")
        if "composite_grade" in text[:1000]:
            out.append(fid)
    return out


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--n", type=int, default=10)
    p.add_argument("--apply", action="store_true", help="Apply changes")
    p.add_argument("--dry-run", action="store_true", help="Preview only")
    args = p.parse_args()

    if not args.apply and not args.dry_run:
        args.dry_run = True

    paths = StoragePaths()
    batches = _find_recent_batches(paths.batches_dir, args.n)
    if not batches:
        print("No batches found.", file=sys.stderr)
        return 1

    print(f"Replaying status sync over {len(batches)} batches:")
    for bdir in reversed(batches):
        bid = bdir.name
        jpath = bdir / "judge.md"
        mpath = bdir / "manifest.yaml"
        direction = _direction_from_manifest(mpath)
        if direction is None or not jpath.exists():
            print(f"  {bid}: skipped (missing manifest.direction or judge.md)")
            continue
        dpath = paths.direction_file(direction)
        if not dpath.exists():
            print(f"  {bid} ({direction}): skipped (direction.md missing)")
            continue

        text_before = dpath.read_text(encoding="utf-8")
        status_before = _extract_status(text_before)

        if args.apply:
            judge_body = jpath.read_text(encoding="utf-8")
            sync_status_from_judge(dpath, judge_body=judge_body, batch_id=bid)
            status_after = _extract_status(dpath.read_text(encoding="utf-8"))
        else:
            # Dry run: load the function's decision without writing
            judge_body = jpath.read_text(encoding="utf-8")
            from research.memory.direction_updater import _parse_declared_status
            tgt = _parse_declared_status(judge_body)
            status_after = tgt if tgt and tgt != status_before else status_before

        changed = status_before != status_after
        tag = " ← APPLIED" if changed and args.apply else (" → would set" if changed else "")
        print(f"  {bid} ({direction}): {status_before} → {status_after}{tag}")

    if args.apply:
        print("\nRefreshing INDEX.md (frontmatter + auto-section + narrative blocks)…")
        from research.storage.state import StateFile
        state = StateFile(paths.state_file).read()
        refresh_index(paths, round_counter=state.round)
        print(f"  INDEX.md frontmatter now round={state.round}, last_batch={state.last_batch}")

    orphans = _find_orphan_reports(paths)
    if orphans:
        print("\nPotential orphan factor reports (check git status for these):")
        for fid in orphans:
            print(f"  - {fid}: run `research commit-report {fid}`")

    return 0


def _extract_status(text: str) -> str:
    m = re.search(r"^status:\s*(\S+)", text, re.MULTILINE)
    return m.group(1) if m else "?"


if __name__ == "__main__":
    sys.exit(main())
