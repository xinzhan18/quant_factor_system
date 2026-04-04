"""Candidate classification and caching policies."""

from __future__ import annotations

from typing import Any, Dict


def _candidate_cache_key(c: Dict[str, Any]) -> str:
    """Derive a stable cache key for a candidate (DSL expression or Python code hash)."""
    if c.get("expression"):
        return c["expression"]
    # Python factors: use first 100 chars of code as cache key
    return c.get("code", "")[:100]


def _is_python_candidate(c: Dict[str, Any]) -> bool:
    """Return True if the candidate represents a Python factor (not a DSL expression)."""
    return c.get("source") == "python" or c.get("type") == "python"
