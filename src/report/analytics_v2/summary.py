"""One-line factor summary — for report top-of-page.

Consumes ``result.yaml`` schema v3 paths directly (no recomputation).
"""

from __future__ import annotations

from typing import Any


def build_summary(candidate: dict[str, Any], factor_id: str) -> dict[str, Any]:
    """Return a compact dict suitable for a top-of-page summary card."""
    ic = candidate.get("ic") or {}
    val = ic.get("validation") or {}
    q_val = (candidate.get("quintile") or {}).get("validation") or {}
    barra = candidate.get("barra") or {}
    uq = candidate.get("uniqueness") or {}

    return {
        "factor_id": factor_id,
        "expression": candidate.get("expression"),
        "source_type": candidate.get("source_type", "dsl"),
        "ic_mean": val.get("ic_mean"),
        "ic_ir": val.get("ic_ir"),
        "monotonicity": q_val.get("monotonicity"),
        "long_short_mean": q_val.get("ls_mean"),
        "alpha_survival": barra.get("alpha_survival_ratio"),
        "style_r_squared": barra.get("style_r_squared"),
        "max_lib_corr": uq.get("max_lib_corr"),
        "nearest_factor": uq.get("nearest_factor_id"),
    }
