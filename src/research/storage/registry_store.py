"""FactorRegistry and FamilyRegistry CRUD.

Manages ``registry/factors/index.yaml``, individual ``factor_<id>.yaml``
detail files, and ``registry/families/family_registry.yaml``.
"""

from __future__ import annotations

from typing import Any

from .paths import StoragePaths
from .yaml_io import load_yaml, save_yaml


class RegistryStore:
    """CRUD for the factor and family registries."""

    def __init__(self, paths: StoragePaths) -> None:
        self._paths = paths

    # ------------------------------------------------------------------
    # factors/index.yaml
    # ------------------------------------------------------------------

    def load_factor_index(self) -> dict[str, Any]:
        return load_yaml(self._paths.factor_index_file)

    def save_factor_index(self, data: dict[str, Any]) -> None:
        save_yaml(self._paths.factor_index_file, data)

    def upsert_factor_entry(self, factor_id: str, entry: dict[str, Any]) -> None:
        """Insert or update a single factor entry in the index."""
        index = self.load_factor_index()
        items: list[dict[str, Any]] = index.setdefault("factors", [])
        for i, item in enumerate(items):
            if item.get("factor_id") == factor_id:
                items[i] = {**entry, "factor_id": factor_id}
                self.save_factor_index(index)
                return
        items.append({**entry, "factor_id": factor_id})
        self.save_factor_index(index)

    def remove_factor_entry(self, factor_id: str) -> None:
        index = self.load_factor_index()
        items: list[dict[str, Any]] = index.get("factors", [])
        index["factors"] = [it for it in items if it.get("factor_id") != factor_id]
        self.save_factor_index(index)

    def list_factor_ids(self) -> list[str]:
        index = self.load_factor_index()
        return [f["factor_id"] for f in index.get("factors", []) if "factor_id" in f]

    # ------------------------------------------------------------------
    # factors/factor_<factor_id>.yaml (detail)
    # ------------------------------------------------------------------

    def load_factor_detail(self, factor_id: str) -> dict[str, Any]:
        return load_yaml(self._paths.factor_detail_file(factor_id))

    def save_factor_detail(self, factor_id: str, data: dict[str, Any]) -> None:
        data["factor_id"] = factor_id
        save_yaml(self._paths.factor_detail_file(factor_id), data)

    def delete_factor_detail(self, factor_id: str) -> None:
        path = self._paths.factor_detail_file(factor_id)
        if path.exists():
            path.unlink()

    # ------------------------------------------------------------------
    # families/family_registry.yaml
    # ------------------------------------------------------------------

    def load_family_registry(self) -> dict[str, Any]:
        return load_yaml(self._paths.family_registry_file)

    def save_family_registry(self, data: dict[str, Any]) -> None:
        save_yaml(self._paths.family_registry_file, data)

    def upsert_family(self, family_id: str, entry: dict[str, Any]) -> None:
        """Insert or update a single family in the registry."""
        reg = self.load_family_registry()
        items: list[dict[str, Any]] = reg.setdefault("families", [])
        for i, item in enumerate(items):
            if item.get("family_id") == family_id:
                items[i] = {**entry, "family_id": family_id}
                self.save_family_registry(reg)
                return
        items.append({**entry, "family_id": family_id})
        self.save_family_registry(reg)
