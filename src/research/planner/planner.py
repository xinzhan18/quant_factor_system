"""Execution planner for normalized Factor IR manifests."""

from __future__ import annotations

import re
from typing import Any

from data.primitive import PrimitiveCache, PrimitiveRegistry, PrimitiveSpec
from research.compute.primitive_bridge import load_manifest_primitive_specs
from research.ir import normalize_manifest
from research.planner.execution_plan import (
    DailyPythonTask,
    ExecutionPlan,
    FactorTask,
    PrimitiveTask,
)
from research.storage.paths import StoragePaths

_FIELD_PATTERN = re.compile(r"\$[a-zA-Z_][a-zA-Z0-9_]*")


class PlannerError(ValueError):
    """Raised when an execution plan has blocking errors."""


class ExecutionPlanner:
    """Build an execution plan from a manifest.

    The planner is intentionally non-computational: it validates and groups
    tasks, while existing materializers/backends still perform the work.
    """

    def __init__(
        self,
        manifest: dict[str, Any],
        paths: StoragePaths,
        config: dict[str, Any],
        *,
        start: str,
        end: str,
    ) -> None:
        self.manifest = manifest
        self.paths = paths
        self.config = config
        self.start = start
        self.end = end

    def build(self, *, raise_on_error: bool = True) -> ExecutionPlan:
        normalized = normalize_manifest(self.manifest)
        errors: list[str] = []
        specs = self._load_specs(errors)

        qlib_tasks: list[FactorTask] = []
        python_tasks: list[FactorTask] = []
        daily_python_tasks: list[DailyPythonTask] = []

        declared_deps: list[str] = []
        for cand in normalized.get("candidates", []) or []:
            deps = _dedupe_strings(cand.get("primitive_dependencies") or [])
            for dep in deps:
                if dep not in declared_deps:
                    declared_deps.append(dep)

            backend = ((cand.get("factor_logic") or {}).get("backend")) or (
                "qlib" if cand.get("source_type") == "dsl" else cand.get("source_type")
            )
            cid = str(cand.get("candidate_id") or "")
            if backend == "qlib":
                expression = cand.get("expression")
                self._check_primitive_references(cid, expression, deps, specs, errors)
                qlib_tasks.append(
                    FactorTask(
                        candidate_id=cid,
                        backend="qlib",
                        source_type="dsl",
                        expression=expression,
                        primitive_dependencies=deps,
                    )
                )
            elif backend == "python":
                python_tasks.append(
                    FactorTask(
                        candidate_id=cid,
                        backend="python",
                        source_type="python",
                        path=cand.get("path"),
                        primitive_dependencies=deps,
                    )
                )
            elif backend == "daily_python":
                logic = cand.get("factor_logic") or {}
                daily_python_tasks.append(
                    DailyPythonTask(
                        candidate_id=cid,
                        template=str(logic.get("template") or ""),
                        params=dict(logic.get("params") or {}),
                        primitive_dependencies=deps,
                    )
                )
            else:
                errors.append(f"{cid}:unsupported_backend:{backend}")

        primitive_tasks = self._build_primitive_tasks(declared_deps, specs, errors)
        plan = ExecutionPlan(
            normalized_manifest=normalized,
            primitive_tasks=primitive_tasks,
            qlib_tasks=qlib_tasks,
            python_tasks=python_tasks,
            daily_python_tasks=daily_python_tasks,
            errors=errors,
        )
        if raise_on_error and plan.has_errors:
            raise PlannerError("; ".join(plan.errors))
        return plan

    def _load_specs(self, errors: list[str]) -> dict[str, PrimitiveSpec]:
        registry = PrimitiveRegistry(self.paths.minute_primitive_registry_dir)
        try:
            return load_manifest_primitive_specs(self.manifest, registry)
        except Exception as exc:  # noqa: BLE001 - surfaced as planner error
            errors.append(f"primitive_registry_error:{type(exc).__name__}:{exc}")
            return {}

    def _build_primitive_tasks(
        self,
        feature_ids: list[str],
        specs: dict[str, PrimitiveSpec],
        errors: list[str],
    ) -> list[PrimitiveTask]:
        if not feature_ids:
            return []
        cache = PrimitiveCache(self.paths.minute_primitive_store_dir)
        tasks: list[PrimitiveTask] = []
        for fid in feature_ids:
            spec = specs.get(fid)
            if spec is None:
                errors.append(f"primitive_missing_spec:{fid}")
                continue
            hit = cache.get(spec, start=self.start, end=self.end)
            status = "cache_hit" if hit is not None else "cache_miss"
            if status == "cache_miss" and not self._has_minute_loader_config():
                errors.append(f"primitive_cache_miss_without_loader:{fid}")
            tasks.append(
                PrimitiveTask(
                    feature_id=fid,
                    backend=f"{spec.source_type}_materializer",
                    source_type=spec.source_type,
                    status=status,
                    spec_hash=spec.spec_hash,
                    available_time=spec.time_semantics.get("available_time"),
                )
            )
        return tasks

    def _check_primitive_references(
        self,
        candidate_id: str,
        expression: str | None,
        declared_deps: list[str],
        specs: dict[str, PrimitiveSpec],
        errors: list[str],
    ) -> None:
        if not expression or not specs:
            return
        fields = {field[1:] for field in _FIELD_PATTERN.findall(expression)}
        referenced_primitives = sorted(fields & set(specs.keys()))
        missing = [fid for fid in referenced_primitives if fid not in declared_deps]
        for fid in missing:
            errors.append(
                f"{candidate_id}:primitive_referenced_but_not_declared:{fid}"
            )

    def _has_minute_loader_config(self) -> bool:
        primitive_cfg = self.config.get("primitive") or {}
        return bool(
            self.config.get("primitive_minute_parquet")
            or primitive_cfg.get("minute_parquet")
        )


def _dedupe_strings(values: list[Any]) -> list[str]:
    out: list[str] = []
    for value in values:
        if value is None:
            continue
        text = str(value)
        if text and text not in out:
            out.append(text)
    return out
