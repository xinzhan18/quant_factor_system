"""LogicRegistry and LogicCard CRUD.

Manages ``logic/registry.yaml`` (index of all logics) and individual
``logic/cards/<logic_id>.yaml`` files, plus proposal and review artefacts.
"""

from __future__ import annotations

from typing import Any

from .paths import StoragePaths
from .yaml_io import load_yaml, save_yaml


class LogicStore:
    """CRUD for the logic layer: registry, cards, proposals, reviews, snapshots."""

    def __init__(self, paths: StoragePaths) -> None:
        self._paths = paths

    # ------------------------------------------------------------------
    # registry.yaml (index)
    # ------------------------------------------------------------------

    def load_registry(self) -> dict[str, Any]:
        return load_yaml(self._paths.logic_registry_file)

    def save_registry(self, data: dict[str, Any]) -> None:
        save_yaml(self._paths.logic_registry_file, data)

    def upsert_registry_entry(self, logic_id: str, entry: dict[str, Any]) -> None:
        """Insert or update a single logic entry in the registry index."""
        reg = self.load_registry()
        items: list[dict[str, Any]] = reg.setdefault("logics", [])
        for i, item in enumerate(items):
            if item.get("logic_id") == logic_id:
                items[i] = {**entry, "logic_id": logic_id}
                self.save_registry(reg)
                return
        items.append({**entry, "logic_id": logic_id})
        self.save_registry(reg)

    def remove_registry_entry(self, logic_id: str) -> None:
        reg = self.load_registry()
        items: list[dict[str, Any]] = reg.get("logics", [])
        reg["logics"] = [it for it in items if it.get("logic_id") != logic_id]
        self.save_registry(reg)

    # ------------------------------------------------------------------
    # cards/<logic_id>.yaml
    # ------------------------------------------------------------------

    def load_card(self, logic_id: str) -> dict[str, Any]:
        return load_yaml(self._paths.logic_card_file(logic_id))

    def save_card(self, logic_id: str, data: dict[str, Any]) -> None:
        data["logic_id"] = logic_id
        save_yaml(self._paths.logic_card_file(logic_id), data)

    def list_cards(self) -> list[str]:
        d = self._paths.logic_cards_dir
        if not d.exists():
            return []
        return sorted(p.stem for p in d.glob("*.yaml"))

    def delete_card(self, logic_id: str) -> None:
        path = self._paths.logic_card_file(logic_id)
        if path.exists():
            path.unlink()

    # ------------------------------------------------------------------
    # proposals/<proposal_id>.yaml
    # ------------------------------------------------------------------

    def load_proposal(self, proposal_id: str) -> dict[str, Any]:
        return load_yaml(self._paths.logic_proposal_file(proposal_id))

    def save_proposal(self, proposal_id: str, data: dict[str, Any]) -> None:
        data["proposal_id"] = proposal_id
        save_yaml(self._paths.logic_proposal_file(proposal_id), data)

    def list_proposals(self) -> list[str]:
        d = self._paths.logic_proposals_dir
        if not d.exists():
            return []
        return sorted(p.stem for p in d.glob("*.yaml"))

    # ------------------------------------------------------------------
    # reviews/review_<proposal_id>.yaml
    # ------------------------------------------------------------------

    def load_review(self, proposal_id: str) -> dict[str, Any]:
        return load_yaml(self._paths.logic_review_file(proposal_id))

    def save_review(self, proposal_id: str, data: dict[str, Any]) -> None:
        data["proposal_id"] = proposal_id
        save_yaml(self._paths.logic_review_file(proposal_id), data)

    # ------------------------------------------------------------------
    # snapshots/<snapshot_name>.yaml
    # ------------------------------------------------------------------

    def load_snapshot(self, snapshot_name: str) -> dict[str, Any]:
        return load_yaml(self._paths.logic_snapshot_file(snapshot_name))

    def save_snapshot(self, snapshot_name: str, data: dict[str, Any]) -> None:
        save_yaml(self._paths.logic_snapshot_file(snapshot_name), data)

    def list_snapshots(self) -> list[str]:
        d = self._paths.logic_snapshots_dir
        if not d.exists():
            return []
        return sorted(p.stem for p in d.glob("*.yaml"))
