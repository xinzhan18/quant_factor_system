#!/usr/bin/env python3
"""Historical storage repair — fixes all known data breaks.

Modes:
    --dry-run   (default) Report what would change, write nothing
    --apply     Execute all repairs
    --report-json PATH  Write repair summary to JSON

Idempotent — each function checks if fix is already applied.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

import yaml

from research.domain.batch_phases import (
    BATCH_USAGE_UNIFIED_FIELDS,
    LEDGER_TOP_LEVEL_WHITELIST,
    derive_phase_from_files,
)
from research.governance.holdout_queue import HoldoutQueue
from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml, save_yaml

PATHS = StoragePaths(ROOT / "storage")

# Default sample policy values
DEFAULT_TRAIN_RANGE = ["2015-01-01", "2021-12-31"]
DEFAULT_VALIDATION_RANGE = ["2022-01-01", "2023-12-31"]
DEFAULT_VALIDATION_WINDOW_ID = "val_2022_2023"


class RepairLog:
    """Collects repair actions for reporting."""

    def __init__(self, dry_run: bool = True) -> None:
        self.dry_run = dry_run
        self.actions: list[dict[str, str]] = []

    def record(self, category: str, message: str) -> None:
        prefix = "[DRY-RUN] " if self.dry_run else ""
        self.actions.append({"category": category, "message": message})
        print(f"  {prefix}{message}")

    @property
    def count(self) -> int:
        return len(self.actions)


# ------------------------------------------------------------------
# 2.1 Fix stray ledger top-level keys
# ------------------------------------------------------------------


def fix_stray_ledger_keys(log: RepairLog) -> None:
    """Merge stray top-level keys into batch_usage.batches."""
    ledger = load_yaml(PATHS.ledger_file)
    unexpected = set(ledger.keys()) - LEDGER_TOP_LEVEL_WHITELIST

    if not unexpected:
        return

    for key in sorted(unexpected):
        value = ledger[key]
        if key == "batches" and isinstance(value, dict):
            # Merge into batch_usage.batches
            bu = ledger.setdefault("batch_usage", {}).setdefault("batches", {})
            for bid, entry in value.items():
                if bid not in bu:
                    log.record("stray_key", f"Merged {key}.{bid} into batch_usage.batches")
                    if not log.dry_run:
                        bu[bid] = entry
                else:
                    log.record("stray_key", f"Skipped {key}.{bid} — already in batch_usage.batches")
        else:
            log.record("stray_key", f"Removing unexpected top-level key: {key!r}")

        if not log.dry_run:
            del ledger[key]

    if not log.dry_run:
        save_yaml(PATHS.ledger_file, ledger)


# ------------------------------------------------------------------
# 2.2 Backfill missing batch_usage entries
# ------------------------------------------------------------------


def _build_entry_from_disk(batch_id: str) -> dict[str, Any]:
    """Build a unified-schema entry from files on disk."""
    batch_dir = PATHS.batch_dir(batch_id)
    manifest = load_yaml(PATHS.batch_manifest_file(batch_id))
    packet_path = PATHS.judge_packet_file(batch_id)
    packet = load_yaml(packet_path) if packet_path.exists() else {}

    # Unwrap packet if needed
    if "judge_packet" in packet:
        packet = packet["judge_packet"]

    candidates = manifest.get("candidates", [])
    logic_ids = sorted({
        str(c.get("logic_id", ""))
        for c in candidates if c.get("logic_id")
    })
    if not logic_ids:
        # Try from batch_metadata
        meta = manifest.get("batch_metadata", {})
        lid = meta.get("logic_id", "")
        if lid:
            logic_ids = [str(lid)]

    phase = derive_phase_from_files(batch_dir)

    train_range = DEFAULT_TRAIN_RANGE
    validation_range = DEFAULT_VALIDATION_RANGE
    validation_window_id = DEFAULT_VALIDATION_WINDOW_ID
    holdout_used = False

    # Extract from packet if available
    sp = packet.get("sample_policy", {})
    if sp:
        train_range = sp.get("train_range", train_range)
        validation_range = sp.get("validation_range", validation_range)
        validation_window_id = sp.get("validation_window_id", validation_window_id)

    # Check holdout from briefs
    for brief in packet.get("candidate_briefs", []):
        if brief.get("holdout_review_recommended"):
            holdout_used = True
            break

    return {
        "batch_id": batch_id,
        "candidate_count": len(candidates),
        "logic_ids": logic_ids,
        "phase": phase,
        "holdout_used": holdout_used,
        "train_range": train_range,
        "validation_range": validation_range,
        "validation_window_id": validation_window_id,
    }


def backfill_missing_batch_usage_entries(log: RepairLog) -> None:
    """Add batch_usage entries for batch dirs missing from ledger."""
    ledger = load_yaml(PATHS.ledger_file)
    bu = ledger.setdefault("batch_usage", {}).setdefault("batches", {})

    for d in sorted(PATHS.batches_dir.iterdir()):
        if not d.is_dir() or not d.name.startswith("batch_"):
            continue
        bid = d.name
        if bid in bu:
            continue
        # Check manifest exists
        if not PATHS.batch_manifest_file(bid).exists():
            continue

        entry = _build_entry_from_disk(bid)
        log.record("backfill", f"Backfill batch_usage for {bid} (phase={entry['phase']})")
        if not log.dry_run:
            bu[bid] = entry

    if not log.dry_run:
        save_yaml(PATHS.ledger_file, ledger)


# ------------------------------------------------------------------
# 2.3 Normalize existing batch_usage entries
# ------------------------------------------------------------------


def normalize_existing_batch_usage_entries(log: RepairLog) -> None:
    """Normalize schema of existing entries to unified format."""
    ledger = load_yaml(PATHS.ledger_file)
    bu = ledger.get("batch_usage", {}).get("batches", {})
    changed = False

    for bid, entry in sorted(bu.items()):
        if not isinstance(entry, dict):
            continue
        fixes = []

        # logic_id → logic_ids
        if "logic_id" in entry and "logic_ids" not in entry:
            if not log.dry_run:
                entry["logic_ids"] = [entry.pop("logic_id")]
            fixes.append("logic_id→logic_ids")

        # batch_id
        if "batch_id" not in entry:
            if not log.dry_run:
                entry["batch_id"] = bid
            fixes.append("+batch_id")

        # holdout_used
        if "holdout_used" not in entry:
            if not log.dry_run:
                entry["holdout_used"] = False
            fixes.append("+holdout_used")

        # train_range, validation_range, validation_window_id
        for field, default in [
            ("train_range", DEFAULT_TRAIN_RANGE),
            ("validation_range", DEFAULT_VALIDATION_RANGE),
            ("validation_window_id", DEFAULT_VALIDATION_WINDOW_ID),
        ]:
            if field not in entry:
                # Try to get from disk
                packet_path = PATHS.judge_packet_file(bid)
                if packet_path.exists():
                    pkt = load_yaml(packet_path)
                    if "judge_packet" in pkt:
                        pkt = pkt["judge_packet"]
                    sp = pkt.get("sample_policy", {})
                    val = sp.get(field, default)
                else:
                    val = default
                if not log.dry_run:
                    entry[field] = val
                fixes.append(f"+{field}")

        if fixes:
            log.record("normalize", f"{bid}: {', '.join(fixes)}")
            changed = True

    if changed and not log.dry_run:
        save_yaml(PATHS.ledger_file, ledger)


# ------------------------------------------------------------------
# 2.4 Mark batch_059 as interrupted_judge
# ------------------------------------------------------------------


def fix_batch_059(log: RepairLog) -> None:
    """Mark batch_059 as interrupted_judge."""
    ledger = load_yaml(PATHS.ledger_file)
    bu = ledger.get("batch_usage", {}).get("batches", {})
    entry = bu.get("batch_059", {})

    if entry.get("phase") == "interrupted_judge":
        return  # already fixed

    if entry.get("phase") in ("abandoned", "finalized"):
        return  # don't override terminal states

    log.record("batch_059", "Set phase → interrupted_judge")
    if not log.dry_run:
        entry["phase"] = "interrupted_judge"
        bu["batch_059"] = entry
        save_yaml(PATHS.ledger_file, ledger)

        # Audit entry
        from research.storage.ledger_store import LedgerStore
        ls = LedgerStore(PATHS)
        ls.append_audit_entry(
            actor="repair_pipeline_state",
            action="mark_interrupted",
            target="batch_059",
            detail="Has judge_packet but no judge_report; marked interrupted_judge",
        )


# ------------------------------------------------------------------
# 2.5 Fix logic card thread alignment
# ------------------------------------------------------------------


def fix_thread_alignment(log: RepairLog) -> None:
    """Park active threads on parked/saturated/dead cards."""
    terminal = {"parked", "saturated", "dead"}

    for card_file in sorted(PATHS.logic_cards_dir.glob("L*.yaml")):
        card = load_yaml(card_file)
        logic_id = card.get("logic_id", card_file.stem)
        status = card.get("status", "")

        if status not in terminal:
            continue

        threads = card.get("deepening_threads", [])
        parked_any = False
        for t in threads:
            if isinstance(t, dict) and t.get("status") == "active":
                tid = t.get("id", "?")
                log.record("thread_align", f"{logic_id}/{tid}: active → parked")
                if not log.dry_run:
                    t["status"] = "parked"
                    parked_any = True

        if parked_any and not log.dry_run:
            save_yaml(card_file, card)


# ------------------------------------------------------------------
# 2.6 Backfill L006 reflection
# ------------------------------------------------------------------


def backfill_l006_reflection(log: RepairLog) -> None:
    """Create L006 reflection file if missing."""
    reflection_path = PATHS.logic_reflection_file("L006")

    # Check if already has batch_064 header
    if reflection_path.exists():
        content = reflection_path.read_text(encoding="utf-8")
        if "## Batch batch_064" in content:
            return  # already present

    log.record("reflection", "Create L006 reflection for batch_064")

    if log.dry_run:
        return

    card = load_yaml(PATHS.logic_card_file("L006"))
    bottleneck = card.get("evidence_summary", {}).get("current_bottleneck", "")
    generated = card.get("evidence_summary", {}).get("factors_generated", 0)
    admitted = card.get("evidence_summary", {}).get("factors_admitted", 0)

    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    content = f"""# L006 — {card.get('name', 'A股特有市场微结构 × 涨跌停动量')}

