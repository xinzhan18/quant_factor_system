"""Family registry — CRUD for factor families.

Families group factors that share structural patterns. Three states:
- **registered**: Formally recognized family with a known structural signature.
- **provisional**: Auto-created from pattern detection. Uses ``PF_`` prefix.
                   No hard blocking; factors can still use provisional families.
- **unknown**:    Fallback for factors that don't match any family.

Storage: YAML files under ``storage/registry/families/``.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from research.logic._yaml_utils import dump_yaml, now_ts

logger = logging.getLogger(__name__)

VALID_FAMILY_STATUSES = frozenset({"registered", "provisional", "unknown"})
PROVISIONAL_PREFIX = "PF_"


@dataclass
class FamilyRecord:
    """A factor family record."""

    family_id: str
    name: str
    status: str  # registered / provisional / unknown
    description: str = ""
    structural_signature: str = ""
    typical_ops: List[str] = field(default_factory=list)
    typical_fields: List[str] = field(default_factory=list)
    factor_ids: List[str] = field(default_factory=list)
    logic_ids: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if self.status not in VALID_FAMILY_STATUSES:
            raise ValueError(
                f"Invalid family status {self.status!r}; "
                f"must be one of {sorted(VALID_FAMILY_STATUSES)}"
            )
        if self.status == "provisional" and not self.family_id.startswith(
            PROVISIONAL_PREFIX
        ):
            raise ValueError(
                f"Provisional family ID must start with '{PROVISIONAL_PREFIX}', "
                f"got {self.family_id!r}"
            )
        ts = now_ts()
        if not self.created_at:
            self.created_at = ts
        if not self.updated_at:
            self.updated_at = ts

    def to_dict(self) -> Dict[str, Any]:
        return {
            "family_id": self.family_id,
            "name": self.name,
            "status": self.status,
            "description": self.description,
            "structural_signature": self.structural_signature,
            "typical_ops": self.typical_ops,
            "typical_fields": self.typical_fields,
            "factor_ids": self.factor_ids,
            "logic_ids": self.logic_ids,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FamilyRecord":
        return cls(
            family_id=data["family_id"],
            name=data["name"],
            status=data["status"],
            description=data.get("description", ""),
            structural_signature=data.get("structural_signature", ""),
            typical_ops=data.get("typical_ops", []),
            typical_fields=data.get("typical_fields", []),
            factor_ids=data.get("factor_ids", []),
            logic_ids=data.get("logic_ids", []),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


class FamilyRegistry:
    """YAML-backed CRUD store for factor families.

    Files stored at ``<families_dir>/<family_id>.yaml``.
    An index is maintained at ``<families_dir>/families_index.yaml``.
    """

    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = Path(storage_dir)
        self._families_dir = self._storage_dir / "registry" / "families"
        self._families_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _family_path(self, family_id: str) -> Path:
        return self._families_dir / f"{family_id}.yaml"

    def _index_path(self) -> Path:
        return self._families_dir / "families_index.yaml"

    def _scan_ids(self) -> List[str]:
        """Return sorted list of family IDs from files."""
        ids: List[str] = []
        for p in self._families_dir.iterdir():
            if p.suffix == ".yaml" and p.name != "families_index.yaml":
                ids.append(p.stem)
        return sorted(ids)

    def _next_id_for_prefix(self, prefix: str) -> str:
        """Auto-increment ID for a given prefix (e.g. 'FM_' or 'PF_')."""
        pattern = re.compile(rf"^{re.escape(prefix)}(\d+)$")
        max_num = 0
        for fid in self._scan_ids():
            m = pattern.match(fid)
            if m:
                max_num = max(max_num, int(m.group(1)))
        return f"{prefix}{max_num + 1:03d}"

    def _update_index(self) -> None:
        """Rebuild the families index file."""
        entries: List[Dict[str, str]] = []
        for fid in self._scan_ids():
            rec = self.get(fid)
            if rec:
                entries.append(
                    {
                        "family_id": rec.family_id,
                        "name": rec.name,
                        "status": rec.status,
                    }
                )
        index = {"families": entries, "count": len(entries)}
        dump_yaml(self._index_path(), index)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        name: str,
        status: str = "registered",
        description: str = "",
        structural_signature: str = "",
        typical_ops: Optional[List[str]] = None,
        typical_fields: Optional[List[str]] = None,
        family_id: Optional[str] = None,
    ) -> FamilyRecord:
        """Create a new family record.

        If ``family_id`` is not provided, it is auto-generated based on status.
        """
        if family_id is None:
            if status == "provisional":
                family_id = self._next_id_for_prefix("PF_")
            else:
                family_id = self._next_id_for_prefix("FM_")

        record = FamilyRecord(
            family_id=family_id,
            name=name,
            status=status,
            description=description,
            structural_signature=structural_signature,
            typical_ops=typical_ops or [],
            typical_fields=typical_fields or [],
        )

        self._save(record)
        logger.info(
            "Created family %s (%s): %s", family_id, status, name
        )
        return record

    def get(self, family_id: str) -> Optional[FamilyRecord]:
        """Load a family record by ID. Returns None if not found."""
        path = self._family_path(family_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            return None
        return FamilyRecord.from_dict(data)

    def list_families(
        self, status: Optional[str] = None
    ) -> List[FamilyRecord]:
        """Return all families, optionally filtered by status."""
        results: List[FamilyRecord] = []
        for fid in self._scan_ids():
            rec = self.get(fid)
            if rec is None:
                continue
            if status is None or rec.status == status:
                results.append(rec)
        return results

    def update(self, record: FamilyRecord) -> None:
        """Persist an updated family record (must already exist)."""
        if not self._family_path(record.family_id).exists():
            raise KeyError(
                f"Family {record.family_id!r} not found"
            )
        record.updated_at = now_ts()
        self._save(record)
        logger.debug("Updated family %s", record.family_id)

    def delete(self, family_id: str) -> bool:
        """Delete a family file. Returns True if deleted, False if not found."""
        path = self._family_path(family_id)
        if not path.exists():
            return False
        path.unlink()
        self._update_index()
        logger.info("Deleted family %s", family_id)
        return True

    def add_factor(self, family_id: str, factor_id: str) -> None:
        """Add a factor ID to a family's member list."""
        rec = self.get(family_id)
        if rec is None:
            raise KeyError(f"Family {family_id!r} not found")
        if factor_id not in rec.factor_ids:
            rec.factor_ids.append(factor_id)
            self.update(rec)

    def add_logic(self, family_id: str, logic_id: str) -> None:
        """Associate a logic ID with a family."""
        rec = self.get(family_id)
        if rec is None:
            raise KeyError(f"Family {family_id!r} not found")
        if logic_id not in rec.logic_ids:
            rec.logic_ids.append(logic_id)
            self.update(rec)

    def promote_to_registered(self, family_id: str) -> FamilyRecord:
        """Promote a provisional family to registered status.

        Generates a new FM_XXX ID and re-saves the record.
        """
        rec = self.get(family_id)
        if rec is None:
            raise KeyError(f"Family {family_id!r} not found")
        if rec.status != "provisional":
            raise ValueError(
                f"Can only promote provisional families, "
                f"got status={rec.status!r}"
            )

        # Delete old provisional file
        self.delete(family_id)

        # Create under new registered ID
        new_id = self._next_id_for_prefix("FM_")
        rec.family_id = new_id
        rec.status = "registered"
        rec.updated_at = now_ts()
        self._save(rec)
        logger.info(
            "Promoted family %s -> %s (registered)", family_id, new_id
        )
        return rec

    def _save(self, record: FamilyRecord) -> None:
        """Write family YAML and update index."""
        dump_yaml(self._family_path(record.family_id), record.to_dict())
        self._update_index()
