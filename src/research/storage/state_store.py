"""ResearchState and PendingHoldoutQueue CRUD.

Manages ``state/research_state.yaml`` (the global entry point for all skills)
and ``state/pending_holdout_queue.yaml``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from research.governance.holdout_queue import HoldoutQueue

from .paths import StoragePaths
from .yaml_io import load_yaml, save_yaml


class StateStore:
    """CRUD for the global research state and holdout queue."""

    def __init__(self, paths: StoragePaths) -> None:
        self._paths = paths

    # ------------------------------------------------------------------
    # research_state.yaml
    # ------------------------------------------------------------------

    def load_state(self) -> dict[str, Any]:
        return load_yaml(self._paths.research_state_file)

    def save_state(self, data: dict[str, Any]) -> None:
        data["last_updated_at"] = _now_iso()
        save_yaml(self._paths.research_state_file, data)

    def update_state(self, patch: dict[str, Any]) -> dict[str, Any]:
        """Merge *patch* into the existing state and persist."""
        state = self.load_state()
        state.update(patch)
        self.save_state(state)
        return state

    # ------------------------------------------------------------------
    # pending_holdout_queue.yaml
    # ------------------------------------------------------------------

    def load_holdout_queue(self) -> dict[str, Any]:
        queue = HoldoutQueue.load_yaml(str(self._paths.pending_holdout_queue_file))
        return {"holdout_queue": queue.to_dict_list()}

    def save_holdout_queue(self, data: dict[str, Any]) -> None:
        items = data.get("holdout_queue")
        if items is None and "pending" in data:
            items = data.get("pending", [])
        queue = HoldoutQueue.from_dict_list(items or [])
        queue.save_yaml(str(self._paths.pending_holdout_queue_file))

    def enqueue_holdout(self, entry: dict[str, Any]) -> None:
        """Append an entry to the pending holdout queue."""
        queue = HoldoutQueue.load_yaml(str(self._paths.pending_holdout_queue_file))
        queue.enqueue(
            candidate_id=str(entry.get("candidate_id", entry.get("factor_id", ""))),
            logic_id=str(entry.get("logic_id", entry.get("candidate_id", entry.get("factor_id", "")))),
            family_id=str(entry.get("family_id", entry.get("candidate_id", entry.get("factor_id", "")))),
            batch_id=str(entry.get("batch_id", "")),
            experiment_lineage_tag=str(entry.get("experiment_lineage_tag", "")),
        )
        queue.save_yaml(str(self._paths.pending_holdout_queue_file))

    def dequeue_holdout(self) -> dict[str, Any] | None:
        """Pop the oldest entry from the pending holdout queue."""
        queue = HoldoutQueue.load_yaml(str(self._paths.pending_holdout_queue_file))
        pending = queue.pending()
        if not pending:
            return None
        entry = pending[0]
        queue.mark_reviewed(entry.candidate_id)
        queue.save_yaml(str(self._paths.pending_holdout_queue_file))
        return entry.to_dict()

    def recompute_from_cards(self, cards_dir: Path) -> dict[str, Any]:
        """Recompute derived state fields from card files.

        Updates active_logic_ids, warm_logic_ids, and schedulable_logic_ids
        (active + productive + warm).
        Preserves all other state fields (current_batch, pending_holdout, etc.).
        """
        from .yaml_io import load_yaml

        active = []
        warm = []
        productive = []
        for card_file in sorted(cards_dir.glob("L*.yaml")):
            card = load_yaml(card_file)
            lid = card.get("logic_id", "")
            status = card.get("status", "")
            if status == "active":
                active.append(lid)
            elif status == "warm":
                warm.append(lid)
            elif status == "productive":
                productive.append(lid)

        return self.update_state({
            "active_logic_ids": active,
            "warm_logic_ids": warm,
            "schedulable_logic_ids": sorted(active + productive + warm),
        })


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
