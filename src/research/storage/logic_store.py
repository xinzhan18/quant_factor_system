"""LogicRegistry and LogicCard CRUD.

Manages:
- ``logic/registry.yaml`` — lightweight index of all logics
- ``logic/cards/<logic_id>.yaml`` — full logic card objects
- ``logic/proposals/<proposal_id>.yaml`` — draft proposals
- ``logic/reviews/review_<proposal_id>.yaml`` — review results
- ``logic/snapshots/<name>.yaml`` — schedule snapshots
"""

from __future__ import annotations

import logging
from typing import List

from research.storage.paths import StoragePaths
from research.storage.yaml_io import glob_stems, load_yaml, save_yaml, upsert_list

logger = logging.getLogger(__name__)


class LogicStore:
    """CRUD operations for the logic layer."""

    def __init__(self, paths: StoragePaths) -> None:
        self.paths = paths

    # ------------------------------------------------------------------
    # registry (index)
    # ------------------------------------------------------------------
    def load_registry(self) -> dict:
        """Load ``logic/registry.yaml``."""
        return load_yaml(self.paths.logic_registry)

    def save_registry(self, registry: dict) -> None:
        """Persist ``logic/registry.yaml``."""
        save_yaml(self.paths.logic_registry, registry)

    def list_logics(self) -> List[dict]:
        """Return the ``logics`` list from the registry."""
        reg = self.load_registry()
        return reg.get("logics", [])

    def upsert_registry_entry(self, entry: dict) -> None:
        """Insert or update a single entry in the registry index.

        Matches on ``logic_id``.
        """
        reg = self.load_registry()
        logics: list = reg.setdefault("logics", [])
        upsert_list(logics, entry, "logic_id")
        self.save_registry(reg)

    # ------------------------------------------------------------------
    # cards
    # ------------------------------------------------------------------
    def load_card(self, logic_id: str) -> dict:
        """Load a single logic card."""
        return load_yaml(self.paths.logic_card(logic_id))

    def save_card(self, logic_id: str, card: dict) -> None:
        """Persist a single logic card."""
        save_yaml(self.paths.logic_card(logic_id), card)

    def list_card_ids(self) -> List[str]:
        """Return logic_ids for all card YAML files on disk."""
        return glob_stems(self.paths.logic_cards_dir)

    # ------------------------------------------------------------------
    # proposals
    # ------------------------------------------------------------------
    def load_proposal(self, proposal_id: str) -> dict:
        """Load a draft proposal."""
        return load_yaml(self.paths.logic_proposal(proposal_id))

    def save_proposal(self, proposal_id: str, proposal: dict) -> None:
        """Persist a draft proposal."""
        save_yaml(self.paths.logic_proposal(proposal_id), proposal)

    # ------------------------------------------------------------------
    # reviews
    # ------------------------------------------------------------------
    def load_review(self, proposal_id: str) -> dict:
        """Load a review for *proposal_id*."""
        return load_yaml(self.paths.logic_review(proposal_id))

    def save_review(self, proposal_id: str, review: dict) -> None:
        """Persist a review for *proposal_id*."""
        save_yaml(self.paths.logic_review(proposal_id), review)

    # ------------------------------------------------------------------
    # snapshots
    # ------------------------------------------------------------------
    def load_snapshot(self, snapshot_name: str) -> dict:
        """Load a schedule snapshot."""
        return load_yaml(self.paths.logic_snapshot(snapshot_name))

    def save_snapshot(self, snapshot_name: str, snapshot: dict) -> None:
        """Persist a schedule snapshot."""
        save_yaml(self.paths.logic_snapshot(snapshot_name), snapshot)

    def list_snapshots(self) -> List[str]:
        """Return snapshot names (without .yaml) sorted by name."""
        return glob_stems(self.paths.logic_snapshots_dir)

    # ------------------------------------------------------------------
    # convenience queries
    # ------------------------------------------------------------------
    def logics_by_status(self, status: str) -> List[dict]:
        """Return registry entries with the given *status*."""
        return [l for l in self.list_logics() if l.get("status") == status]
