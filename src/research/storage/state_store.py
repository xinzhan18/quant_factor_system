"""ResearchState and PendingHoldoutQueue CRUD.

Manages ``state/research_state.yaml`` (the global entry point for all skills)
and ``state/pending_holdout_queue.yaml``.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
        return load_yaml(self._paths.pending_holdout_queue_file)

    def save_holdout_queue(self, data: dict[str, Any]) -> None:
        save_yaml(self._paths.pending_holdout_queue_file, data)

    def enqueue_holdout(self, entry: dict[str, Any]) -> None:
        """Append an entry to the pending holdout queue."""
        queue = self.load_holdout_queue()
        items = queue.setdefault("pending", [])
        items.append(entry)
        self.save_holdout_queue(queue)

    def dequeue_holdout(self) -> dict[str, Any] | None:
        """Pop the oldest entry from the pending holdout queue."""
        queue = self.load_holdout_queue()
        items = queue.get("pending", [])
        if not items:
            return None
        entry = items.pop(0)
        self.save_holdout_queue(queue)
        return entry

    def recompute_from_cards(self, cards_dir: Path) -> dict[str, Any]:
        """Recompute derived state fields (active/warm logic IDs) from card files.

        Only updates active_logic_ids and warm_logic_ids.
        Preserves all other state fields (current_batch, pending_holdout, etc.).
        """
        from .yaml_io import load_yaml

        active = []
        warm = []
        for card_file in sorted(cards_dir.glob("L*.yaml")):
            card = load_yaml(card_file)
            lid = card.get("logic_id", "")
            status = card.get("status", "")
            if status == "active":
                active.append(lid)
            elif status == "warm":
                warm.append(lid)

        return self.update_state({
            "active_logic_ids": active,
            "warm_logic_ids": warm,
        })


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
