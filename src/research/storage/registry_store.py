"""FactorRegistry and FamilyRegistry CRUD.

Manages:
- ``registry/factors/index.yaml`` — lightweight factor index
- ``registry/factors/factor_<id>.yaml`` — full factor detail cards
- ``registry/families/family_registry.yaml`` — family definitions
"""

from __future__ import annotations

import logging
from typing import List

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml, save_yaml, upsert_list

logger = logging.getLogger(__name__)


class RegistryStore:
    """CRUD for the factor and family registries."""

    def __init__(self, paths: StoragePaths) -> None:
        self.paths = paths

    # ------------------------------------------------------------------
    # factor index
    # ------------------------------------------------------------------
    def load_factor_index(self) -> dict:
        """Load ``registry/factors/index.yaml``."""
        return load_yaml(self.paths.factor_index)

    def save_factor_index(self, index: dict) -> None:
        """Persist the factor index."""
        save_yaml(self.paths.factor_index, index)

    def list_factors(self) -> List[dict]:
        """Return the ``factors`` list from the index."""
        idx = self.load_factor_index()
        return idx.get("factors", [])

    def upsert_factor_entry(self, entry: dict) -> None:
        """Insert or update a single factor in the index.

        Matches on ``factor_id``.
        """
        idx = self.load_factor_index()
        factors: list = idx.setdefault("factors", [])
        upsert_list(factors, entry, "factor_id")
        self.save_factor_index(idx)

    def remove_factor_entry(self, factor_id: str) -> bool:
        """Remove a factor from the index. Returns True if found and removed."""
        idx = self.load_factor_index()
        factors: list = idx.get("factors", [])
        original_len = len(factors)
        factors = [f for f in factors if f.get("factor_id") != factor_id]
        if len(factors) == original_len:
            return False
        idx["factors"] = factors
        self.save_factor_index(idx)
        return True

    # ------------------------------------------------------------------
    # factor detail cards
    # ------------------------------------------------------------------
    def load_factor_detail(self, factor_id: str) -> dict:
        """Load a single factor detail YAML."""
        return load_yaml(self.paths.factor_detail(factor_id))

    def save_factor_detail(self, factor_id: str, detail: dict) -> None:
        """Persist a single factor detail YAML."""
        save_yaml(self.paths.factor_detail(factor_id), detail)

    def list_factor_detail_ids(self) -> List[str]:
        """Return factor IDs for all detail files on disk.

        Extracts the ID from filenames like ``factor_001.yaml`` -> ``001``.
        """
        d = self.paths.factors_dir
        if not d.exists():
            return []
        ids = []
        for p in d.glob("factor_*.yaml"):
            stem = p.stem  # e.g. "factor_001"
            fid = stem.replace("factor_", "", 1)
            ids.append(fid)
        return sorted(ids)

    # ------------------------------------------------------------------
    # family registry
    # ------------------------------------------------------------------
    def load_family_registry(self) -> dict:
        """Load ``registry/families/family_registry.yaml``."""
        return load_yaml(self.paths.family_registry)

    def save_family_registry(self, registry: dict) -> None:
        """Persist the family registry."""
        save_yaml(self.paths.family_registry, registry)

    def list_families(self) -> List[dict]:
        """Return the ``families`` list."""
        reg = self.load_family_registry()
        return reg.get("families", [])

    def upsert_family(self, family: dict) -> None:
        """Insert or update a single family entry. Matches on ``family_id``."""
        reg = self.load_family_registry()
        families: list = reg.setdefault("families", [])
        upsert_list(families, family, "family_id")
        self.save_family_registry(reg)
