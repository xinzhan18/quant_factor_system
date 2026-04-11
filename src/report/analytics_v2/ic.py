"""IC section extractor — pull IC fields from a result.yaml candidate entry."""

from __future__ import annotations

from typing import Any


def extract_ic_section(candidate: dict[str, Any]) -> dict[str, Any]:
    """Return the IC metrics block for a report."""
    es = candidate.get("effect_strength") or {}
    return {
        "train": es.get("train") or {},
        "validation": es.get("validation") or {},
    }
