"""Profit / quintile section extractor (schema v3)."""

from __future__ import annotations

from typing import Any


def extract_profit_section(candidate: dict[str, Any]) -> dict[str, Any]:
    """Return quintile returns + monotonicity + long-short summary."""
    q_val = (candidate.get("quintile") or {}).get("validation") or {}
    ls_val = ((candidate.get("quintile") or {}).get("ls_stats") or {}).get("validation") or {}
    return {
        "quintile_returns": {
            k: q_val[k] for k in ("q1", "q2", "q3", "q4", "q5") if k in q_val
        },
        "monotonicity": q_val.get("monotonicity"),
        "long_short_mean": q_val.get("ls_mean"),
        "long_short_n_days": q_val.get("n_days"),
        "long_short_sharpe": ls_val.get("sharpe"),
        "long_short_tstat": ls_val.get("tstat"),
    }
