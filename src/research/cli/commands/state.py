"""CLI command: state — research state overview + mutations.

Reads/writes storage/state/research_state.yaml.

Usage:
    research state              # print current state
    research state set KEY VAL  # update a single key
    research state clear-batch  # reset batch fields after cycle completes
"""

from __future__ import annotations

import json

from research.storage.state_store import StateStore
from research.storage.paths import StoragePaths

_store = StateStore(StoragePaths())


def cmd_state(args):
    """Dispatch state subcommands."""
    action = getattr(args, "state_action", None)

    if action == "set":
        _cmd_set(args.key, args.value)
    elif action == "clear-batch":
        _cmd_clear_batch()
    elif action == "sync-holdout":
        _cmd_sync_holdout()
    elif action == "finalize-batch":
        _cmd_finalize_batch(args.batch_id)
    elif action == "validate-consistency":
        _cmd_validate_consistency(getattr(args, "batch_id", None))
    elif action == "reconcile":
        _cmd_reconcile(args)
    else:
        _cmd_show()


def _cmd_show():
    """Print the current research state."""
    state = _store.load_state()

    if not state:
        print("Research state is empty.")
        print("Hint: initialize with `python scripts/init_new_storage.py`")
        return

    print("=== Research State ===\n")

    print(f"Current batch:       {state.get('current_batch') or '(idle)'}")
    print(f"Batch phase:         {state.get('current_batch_phase') or '-'}")
    print(f"Last completed:      {state.get('last_completed_batch') or '-'}")

    holdout = state.get("pending_holdout_count", 0)
    if holdout:
        print(f"Pending holdout:     {holdout}  *** ACTION REQUIRED ***")
    else:
        print(f"Pending holdout:     0")

    active = state.get("active_logic_ids", [])
    print(f"\nActive logics ({len(active)}):")
    for lid in active:
        print(f"  - {lid}")

    schedulable = state.get("schedulable_logic_ids", [])
    print(f"\nSchedulable logics ({len(schedulable)}):")
    for lid in schedulable:
        print(f"  - {lid}")

    updated = state.get("last_updated_at", "-")
    print(f"\nLast updated: {updated}")


def _cmd_set(key: str, value: str):
    """Set a single key in research state."""
    # Auto-parse value types
    parsed = _parse_value(value)
    _store.update_state({key: parsed})
    print(f"state.{key} = {parsed}")


def _cmd_clear_batch():
    """Clear batch fields after a cycle completes."""
    state = _store.load_state()
    last = state.get("current_batch")
    patch = {
        "current_batch": None,
        "current_batch_phase": None,
    }
    if last:
        patch["last_completed_batch"] = last
    _store.update_state(patch)
    print(f"Batch cleared. last_completed_batch = {last}")


def _cmd_sync_holdout():
    """Sync pending holdout reviews from ledger → queue + state count."""
    import yaml
    from research.governance.holdout_queue import HoldoutQueue

    # Read ledger
    ledger_path = StoragePaths().ledger_file
    with open(ledger_path) as f:
        ledger = yaml.safe_load(f) or {}

    holdout_section = ledger.get("holdout_reviews", {})
    # LedgerStore stores reviews as {"reviews": [...]}, handle both formats
    if isinstance(holdout_section, dict):
        reviews = holdout_section.get("reviews", [])
    else:
        reviews = holdout_section if isinstance(holdout_section, list) else []
    pending = [r for r in reviews if isinstance(r, dict) and r.get("status") == "pending"]

    # Load existing queue, enqueue missing entries
    queue_path = str(StoragePaths().pending_holdout_queue_file)
    queue = HoldoutQueue.load_yaml(queue_path)
    existing_ids = {e.candidate_id for e in queue.entries}

    added = 0
    for r in pending:
        cid = r.get("target_id", "")
        if cid and cid not in existing_ids:
            queue.enqueue(
                candidate_id=cid,
                logic_id=r.get("logic_id", ""),
                family_id=r.get("family_id", ""),
                batch_id=r.get("batch_id", ""),
            )
            added += 1

    queue.save_yaml(queue_path)

    # Update state count
    _store.update_state({"pending_holdout_count": len(queue.pending())})

    print(f"Synced: {added} new entries enqueued, {len(queue.pending())} total pending")


def _cmd_finalize_batch(batch_id: str) -> None:
    from research.storage.finalizer import BatchFinalizer

    result = BatchFinalizer(StoragePaths()).finalize_batch(batch_id)
    print(f"Finalized: {batch_id}")
    print(f"Updated logics:      {', '.join(result.updated_logic_ids) or '-'}")
    print(f"Active logic ids:    {', '.join(result.active_logic_ids) or '-'}")
    print(f"Warm logic ids:      {', '.join(result.warm_logic_ids) or '-'}")
    print(f"Schedulable ids:     {', '.join(result.schedulable_logic_ids) or '-'}")
    if not result.consistency_ok:
        print(f"\nConsistency warnings ({len(result.consistency_errors)}):")
        for err in result.consistency_errors:
            print(f"  ⚠ {err}")


