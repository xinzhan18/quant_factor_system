"""Summaries of factor-generation logic for Phase5 and Phase1 menus."""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml


def build_generation_logic_summary(paths: StoragePaths) -> dict[str, Any]:
    """Scan admitted factor YAML files and summarize generation logic usage."""
    backend_counts: Counter[str] = Counter()
    template_counts: Counter[str] = Counter()
    primitive_counts: Counter[str] = Counter()
    primitive_to_factors: dict[str, list[str]] = defaultdict(list)
    template_to_factors: dict[str, list[str]] = defaultdict(list)

    for path in sorted(paths.factors_dir.glob("F*.yaml")):
        record = load_yaml(path) or {}
        if record.get("status", "active") != "active":
            continue
        fid = str(record.get("factor_id") or path.stem)
        backend = _backend(record)
        backend_counts[backend] += 1

        template = _template(record)
        if template:
            template_counts[template] += 1
            template_to_factors[template].append(fid)

        for primitive in record.get("primitive_dependencies") or []:
            primitive = str(primitive)
            primitive_counts[primitive] += 1
            primitive_to_factors[primitive].append(fid)

    return {
        "backend_counts": dict(sorted(backend_counts.items())),
        "daily_template_counts": dict(sorted(template_counts.items())),
        "primitive_usage_counts": dict(sorted(primitive_counts.items())),
        "template_to_factors": {
            k: sorted(v) for k, v in sorted(template_to_factors.items())
        },
        "primitive_to_factors": {
            k: sorted(v) for k, v in sorted(primitive_to_factors.items())
        },
    }


def _backend(record: dict[str, Any]) -> str:
    return str(
        (record.get("backend_provenance") or {}).get("backend")
        or ((record.get("factor_ir") or {}).get("factor_logic") or {}).get("backend")
        or record.get("source_type")
        or "unknown"
    )


def _template(record: dict[str, Any]) -> str | None:
    template = (
        record.get("daily_template")
        or ((record.get("factor_ir") or {}).get("factor_logic") or {}).get("template")
        or ((record.get("backend_provenance") or {}).get("factor_logic") or {}).get("template")
    )
    return str(template) if template else None
