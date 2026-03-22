"""Factor library management."""

from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .config import MiningConfig

logger = logging.getLogger(__name__)


class FactorLibrary:
    """YAML-based factor library for admitted factors."""

    def __init__(self, config: MiningConfig):
        self._dir = Path(config.library_dir)
        self._factors_dir = self._dir / "factors"
        self._factors_dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._dir / "library.yaml"

    def _read_index(self) -> Dict[str, Any]:
        if not self._index_path.exists():
            return {"thresholds": {}, "factors": []}
        with open(self._index_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"thresholds": {}, "factors": []}

    def _write_index(self, data: Dict[str, Any]) -> None:
        with open(self._index_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    def _next_id(self, index: Dict[str, Any]) -> str:
        factors = index.get("factors", [])
        if not factors:
            return "001"
        max_id = max(int(f["id"]) for f in factors)
        return f"{max_id + 1:03d}"

    def admit(self, factor: Dict[str, Any]) -> str:
        """Admit a new factor to the library. Returns assigned ID."""
        index = self._read_index()
        factor_id = self._next_id(index)
        record = {
            "id": factor_id,
            "name": factor.get("name", f"factor_{factor_id}"),
            "expression": factor["expression"],
            "category": factor.get("category", "other"),
            "batch": factor.get("batch", "unknown"),
            "admitted_at": str(date.today()),
            "metrics": factor.get("metrics", {}),
        }
        detail_path = self._factors_dir / f"factor_{factor_id}.yaml"
        with open(detail_path, "w", encoding="utf-8") as f:
            yaml.dump(record, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        index.setdefault("factors", []).append({
            "id": factor_id, "name": record["name"], "expression": record["expression"],
            "category": record["category"], "ic_mean": record["metrics"].get("ic_mean"),
        })
        self._write_index(index)
        logger.info("Admitted factor %s: %s", factor_id, record["name"])
        return factor_id

    def replace(self, old_id: str, new_factor: Dict[str, Any]) -> str:
        """Replace an existing factor. Keeps the same ID."""
        index = self._read_index()
        index["factors"] = [f for f in index.get("factors", []) if f["id"] != old_id]
        record = {
            "id": old_id,
            "name": new_factor.get("name", f"factor_{old_id}"),
            "expression": new_factor["expression"],
            "category": new_factor.get("category", "other"),
            "batch": new_factor.get("batch", "unknown"),
            "admitted_at": str(date.today()),
            "metrics": new_factor.get("metrics", {}),
            "replaces": old_id,
        }
        detail_path = self._factors_dir / f"factor_{old_id}.yaml"
        with open(detail_path, "w", encoding="utf-8") as f:
            yaml.dump(record, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        index["factors"].append({
            "id": old_id, "name": record["name"], "expression": record["expression"],
            "category": record["category"], "ic_mean": record["metrics"].get("ic_mean"),
        })
        self._write_index(index)
        logger.info("Replaced factor %s with %s", old_id, record["name"])
        return old_id

    def list_factors(self) -> List[Dict[str, Any]]:
        return self._read_index().get("factors", [])

    def load_factor(self, factor_id: str) -> Dict[str, Any]:
        path = self._factors_dir / f"factor_{factor_id}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Factor {factor_id} not found")
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_all_expressions(self) -> Dict[str, str]:
        return {f["id"]: f["expression"] for f in self._read_index().get("factors", [])}

    def get_factor_ic(self, factor_id: str) -> Optional[float]:
        try:
            detail = self.load_factor(factor_id)
            return detail.get("metrics", {}).get("ic_mean")
        except FileNotFoundError:
            return None

    @property
    def size(self) -> int:
        return len(self.list_factors())
