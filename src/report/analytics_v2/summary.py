"""One-line factor summary — for report top-of-page."""

from __future__ import annotations

from typing import Any


def build_summary(candidate: dict[str, Any], factor_id: str) -> dict[str, Any]:
    """Return a compact dict suitable for a top-of-page summary card."""
    es = candidate.get("effect_strength") or {}
    val = es.get("validation") or {}
    q = candidate.get("quintile") or {}
    barra = candidate.get("barra") or {}
    red = candidate.get("redundancy") or {}

    return {
        "factor_id": factor_id,
        "expression": candidate.get("expression"),
        "source_type": candidate.get("source_type", "dsl"),
        "ic_mean": val.get("ic_mean"),
        "ic_ir": val.get("ic_ir"),
        "monotonicity": q.get("monotonicity_validation"),
        "long_short_mean": q.get("long_short_mean_validation"),
        "alpha_survival": barra.get("alpha_survival_ratio"),
        "style_r_squared": barra.get("style_r_squared"),
        "max_lib_corr": red.get("max_lib_corr"),
        "nearest_factor": red.get("nearest_factor_id"),
    }
