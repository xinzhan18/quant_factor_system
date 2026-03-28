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
        self._config = config
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

    def _persist_python_factor(self, factor_id: str, factor: Dict[str, Any]) -> str:
        """Write the Python factor .py file and return the path."""
        python_factors_dir = Path(self._config.python_factors_dir)
        python_factors_dir.mkdir(parents=True, exist_ok=True)
        name = factor.get("name", f"factor_{factor_id}")
        filename = f"F{factor_id}_{name}.py"
        file_path = python_factors_dir / filename
        code = factor.get("code", "pass")
        meta = {
            "name": name,
            "logic_id": factor.get("logic_id"),
            "params": factor.get("params", {}),
            "param_space": factor.get("param_space", {}),
            "lineage": factor.get("lineage", {}),
        }
        content = (
            f'"""Auto-generated Python factor: {name}"""\n'
            f"META = {meta!r}\n"
            f"\n"
            f"def compute(df, params, ops):\n"
        )
        for line in code.splitlines():
            content += f"    {line}\n"
        file_path.write_text(content, encoding="utf-8")
        return str(file_path)

    def admit(self, factor: Dict[str, Any]) -> str:
        """Admit a new factor to the library. Returns assigned ID."""
        index = self._read_index()
        factor_id = self._next_id(index)
        source = factor.get("source", "dsl")
        name = factor.get("name", f"factor_{factor_id}")

        # Persist Python factor .py file before building the record
        code_path: Optional[str] = None
        if source == "python":
            code_path = self._persist_python_factor(factor_id, factor)

        record = {
            "id": factor_id,
            "name": name,
            "expression": factor.get("expression") if source == "dsl" else None,
            "source": source,
            "code_path": code_path,
            "logic_id": factor.get("logic_id"),
            "lineage": factor.get("lineage"),
            "category": factor.get("category", "other"),
            "batch": factor.get("batch", "unknown"),
            "admitted_at": str(date.today()),
            "metrics": factor.get("metrics", {}),
        }
        # For DSL factors keep backward-compat: don't pollute record with None-valued new fields
        if source == "dsl":
            record = {k: v for k, v in record.items()
                      if k not in ("code_path", "logic_id", "lineage") or v is not None}

        detail_path = self._factors_dir / f"factor_{factor_id}.yaml"
        with open(detail_path, "w", encoding="utf-8") as f:
            yaml.dump(record, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        metrics = record["metrics"]
        ic_mean = metrics.get("ic_mean") or metrics.get("ic_mean_is")
        index.setdefault("factors", []).append({
            "id": factor_id,
            "name": record["name"],
            "expression": record.get("expression"),
            "category": record["category"],
            "ic_mean": ic_mean,
            "source": source,
        })
        self._write_index(index)
        logger.info("Admitted factor %s: %s", factor_id, record["name"])
        # Publish to DB — try transient values first, then pickle cache
        factor_values_is = factor.get("_factor_values")
        factor_values_oos = factor.get("_factor_values_oos")
        if factor_values_is is None:
            factor_values_is, factor_values_oos = self._load_values_cache(factor.get("name"))
        if factor_values_is is not None:
            try:
                from .publisher import FactorPublisher
                with FactorPublisher(self._config) as publisher:
                    publisher.publish(
                        factor_id=factor_id,
                        factor_dict=factor,
                        factor_values_is=factor_values_is,
                        factor_values_oos=factor_values_oos,
                    )
            except Exception as e:
                logger.warning("Failed to publish factor %s: %s", factor_id, e)
        else:
            logger.warning("No factor values for %s — skipping DB publish", factor_id)
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
        # Publish to DB — try transient values first, then pickle cache
        factor_values_is = new_factor.get("_factor_values")
        factor_values_oos = new_factor.get("_factor_values_oos")
        if factor_values_is is None:
            factor_values_is, factor_values_oos = self._load_values_cache(new_factor.get("name"))
        if factor_values_is is not None:
            try:
                from .publisher import FactorPublisher
                with FactorPublisher(self._config) as publisher:
                    publisher.publish(
                        factor_id=old_id,
                        factor_dict=new_factor,
                        factor_values_is=factor_values_is,
                        factor_values_oos=factor_values_oos,
                    )
            except Exception as e:
                logger.warning("Failed to publish factor %s: %s", old_id, e)
        else:
            logger.warning("No factor values for %s — skipping DB publish", old_id)
        return old_id

    def _load_values_cache(self, factor_name: str):
        """Try to load factor values from pickle cache (saved by evaluate step)."""
        import glob
        import pickle
        candidates_dir = Path("storage/candidates")
        for pkl in sorted(candidates_dir.glob("*_values.pkl"), reverse=True):
            try:
                with open(pkl, "rb") as f:
                    cache = pickle.load(f)
                if factor_name in cache:
                    logger.info("Loaded factor values from cache: %s", pkl)
                    return cache[factor_name]["is"], cache[factor_name]["oos"]
            except Exception:
                continue
        return None, None

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
            m = detail.get("metrics", {})
            return m.get("ic_mean") or m.get("ic_mean_is")
        except FileNotFoundError:
            return None

    @property
    def size(self) -> int:
        return len(self.list_factors())
