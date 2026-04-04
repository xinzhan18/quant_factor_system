"""ResearchState CRUD.

Manages ``state/research_state.yaml`` and ``state/pending_holdout_queue.yaml``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml, save_yaml

logger = logging.getLogger(__name__)


class StateStore:
    """Read/write the global research state."""

    def __init__(self, paths: StoragePaths) -> None:
        self.paths = paths

    # ------------------------------------------------------------------
    # research_state.yaml
    # ------------------------------------------------------------------
    def load(self) -> dict:
        """Load the research state. Returns dict matching research_state.yaml schema."""
        return load_yaml(self.paths.research_state)

    def save(self, state: dict) -> None:
        """Persist the research state (atomic)."""
        state["last_updated_at"] = datetime.now(timezone.utc).isoformat()
        save_yaml(self.paths.research_state, state)

    # ------------------------------------------------------------------
    # pending_holdout_queue.yaml
    # ------------------------------------------------------------------
    def load_holdout_queue(self) -> dict:
        """Load the pending holdout review queue."""
        return load_yaml(self.paths.pending_holdout_queue)

    def save_holdout_queue(self, queue: dict) -> None:
        """Persist the pending holdout review queue (atomic)."""
        save_yaml(self.paths.pending_holdout_queue, queue)
