"""Execution plan dataclasses."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PrimitiveTask:
    """A daily primitive dependency required before daily factor execution."""

    feature_id: str
    backend: str
    source_type: str
    status: str
    spec_hash: str | None = None
    available_time: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "feature_id": self.feature_id,
            "backend": self.backend,
            "source_type": self.source_type,
            "status": self.status,
            "spec_hash": self.spec_hash,
            "available_time": self.available_time,
        }


@dataclass(frozen=True)
class FactorTask:
    """A candidate task executable by Qlib or legacy Python backend."""

    candidate_id: str
    backend: str
    source_type: str
    expression: str | None = None
    path: str | None = None
    primitive_dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "candidate_id": self.candidate_id,
            "backend": self.backend,
            "source_type": self.source_type,
            "primitive_dependencies": list(self.primitive_dependencies),
        }
        if self.expression is not None:
            out["expression"] = self.expression
        if self.path is not None:
            out["path"] = self.path
        return out


@dataclass(frozen=True)
class DailyPythonTask:
    """A candidate task for the planned DailyPythonBackend."""

    candidate_id: str
    template: str
    params: dict[str, Any] = field(default_factory=dict)
    primitive_dependencies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "backend": "daily_python",
            "template": self.template,
            "params": dict(self.params),
            "primitive_dependencies": list(self.primitive_dependencies),
        }


@dataclass(frozen=True)
class ExecutionPlan:
    """Planner output consumed by Pre-Phase2 and daily backends."""

    normalized_manifest: dict[str, Any]
    primitive_tasks: list[PrimitiveTask] = field(default_factory=list)
    qlib_tasks: list[FactorTask] = field(default_factory=list)
    python_tasks: list[FactorTask] = field(default_factory=list)
    daily_python_tasks: list[DailyPythonTask] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def to_dict(self) -> dict[str, Any]:
        return {
            "primitive_tasks": [task.to_dict() for task in self.primitive_tasks],
            "qlib_tasks": [task.to_dict() for task in self.qlib_tasks],
            "python_tasks": [task.to_dict() for task in self.python_tasks],
            "daily_python_tasks": [
                task.to_dict() for task in self.daily_python_tasks
            ],
            "errors": list(self.errors),
        }
