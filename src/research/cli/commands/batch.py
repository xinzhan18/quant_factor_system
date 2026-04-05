"""CLI command: batch — batch lifecycle management.

Sub-actions:
  list    — list all batch files and their evaluation status
  next-id — print the next available batch ID
  status  — show detailed status for a specific batch
"""

from __future__ import annotations

import re
from pathlib import Path

CANDIDATES_DIR = Path("storage/candidates")


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
    if not CANDIDATES_DIR.exists():
        print(f"Candidates directory not found: {CANDIDATES_DIR}")
        return

    batch_files = sorted(CANDIDATES_DIR.glob("batch_*.yaml"))
    # Exclude result/idea_report/judge_report files
    batch_files = [f for f in batch_files
                   if not any(s in f.name for s in ["_result", "_idea_report",
                                                     "_judge_report", "_values"])]
    if not batch_files:
        print("No batch files found.")
        return

    print(f"{'Batch':15s} {'Evaluated':10s} {'Judged':10s}")
    print("-" * 40)
    for bf in batch_files:
        batch_id = bf.stem
        result_path = bf.parent / f"{batch_id}_result.yaml"
        judge_path = bf.parent / f"{batch_id}_judge_report.yaml"
        evaluated = "yes" if result_path.exists() else "no"
        judged = "yes" if judge_path.exists() else "no"
        print(f"  {batch_id:15s} {evaluated:10s} {judged:10s}")


def _batch_next_id():
    """Print the next available batch ID."""
    max_num = 0
    if CANDIDATES_DIR.exists():
        for f in CANDIDATES_DIR.glob("batch_*.yaml"):
            m = re.search(r"batch_(\d+)", f.stem)
            if m:
                max_num = max(max_num, int(m.group(1)))
    next_id = f"batch_{max_num + 1:03d}"
    print(next_id)


def _batch_status(batch_id=None):
    """Show detailed status for a specific batch."""
    if not batch_id:
        # Find the latest batch
        if not CANDIDATES_DIR.exists():
            print("No candidates directory found.")
            return
        batch_files = sorted(CANDIDATES_DIR.glob("batch_*.yaml"))
        batch_files = [f for f in batch_files
                       if not any(s in f.name for s in ["_result", "_idea_report",
                                                         "_judge_report", "_values"])]
        if not batch_files:
            print("No batch files found.")
            return
        batch_id = batch_files[-1].stem

    import yaml

    batch_path = CANDIDATES_DIR / f"{batch_id}.yaml"
    result_path = CANDIDATES_DIR / f"{batch_id}_result.yaml"

    if not batch_path.exists():
        print(f"Batch file not found: {batch_path}")
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
