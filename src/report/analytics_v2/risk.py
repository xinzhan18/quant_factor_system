"""Risk (Barra) section extractor."""

from __future__ import annotations

from typing import Any


def extract_risk_section(candidate: dict[str, Any]) -> dict[str, Any]:
    """Return the Barra analysis block."""
    b = candidate.get("barra") or {}
    return {
        "style_exposures": b.get("style_exposures") or {},
        "style_r_squared": b.get("style_r_squared"),
        "barra_residual_ic": b.get("barra_residual_ic"),
        "barra_residual_icir": b.get("barra_residual_icir"),
        "alpha_survival_ratio": b.get("alpha_survival_ratio"),
        "dominant_style_exposure": b.get("dominant_style_exposure"),
        "style_crowding_risk": b.get("style_crowding_risk"),
    }
