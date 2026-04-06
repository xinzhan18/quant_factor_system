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

    reviews = ledger.get("holdout_reviews", [])
    pending = [r for r in reviews if r.get("status") == "pending"]

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
