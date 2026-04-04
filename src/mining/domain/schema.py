"""Canonical factor record schema — single metadata truth definition.

All factor records in the system (library YAML, DB, evaluator output)
must conform to this schema. The normalize_metrics() function handles
legacy alias resolution.

SCOPE: normalize_metrics() applies ONLY to factor record metrics
(library/registry storage). It must NOT be applied to intermediate
evaluator/analyzer result dicts, which use their own naming.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

VALID_STATUSES = {"active", "legacy", "retired"}
VALID_SOURCES = {"dsl", "python"}

# Maps legacy/variant metric keys -> canonical key.
# When both alias and canonical are present, canonical wins.
METRICS_ALIASES: Dict[str, str] = {
    "ic_mean_is": "ic_mean",
    "ic_ir_is": "ic_ir",
    "max_lib_corr": "max_corr",
    "monotonicity": "monotonicity_is",
}


def normalize_metrics(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Resolve legacy metric aliases to canonical names for library storage.

    SCOPE: Only for factor record metrics persisted in registry YAML.
    Do NOT apply to intermediate evaluator/analyzer result dicts.

    Rules:
    - If canonical key already present, keep it (alias is dropped).
    - If only alias present, rename to canonical.
    - Unknown keys pass through unchanged.
    """
    result = {}
    for k, v in raw.items():
        canonical = METRICS_ALIASES.get(k)
        if canonical:
            if canonical not in raw and canonical not in result:
                result[canonical] = v
        else:
            result[k] = v
    return result


@dataclass
class FactorRecord:
    """Canonical factor record — the single metadata truth definition.

    Not persisted directly (we use YAML dicts). Serves as schema contract:
    validation, defaults, and long_leg inference.

    Defaults are legacy/v1 for migration safety. Use factory methods:
    - FactorRecord.for_new_admission() -> active/v2
    - FactorRecord.for_migration()     -> legacy/v1
    """
    # Required
    id: str
    name: str
    expression: Optional[str]  # None for Python factors
    category: str
    batch: str

    # Defaults — "legacy" and "v1" for migration safety
    source: str = "dsl"
    status: str = "legacy"
    evaluation_version: str = "v1"
    admitted_at: Optional[str] = None
    logic_id: Optional[str] = None
    lineage: Optional[Dict[str, Any]] = None
    code_path: Optional[str] = None
    replaces: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    long_leg: Optional[str] = None

    def __post_init__(self):
        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status {self.status!r}, must be one of {VALID_STATUSES}"
            )
        if self.source not in VALID_SOURCES:
            raise ValueError(
                f"Invalid source {self.source!r}, must be one of {VALID_SOURCES}"
            )
        if self.metrics:
            self.metrics = normalize_metrics(self.metrics)
        if self.long_leg is None and self.metrics:
            ic = self.metrics.get("ic_mean")
            if ic is not None:
                self.long_leg = "high" if ic >= 0 else "low"

    @classmethod
    def for_new_admission(cls, **kwargs) -> "FactorRecord":
        """Factory for new pipeline admissions (active/v2)."""
        kwargs.setdefault("status", "active")
        kwargs.setdefault("evaluation_version", "v2")
        return cls(**kwargs)

    @classmethod
    def for_migration(cls, **kwargs) -> "FactorRecord":
        """Factory for migrating legacy records (legacy/v1)."""
        kwargs.setdefault("status", "legacy")
        kwargs.setdefault("evaluation_version", "v1")
        return cls(**kwargs)

    def to_detail_dict(self) -> Dict[str, Any]:
        """Export as dict for detail YAML (factor_XXX.yaml)."""
        d: Dict[str, Any] = {
            "id": self.id,
            "name": self.name,
            "expression": self.expression,
            "source": self.source,
            "status": self.status,
            "evaluation_version": self.evaluation_version,
            "category": self.category,
            "batch": self.batch,
            "admitted_at": self.admitted_at,
            "long_leg": self.long_leg,
            "metrics": self.metrics,
        }
        if self.logic_id:
            d["logic_id"] = self.logic_id
        if self.lineage:
            d["lineage"] = self.lineage
        if self.code_path:
            d["code_path"] = self.code_path
        if self.replaces:
            d["replaces"] = self.replaces
        return d

    def to_index_dict(self) -> Dict[str, Any]:
        """Export as dict for library index (library.yaml factors list)."""
        return {
            "id": self.id,
            "name": self.name,
            "expression": self.expression,
            "source": self.source,
            "category": self.category,
            "status": self.status,
            "ic_mean": self.metrics.get("ic_mean"),
            "long_leg": self.long_leg,
            "evaluation_version": self.evaluation_version,
        }
