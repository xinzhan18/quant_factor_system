"""Market logic library — CRUD for logic YAML files in storage/logic/."""

from __future__ import annotations

import logging
import re
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

logger = logging.getLogger(__name__)

_VALID_STATUSES = {"active", "exhausted", "dead", "archived"}


class MarketLogicLibrary:
    """YAML-based library for market logic hypotheses.

    Each logic is stored as an individual YAML file under *logic_dir*
    (e.g. ``storage/logic/L001.yaml``).  A taxonomy index is expected at
    ``logic_dir/taxonomy.yaml`` but is not required for operation.
    """

    def __init__(self, logic_dir: str) -> None:
        self._dir = Path(logic_dir)
        self._dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _logic_path(self, logic_id: str) -> Path:
        return self._dir / f"{logic_id}.yaml"

    def _scan_ids(self) -> List[str]:
        """Return sorted list of existing logic IDs (e.g. ['L001', 'L002'])."""
        pattern = re.compile(r"^L(\d+)\.yaml$")
        ids: List[str] = []
        for p in self._dir.iterdir():
            m = pattern.match(p.name)
            if m:
                ids.append(p.stem)
        return sorted(ids)

    def _next_id(self) -> str:
        existing = self._scan_ids()
        if not existing:
            return "L001"
        nums = [int(lid[1:]) for lid in existing]
        return f"L{max(nums) + 1:03d}"

    def _read(self, logic_id: str) -> Optional[Dict[str, Any]]:
        path = self._logic_path(logic_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def _write(self, data: Dict[str, Any]) -> None:
        logic_id = data["id"]
        path = self._logic_path(logic_id)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(
        self,
        name: str,
        category: str,
        hypothesis: Dict[str, Any],
        constraints: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a new logic entry and persist it.  Returns the full record."""
        logic_id = self._next_id()
        record: Dict[str, Any] = {
            "id": logic_id,
            "name": name,
            "status": "active",
            "category": category,
            "created": str(date.today()),
            "hypothesis": hypothesis,
            "constraints": constraints or {},
            "stats": {
                "factors_generated": 0,
                "factors_admitted": 0,
                "best_ic": 0.0,
                "rounds_without_admit": 0,
            },
        }
        self._write(record)
        logger.info("Created logic %s: %s", logic_id, name)
        return record

    def get(self, logic_id: str) -> Optional[Dict[str, Any]]:
        """Return the logic record for *logic_id*, or None if not found."""
        return self._read(logic_id)

    def list_logics(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return all logic records, optionally filtered by *status*."""
        records: List[Dict[str, Any]] = []
        for lid in self._scan_ids():
            record = self._read(lid)
            if record is None:
                continue
            if status is None or record.get("status") == status:
                records.append(record)
        return records

    def update_stats(self, logic_id: str, **kwargs: Any) -> None:
        """Merge *kwargs* into the ``stats`` sub-dict of the logic record.

        Only keys that already exist in the stats block are updated; unknown
        keys are silently added.
        """
        record = self._read(logic_id)
        if record is None:
            raise KeyError(f"Logic {logic_id!r} not found")
        stats = record.setdefault("stats", {})
        stats.update(kwargs)
        self._write(record)
        logger.debug("Updated stats for %s: %s", logic_id, kwargs)

    def update_status(self, logic_id: str, status: str) -> None:
        """Transition *logic_id* to *status*."""
        if status not in _VALID_STATUSES:
            raise ValueError(f"Invalid status {status!r}; must be one of {_VALID_STATUSES}")
        record = self._read(logic_id)
        if record is None:
            raise KeyError(f"Logic {logic_id!r} not found")
        record["status"] = status
        self._write(record)
        logger.info("Updated status of %s to %s", logic_id, status)

    def coverage_map(self) -> Dict[str, int]:
        """Return a dict mapping category → count of *active* logics."""
        counts: Dict[str, int] = {}
        for record in self.list_logics(status="active"):
            cat = record.get("category", "unknown")
            counts[cat] = counts.get(cat, 0) + 1
        return counts