def _cmd_validate_consistency(batch_id: str | None) -> None:
    from research.storage.consistency import StorageConsistencyChecker

    report = StorageConsistencyChecker(StoragePaths()).check(batch_id=batch_id)
    if report.ok:
        print("Storage consistency: OK")
        return
    print("Storage consistency: FAILED")
    for err in report.errors:
        print(f"- {err}")
    raise SystemExit(1)


def _cmd_reconcile(args) -> None:
    """Recovery from interrupted flows — recompute derived state.

    Default: safe writes (recompute state, sync holdout, clean stray keys, normalize schema).
    --report-only: pure read-only, only run checks.
    --full-apply: also backfill missing batch_usage and finalize judged-but-unfinalised batches.
    """
    from research.domain.batch_phases import (
        LEDGER_TOP_LEVEL_WHITELIST,
        derive_phase_from_files,
    )
    from research.storage.consistency import StorageConsistencyChecker
    from research.storage.ledger_store import LedgerStore
    from research.storage.yaml_io import load_yaml, save_yaml

    report_only = getattr(args, "report_only", False)
    full_apply = getattr(args, "full_apply", False)
    paths = StoragePaths()
    ledger = LedgerStore(paths)
    actions: list[str] = []

    # 1. Recompute state from cards
    if not report_only:
        _store.recompute_from_cards(paths.logic_cards_dir)
        actions.append("Recomputed state from logic cards")

    # 2. Sync holdout count
    if not report_only:
        from research.governance.holdout_queue import HoldoutQueue
        queue = HoldoutQueue.load_yaml(str(paths.pending_holdout_queue_file))
        _store.update_state({"pending_holdout_count": len(queue.pending())})
        actions.append("Synced pending_holdout_count")

    # 3. Clean stray ledger keys
    if not report_only:
        raw = load_yaml(paths.ledger_file)
        stray = set(raw.keys()) - LEDGER_TOP_LEVEL_WHITELIST
        if stray:
            bu = raw.setdefault("batch_usage", {}).setdefault("batches", {})
            for key in sorted(stray):
                val = raw[key]
                if key == "batches" and isinstance(val, dict):
                    for bid, entry in val.items():
                        if bid not in bu:
                            bu[bid] = entry
                del raw[key]
            save_yaml(paths.ledger_file, raw)
            actions.append(f"Cleaned stray ledger keys: {sorted(stray)}")

    # 4. Normalize batch_usage schema (safe)
    if not report_only:
        raw = load_yaml(paths.ledger_file)
        bu = raw.get("batch_usage", {}).get("batches", {})
        for bid, entry in bu.items():
            if not isinstance(entry, dict):
                continue
            if "logic_id" in entry and "logic_ids" not in entry:
                entry["logic_ids"] = [entry.pop("logic_id")]
            if "batch_id" not in entry:
                entry["batch_id"] = bid
            entry.setdefault("holdout_used", False)
            entry.setdefault("train_range", ["2015-01-01", "2021-12-31"])
            entry.setdefault("validation_range", ["2022-01-01", "2023-12-31"])
            entry.setdefault("validation_window_id", "val_2022_2023")
        save_yaml(paths.ledger_file, raw)
        actions.append("Normalized batch_usage schema")

    # 5. Full-apply extras
    if full_apply:
        # Backfill missing batch_usage from disk
        raw = load_yaml(paths.ledger_file)
        bu = raw.get("batch_usage", {}).get("batches", {})
        for d in sorted(paths.batches_dir.iterdir()):
            if not d.is_dir() or not d.name.startswith("batch_"):
                continue
            bid = d.name
            if bid in bu:
                continue
            if not paths.batch_manifest_file(bid).exists():
                continue
            manifest = load_yaml(paths.batch_manifest_file(bid))
            candidates = manifest.get("candidates", [])
            logic_ids = sorted({
                str(c.get("logic_id", ""))
                for c in candidates if c.get("logic_id")
            })
            phase = derive_phase_from_files(d)
            bu[bid] = {
                "batch_id": bid,
                "candidate_count": len(candidates),
                "logic_ids": logic_ids,
                "phase": phase,
                "holdout_used": False,
                "train_range": ["2015-01-01", "2021-12-31"],
                "validation_range": ["2022-01-01", "2023-12-31"],
                "validation_window_id": "val_2022_2023",
            }
            actions.append(f"Backfilled batch_usage for {bid}")
        save_yaml(paths.ledger_file, raw)

    # 6. Extended consistency check
    checker = StorageConsistencyChecker(paths)
    cr = checker.check_extended()

    # Report
    print("=== Reconcile Report ===\n")
    if actions:
        print(f"Actions taken ({len(actions)}):")
        for a in actions:
            print(f"  ✓ {a}")
    elif report_only:
        print("(report-only mode — no writes)")

    if cr.ok:
        print("\nConsistency: OK")
    else:
        print(f"\nConsistency issues ({len(cr.errors)}):")
        for err in cr.errors:
            print(f"  ⚠ {err}")
        raise SystemExit(1)


def _parse_value(value: str):
    """Best-effort parse: null, int, list, or string."""
    if value in ("null", "None", "none"):
        return None
    try:
        return int(value)
    except ValueError:
        pass
    if value.startswith("["):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            pass
    return value
