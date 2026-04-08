#!/usr/bin/env python3
"""Read-only storage audit: scans all truth sources and reports issues.

Usage:
    python scripts/audit_storage.py
    python scripts/audit_storage.py --report-json storage/runtime/audit_report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from research.domain.batch_phases import (
    BATCH_USAGE_UNIFIED_FIELDS,
    LEDGER_TOP_LEVEL_WHITELIST,
    derive_phase_from_files,
)
from research.governance.holdout_queue import HoldoutQueue
from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml

PATHS = StoragePaths(ROOT / "storage")


# ------------------------------------------------------------------
# Audit functions — each returns a list of issue strings
# ------------------------------------------------------------------


def audit_batch_dirs() -> list[str]:
    """Classify each batch dir by files present vs derived phase."""
    issues: list[str] = []
    for d in sorted(PATHS.batches_dir.iterdir()):
        if not d.is_dir() or not d.name.startswith("batch_"):
            continue
        files = {f.name for f in d.iterdir() if f.is_file()}
        derived = derive_phase_from_files(d)
        if derived == "interrupted_judge":
            issues.append(
                f"{d.name}: has judge_packet but no judge_report → interrupted_judge "
                f"(files: {sorted(files)})"
            )
    return issues


def audit_ledger_top_level_keys() -> list[str]:
    """Check for stray top-level keys in ledger.yaml."""
    ledger = load_yaml(PATHS.ledger_file)
    unexpected = set(ledger.keys()) - LEDGER_TOP_LEVEL_WHITELIST
    return [f"Stray ledger top-level key: {k!r}" for k in sorted(unexpected)]


def audit_ledger_coverage() -> list[str]:
    """Cross-ref batch dirs on disk vs batch_usage.batches entries."""
    issues: list[str] = []
    ledger = load_yaml(PATHS.ledger_file)
    batch_usage = ledger.get("batch_usage", {}).get("batches", {})

    # Batch dirs on disk
    on_disk = set()
    for d in sorted(PATHS.batches_dir.iterdir()):
        if d.is_dir() and d.name.startswith("batch_"):
            on_disk.add(d.name)

    # Missing from ledger
    in_ledger = set(batch_usage.keys())
    missing = sorted(on_disk - in_ledger)
    if missing:
        issues.append(f"Batches on disk but missing from batch_usage: {missing}")

    # In ledger but not on disk
    orphan = sorted(in_ledger - on_disk)
    if orphan:
        issues.append(f"Batches in batch_usage but no directory on disk: {orphan}")

    # Phase mismatch
    for bid in sorted(on_disk & in_ledger):
        derived = derive_phase_from_files(PATHS.batch_dir(bid))
        ledger_phase = batch_usage.get(bid, {}).get("phase", "")
        # finalized/abandoned in ledger are terminal — don't compare to disk files
        if ledger_phase in ("finalized", "abandoned"):
            continue
        if derived != ledger_phase:
            issues.append(
                f"{bid}: ledger phase={ledger_phase!r} but disk files imply {derived!r}"
            )

    return issues


def audit_batch_usage_schema() -> list[str]:
    """Check each batch_usage entry for missing unified schema fields."""
    issues: list[str] = []
    ledger = load_yaml(PATHS.ledger_file)
    batch_usage = ledger.get("batch_usage", {}).get("batches", {})

    for bid, entry in sorted(batch_usage.items()):
        if not isinstance(entry, dict):
            issues.append(f"{bid}: batch_usage entry is not a dict")
            continue
        # Check for singular logic_id instead of logic_ids
        if "logic_id" in entry and "logic_ids" not in entry:
            issues.append(f"{bid}: has 'logic_id' (singular) instead of 'logic_ids' (plural)")
        missing = set(BATCH_USAGE_UNIFIED_FIELDS) - set(entry.keys())
        # logic_id counts as logic_ids for this check
        if "logic_ids" in missing and "logic_id" in entry:
            missing.discard("logic_ids")
        if missing:
            issues.append(f"{bid}: missing unified schema fields: {sorted(missing)}")

    return issues


def audit_logic_cards() -> list[str]:
    """Check thread/status alignment and reflection existence."""
    issues: list[str] = []
    terminal_statuses = {"parked", "saturated", "dead"}

    for card_file in sorted(PATHS.logic_cards_dir.glob("L*.yaml")):
        card = load_yaml(card_file)
        logic_id = card.get("logic_id", card_file.stem)
        status = card.get("status", "")

        # Thread alignment
        if status in terminal_statuses:
            threads = card.get("deepening_threads", [])
            active_threads = [
                t.get("id", "?") for t in threads
                if isinstance(t, dict) and t.get("status") == "active"
            ]
            if active_threads:
                issues.append(
                    f"{logic_id}: card is {status!r} but has active threads: {active_threads}"
                )

        # Reflection existence
        last_batch = card.get("last_reflected_batch", "")
        if last_batch:
            reflection_file = PATHS.logic_reflection_file(logic_id)
            if not reflection_file.exists():
                issues.append(
                    f"{logic_id}: last_reflected_batch={last_batch!r} "
                    f"but reflection file missing"
                )

    return issues


def audit_holdout_queue() -> list[str]:
    """Check pending holdout entries for metadata and expiry."""
    issues: list[str] = []
    queue = HoldoutQueue.load_yaml(str(PATHS.pending_holdout_queue_file))

    for entry in queue.entries:
        if entry.status == "pending":
            if not entry.logic_id:
                issues.append(
                    f"Holdout {entry.batch_id}/{entry.candidate_id}: "
                    f"pending but missing logic_id"
                )
            if not entry.family_id:
                issues.append(
                    f"Holdout {entry.batch_id}/{entry.candidate_id}: "
                    f"pending but missing family_id"
                )

    # Cross-ref with ledger
    ledger = load_yaml(PATHS.ledger_file)
    ledger_reviews = ledger.get("holdout_reviews", {}).get("reviews", [])
    ledger_pending = sorted(
        str(item.get("target_id", ""))
        for item in ledger_reviews
        if isinstance(item, dict) and item.get("status") == "pending"
    )
    queue_pending = sorted(e.candidate_id for e in queue.pending())
    if ledger_pending != queue_pending:
        issues.append(
            f"Holdout queue/ledger mismatch: queue_pending={queue_pending}, "
            f"ledger_pending={ledger_pending}"
        )

    return issues


def audit_state_consistency() -> list[str]:
    """Recompute state from cards and compare."""
    issues: list[str] = []
    state = load_yaml(PATHS.research_state_file)

    # Recompute from cards
    active, warm, schedulable = [], [], []
    for card_file in sorted(PATHS.logic_cards_dir.glob("L*.yaml")):
        card = load_yaml(card_file)
        lid = card.get("logic_id", "")
        s = card.get("status", "")
        if s == "active":
            active.append(lid)
        elif s == "warm":
            warm.append(lid)
        elif s == "productive":
            schedulable.append(lid)

    expected_schedulable = sorted(active + warm + schedulable)

    if sorted(state.get("active_logic_ids", [])) != sorted(active):
        issues.append(
            f"State active_logic_ids mismatch: state={state.get('active_logic_ids')}, "
            f"computed={active}"
        )
    if sorted(state.get("warm_logic_ids", [])) != sorted(warm):
        issues.append(
            f"State warm_logic_ids mismatch: state={state.get('warm_logic_ids')}, "
            f"computed={warm}"
        )
    if sorted(state.get("schedulable_logic_ids", [])) != expected_schedulable:
        issues.append(
            f"State schedulable_logic_ids mismatch: "
            f"state={state.get('schedulable_logic_ids')}, computed={expected_schedulable}"
        )

    # Holdout count
    queue = HoldoutQueue.load_yaml(str(PATHS.pending_holdout_queue_file))
    actual_pending = len(queue.pending())
    state_pending = state.get("pending_holdout_count", 0)
    if state_pending != actual_pending:
        issues.append(
            f"State pending_holdout_count={state_pending} but actual pending={actual_pending}"
        )

    return issues


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------

ALL_CHECKS = [
    ("Batch directories", audit_batch_dirs),
    ("Ledger top-level keys", audit_ledger_top_level_keys),
    ("Ledger coverage", audit_ledger_coverage),
    ("Batch usage schema", audit_batch_usage_schema),
    ("Logic cards", audit_logic_cards),
    ("Holdout queue", audit_holdout_queue),
    ("State consistency", audit_state_consistency),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Read-only storage audit")
    parser.add_argument("--report-json", help="Write JSON report to this path")
    args = parser.parse_args()

    total_issues = 0
    report: dict[str, list[str]] = {}

    for name, check_fn in ALL_CHECKS:
        issues = check_fn()
        report[name] = issues
        total_issues += len(issues)

        if issues:
            print(f"\n[{name}] — {len(issues)} issue(s):")
            for issue in issues:
                print(f"  ⚠ {issue}")
        else:
            print(f"[{name}] — OK")

    print(f"\n{'='*60}")
    print(f"Total issues: {total_issues}")

    if args.report_json:
        out_path = Path(args.report_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"JSON report written to {out_path}")

    sys.exit(0 if total_issues == 0 else 1)


if __name__ == "__main__":
    main()
