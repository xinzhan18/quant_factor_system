"""CLI command: batch — batch lifecycle management.

Sub-actions:
  list    — list all batch files and their evaluation status
  next-id — print the next available batch ID
  status  — show detailed status for a specific batch
"""

from __future__ import annotations

import re
from pathlib import Path

from research.storage.paths import StoragePaths

BATCHES_DIR = StoragePaths().batches_dir


def cmd_batch(args):
    """Dispatch batch sub-actions."""
    action = args.batch_action

    if action == "list":
        _batch_list()
    elif action == "next-id":
        _batch_next_id()
    elif action == "status":
        _batch_status(batch_id=getattr(args, "batch_id", None))


def _batch_list():
    """List all batch files and their evaluation status."""
    if not BATCHES_DIR.exists():
        print(f"Batches directory not found: {BATCHES_DIR}")
        return

    batch_dirs = sorted(
        p for p in BATCHES_DIR.iterdir()
        if p.is_dir() and (p / "manifest.yaml").exists()
    )
    if not batch_dirs:
        print("No batch files found.")
        return

    print(f"{'Batch':15s} {'Evaluated':10s} {'Judged':10s}")
    print("-" * 40)
    for bd in batch_dirs:
        batch_id = bd.name
        evaluated = "yes" if (bd / "research_result.yaml").exists() else "no"
        judged = "yes" if (bd / "judge_report.yaml").exists() else "no"
        print(f"  {batch_id:15s} {evaluated:10s} {judged:10s}")


def _batch_next_id():
    """Print the next available batch ID."""
    max_num = 0
    if BATCHES_DIR.exists():
        for d in BATCHES_DIR.iterdir():
            if d.is_dir():
                m = re.search(r"batch_(\d+)", d.name)
                if m:
                    max_num = max(max_num, int(m.group(1)))
    next_id = f"batch_{max_num + 1:03d}"
    print(next_id)


def _batch_status(batch_id=None):
    """Show detailed status for a specific batch."""
    if not batch_id:
        if not BATCHES_DIR.exists():
            print("No batches directory found.")
            return
        batch_dirs = sorted(
            p for p in BATCHES_DIR.iterdir()
            if p.is_dir() and (p / "manifest.yaml").exists()
        )
        if not batch_dirs:
            print("No batch files found.")
            return
        batch_id = batch_dirs[-1].name

    import yaml

    bd = BATCHES_DIR / batch_id
    batch_path = bd / "manifest.yaml"
    result_path = bd / "research_result.yaml"

    if not batch_path.exists():
        print(f"Batch manifest not found: {batch_path}")
        return

    with open(batch_path) as f:
        batch_data = yaml.safe_load(f)

    candidates = batch_data.get("candidates", [])
    print(f"Batch: {batch_id}")
    print(f"  Candidates: {len(candidates)}")
    print(f"  Evaluated:  {'yes' if result_path.exists() else 'no'}")

    if result_path.exists():
        with open(result_path) as f:
            result_data = yaml.unsafe_load(f)
        screened = result_data.get("screened", [])
        rejected = result_data.get("rejected", [])
        print(f"  Screened:   {len(screened)}")
        print(f"  Rejected:   {len(rejected)}")
        for s in screened:
            name = s.get("name", "?")
            ic = s.get("metrics", {}).get("ic_mean", "N/A")
            print(f"    + {name}: IC={ic}")
