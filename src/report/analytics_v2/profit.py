"""Profit / quintile section extractor."""

from __future__ import annotations

from typing import Any


def extract_profit_section(candidate: dict[str, Any]) -> dict[str, Any]:
    """Return quintile returns + monotonicity + long-short summary."""
    q = candidate.get("quintile") or {}
    return {
        "quintile_returns": q.get("quintile_returns_validation") or {},
        "monotonicity": q.get("monotonicity_validation"),
        "long_short_mean": q.get("long_short_mean_validation"),
        "long_short_n_days": q.get("long_short_n_days"),
    }
