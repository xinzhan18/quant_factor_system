"""Factor library management."""

from __future__ import annotations

import logging
import shutil
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from .config import MiningConfig
from .schema import FactorRecord

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

    def _publish(self, factor_id: str, factor_dict: Dict[str, Any]) -> None:
        """Publish factor to DB. Best-effort — failure is logged, not raised."""
        factor_values_is = factor_dict.get("_factor_values")
        factor_values_oos = factor_dict.get("_factor_values_oos")
        if factor_values_is is None:
            factor_values_is, factor_values_oos = self._load_values_cache(
                factor_dict.get("name"))
        if factor_values_is is not None:
            try:
                from .publisher import FactorPublisher
                with FactorPublisher(self._config) as publisher:
                    publisher.publish(
                        factor_id=factor_id,
                        factor_dict=factor_dict,
                        factor_values_is=factor_values_is,
                        factor_values_oos=factor_values_oos,
                    )
            except Exception as e:
                logger.warning("Failed to publish factor %s: %s", factor_id, e)
        else:
            logger.warning("No factor values for %s — skipping DB publish", factor_id)

    def admit(self, factor: Dict[str, Any]) -> str:
        """Admit a new factor to the library. Returns assigned ID."""
        index = self._read_index()
        factor_id = self._next_id(index)
        source = factor.get("source", "dsl")
        name = factor.get("name", f"factor_{factor_id}")

        code_path: Optional[str] = None
        if source == "python":
            code_path = self._persist_python_factor(factor_id, factor)

        record = FactorRecord.for_new_admission(
            id=factor_id,
            name=name,
            expression=factor.get("expression") if source == "dsl" else None,
            source=source,
            category=factor.get("category", "other"),
            batch=factor.get("batch", "unknown"),
            admitted_at=str(date.today()),
            logic_id=factor.get("logic_id"),
            lineage=factor.get("lineage"),
            code_path=code_path,
            metrics=factor.get("metrics", {}),
        )

        detail_path = self._factors_dir / f"factor_{factor_id}.yaml"
        with open(detail_path, "w", encoding="utf-8") as f:
            yaml.dump(record.to_detail_dict(), f,
                      default_flow_style=False, allow_unicode=True, sort_keys=False)
        index.setdefault("factors", []).append(record.to_index_dict())
        self._write_index(index)
        logger.info("Admitted factor %s: %s", factor_id, record.name)

        self._publish(factor_id, factor)
        return factor_id

    def replace(self, old_id: str, new_factor: Dict[str, Any]) -> str:
        """Replace an existing factor. Keeps the same ID.

        Archives old detail YAML to factors/history/ before overwrite.
        New record: status=active, evaluation_version=v2, replaces=old_id.
        """
        # Archive old detail YAML before overwrite
        old_detail = self._factors_dir / f"factor_{old_id}.yaml"
        if old_detail.exists():
            history_dir = self._factors_dir / "history"
            history_dir.mkdir(exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"factor_{old_id}__replaced_{ts}.yaml"
            shutil.copy2(str(old_detail), str(history_dir / archive_name))
            logger.info("Archived %s → history/%s", old_detail.name, archive_name)

        index = self._read_index()
        index["factors"] = [f for f in index.get("factors", []) if f["id"] != old_id]

        source = new_factor.get("source", "dsl")
        code_path: Optional[str] = None
        if source == "python":
            code_path = self._persist_python_factor(old_id, new_factor)

        record = FactorRecord.for_new_admission(
            id=old_id,
            name=new_factor.get("name", f"factor_{old_id}"),
            expression=new_factor.get("expression") if source == "dsl" else None,
            source=source,
            category=new_factor.get("category", "other"),
            batch=new_factor.get("batch", "unknown"),
            admitted_at=str(date.today()),
            logic_id=new_factor.get("logic_id"),
            lineage=new_factor.get("lineage"),
            code_path=code_path,
            replaces=old_id,
            metrics=new_factor.get("metrics", {}),
        )

        detail_path = self._factors_dir / f"factor_{old_id}.yaml"
        with open(detail_path, "w", encoding="utf-8") as f:
            yaml.dump(record.to_detail_dict(), f,
                      default_flow_style=False, allow_unicode=True, sort_keys=False)
        index["factors"].append(record.to_index_dict())
        self._write_index(index)
        logger.info("Replaced factor %s with %s", old_id, record.name)

        self._publish(old_id, new_factor)
        return old_id

    def retire(self, factor_id: str) -> None:
        """Mark a factor as retired in both detail and index."""
        self._set_status(factor_id, "retired")

    def _set_status(self, factor_id: str, status: str) -> None:
        """Update factor status in detail YAML and index."""
        detail_path = self._factors_dir / f"factor_{factor_id}.yaml"
        if not detail_path.exists():
            raise FileNotFoundError(f"Factor {factor_id} not found")
        with open(detail_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        data["status"] = status
        with open(detail_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        index = self._read_index()
        for entry in index.get("factors", []):
            if str(entry["id"]) == str(factor_id):
                entry["status"] = status
                break
        self._write_index(index)
        logger.info("Factor %s status → %s", factor_id, status)

    def _load_values_cache(self, factor_name: str):
        """Try to load factor values from pickle cache (saved by evaluate step)."""
        import pickle
        candidates_dir = Path(self._config.candidates_dir)
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

    def list_factors(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """List factors, optionally filtered by status."""
        factors = self._read_index().get("factors", [])
        if status:
            factors = [f for f in factors if f.get("status") == status]
        return factors

    def load_factor(self, factor_id: str) -> Dict[str, Any]:
        path = self._factors_dir / f"factor_{factor_id}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Factor {factor_id} not found")
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def get_all_expressions(self) -> Dict[str, str]:
        """Return expressions for ALL factors (all statuses participate in corr blocking)."""
        return {f["id"]: f["expression"] for f in self._read_index().get("factors", [])}

    def get_factor_ic(self, factor_id: str) -> Optional[float]:
        try:
            detail = self.load_factor(factor_id)
            m = detail.get("metrics", {})
            return m.get("ic_mean")
        except FileNotFoundError:
            return None

    @property
    def size(self) -> int:
        return len(self.list_factors())
