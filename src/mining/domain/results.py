"""Batch evaluation result types and serialization helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


def _clean_factor_dict(c: Dict[str, Any]) -> Dict[str, Any]:
    """Extract only serializable fields from a factor dict (whitelist approach)."""
    ALLOWED_KEYS = {
        "name", "expression", "category", "rationale", "batch",
        "stage1", "stage2", "stage3", "full_ic", "report_card",
        "validation_error", "reject_reason",
        # Python factor / logic-guided evolution keys
        "source", "code", "code_path", "type", "params", "param_space",
        "logic_id", "lineage",
    }
    return {k: v for k, v in c.items() if k in ALLOWED_KEYS}


@dataclass
class BatchResult:
    """Result of a batch evaluation.

    ``screened`` contains factors that passed Stage 1-2 hard filters and have
    a full 6-dimension FactorReportCard.  They are *not* automatically admitted
    — the LLM in the Ralph Loop skill reviews them and decides.

    ``admitted`` is an alias kept for backward compatibility (same list).
    """
    screened: List[Dict[str, Any]] = field(default_factory=list)
    rejected: List[Dict[str, Any]] = field(default_factory=list)
    replacements: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def admitted(self) -> List[Dict[str, Any]]:
        """Backward-compatible alias for screened."""
        return self.screened

    def to_dict(self) -> Dict[str, Any]:
        """Return a clean, serializable dict for YAML/JSON export."""
        clean_replacements = []
        for r in self.replacements:
            if isinstance(r, dict) and "new_factor" in r:
                clean_replacements.append({
                    "new_factor": _clean_factor_dict(r["new_factor"]),
                    "replaces": r.get("replaces"),
                })
            else:
                clean_replacements.append(_clean_factor_dict(r))
        return {
            "screened": [_clean_factor_dict(c) for c in self.screened],
            "rejected": [_clean_factor_dict(c) for c in self.rejected],
            "replacements": clean_replacements,
        }