## Batch batch_064 — {now}

**Logic**: L006
**Generated**: {generated}  |  **Admitted**: {admitted}
**Status change**: → parked (All 6 candidates rejected as style traps)
**Bottleneck**: {bottleneck}

[Backfilled by repair_pipeline_state.py — original reflection was not generated during pipeline execution]
"""
    reflection_path.parent.mkdir(parents=True, exist_ok=True)
    reflection_path.write_text(content, encoding="utf-8")


# ------------------------------------------------------------------
# 2.7 Close batch_047 C002 holdout
# ------------------------------------------------------------------


def fix_holdout_batch_047(log: RepairLog) -> None:
    """Mark batch_047 C002 holdout as superseded in both queue and ledger."""
    # Fix queue
    queue = HoldoutQueue.load_yaml(str(PATHS.pending_holdout_queue_file))
    queue_changed = False
    for entry in queue.entries:
        if (
            entry.batch_id == "batch_047"
            and entry.candidate_id == "C002"
            and entry.status == "pending"
        ):
            log.record("holdout", "queue: batch_047/C002 pending → superseded")
            if not log.dry_run:
                entry.status = "superseded"
                queue_changed = True

    if queue_changed and not log.dry_run:
        queue.save_yaml(str(PATHS.pending_holdout_queue_file))
        from research.storage.state_store import StateStore
        state_store = StateStore(PATHS)
        actual_pending = len(queue.pending())
        state_store.update_state({"pending_holdout_count": actual_pending})
        log.record("holdout", f"Updated pending_holdout_count → {actual_pending}")

    # Fix ledger holdout_reviews
    ledger = load_yaml(PATHS.ledger_file)
    reviews = ledger.get("holdout_reviews", {}).get("reviews", [])
    ledger_changed = False
    for review in reviews:
        if (
            isinstance(review, dict)
            and review.get("target_id") == "C002"
            and review.get("status") == "pending"
        ):
            log.record("holdout", "ledger: HR_047_002 (C002) pending → superseded")
            if not log.dry_run:
                review["status"] = "superseded"
                ledger_changed = True

    if ledger_changed and not log.dry_run:
        save_yaml(PATHS.ledger_file, ledger)


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


ALL_REPAIRS = [
    ("Fix stray ledger keys", fix_stray_ledger_keys),
    ("Backfill missing batch_usage", backfill_missing_batch_usage_entries),
    ("Normalize batch_usage schema", normalize_existing_batch_usage_entries),
    ("Fix batch_059 phase", fix_batch_059),
    ("Fix thread alignment", fix_thread_alignment),
    ("Backfill L006 reflection", backfill_l006_reflection),
    ("Fix holdout batch_047 C002", fix_holdout_batch_047),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Historical storage repair")
    parser.add_argument(
        "--apply", action="store_true",
        help="Actually execute repairs (default: dry-run)"
    )
    parser.add_argument(
        "--report-json", help="Write repair summary to this path"
    )
    args = parser.parse_args()

    dry_run = not args.apply
    log = RepairLog(dry_run=dry_run)

    mode = "DRY-RUN" if dry_run else "APPLY"
    print(f"=== Storage Repair ({mode}) ===\n")

    for name, repair_fn in ALL_REPAIRS:
        print(f"\n[{name}]")
        repair_fn(log)

    print(f"\n{'='*60}")
    print(f"Total actions: {log.count} ({'would apply' if dry_run else 'applied'})")

    if dry_run and log.count > 0:
        print("\nRe-run with --apply to execute repairs.")

    if args.report_json:
        out_path = Path(args.report_json)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(
                {"mode": mode, "actions": log.actions},
                indent=2, ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        print(f"JSON report written to {out_path}")


if __name__ == "__main__":
    main()
