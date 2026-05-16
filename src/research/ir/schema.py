"""Factor IR v1 schema.

The IR records research intent in a backend-neutral shape.  It is deliberately
small in P1: enough to normalize legacy manifest candidates and to make backend
choice explicit without changing Phase2 metric computation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class DataLogic:
    """Data dependencies for one candidate."""

    primitive_dependencies: list[str] = field(default_factory=list)
    daily_fields: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "DataLogic":
        data = data or {}
        return cls(
            primitive_dependencies=_dedupe_strings(
                data.get("primitive_dependencies") or data.get("primitives") or []
            ),
            daily_fields=_dedupe_strings(data.get("daily_fields") or []),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.primitive_dependencies:
            out["primitive_dependencies"] = list(self.primitive_dependencies)
        if self.daily_fields:
            out["daily_fields"] = list(self.daily_fields)
        return out


@dataclass(frozen=True)
class FactorLogic:
    """Executable daily factor logic."""

    backend: str
    expression: str | None = None
    template: str | None = None
    params: dict[str, Any] = field(default_factory=dict)
    path: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "FactorLogic":
        data = data or {}
        backend = str(data.get("backend") or "qlib")
        return cls(
            backend=backend,
            expression=data.get("expression"),
            template=data.get("template"),
            params=dict(data.get("params") or {}),
            path=data.get("path") or data.get("python_path"),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {"backend": self.backend}
        if self.expression is not None:
            out["expression"] = self.expression
        if self.template is not None:
            out["template"] = self.template
        if self.params:
            out["params"] = dict(self.params)
        if self.path is not None:
            out["path"] = self.path
        return out


@dataclass(frozen=True)
class LabelSpec:
    """Prediction target timing metadata."""

    horizon: int | None = None
    decision_time: str | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "LabelSpec":
        data = data or {}
        horizon = data.get("horizon")
        return cls(
            horizon=int(horizon) if horizon is not None else None,
            decision_time=data.get("decision_time"),
        )

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {}
        if self.horizon is not None:
            out["horizon"] = int(self.horizon)
        if self.decision_time is not None:
            out["decision_time"] = self.decision_time
        return out


@dataclass(frozen=True)
class FactorIR:
    """Normalized candidate definition used by planner/backends."""

    candidate_id: str
    ir_version: str
    data_logic: DataLogic
    factor_logic: FactorLogic
    hypothesis: str | None = None
    expected_sign: str | None = None
    label: LabelSpec = field(default_factory=LabelSpec)
    legacy_source_type: str | None = None
    canonical: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "candidate_id": self.candidate_id,
            "ir_version": self.ir_version,
            "data_logic": self.data_logic.to_dict(),
            "factor_logic": self.factor_logic.to_dict(),
        }
        if self.hypothesis:
            out["hypothesis"] = self.hypothesis
        if self.expected_sign:
            out["expected_sign"] = self.expected_sign
        label = self.label.to_dict()
        if label:
            out["label"] = label
        if self.canonical:
            out["canonical"] = self.canonical
        if self.metadata:
            out["metadata"] = dict(self.metadata)
        return out


def _dedupe_strings(values: list[Any]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value)
        if text and text not in out:
            out.append(text)
    return out
