"""IC section extractor — schema v3.

Reads from ``candidate["ic"]`` produced by Phase 2 orchestrator.
"""

from __future__ import annotations

from typing import Any


def extract_ic_section(candidate: dict[str, Any]) -> dict[str, Any]:
    """Return the IC metrics block for a report."""
    ic = candidate.get("ic") or {}
    return {
        "train": ic.get("train") or {},
        "validation": ic.get("validation") or {},
    }
