"""Forbidden pattern CRUD with 3-state lifecycle.

States: active -> under_review -> retired (or back to active).

Reassessment triggers (any one is sufficient):
    * 2+ batches with opposite evidence
    * definition too broad
    * original evidence proven wrong
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from research.governance._yaml_io import atomic_yaml_write, now_iso

# Valid states and allowed transitions
VALID_STATES = {"active", "under_review", "retired"}
_TRANSITIONS = {
    "active": {"reassess": "under_review", "retire": "retired"},
    "under_review": {"retire": "retired", "reactivate": "active"},
    "retired": {"reactivate": "active"},
}

REASSESSMENT_TRIGGERS = {
    "opposite_evidence",
    "definition_too_broad",
    "original_evidence_wrong",
}


class ForbiddenManager:
    """Manage the ``forbidden.yaml`` file with lifecycle transitions.

    Parameters
    ----------
    base_dir : Path
        Root storage directory.  The forbidden file lives at
        ``<base_dir>/memory/forbidden.yaml``.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = Path(base_dir)
        self._path = self._base_dir / "memory" / "forbidden.yaml"

    @property
    def path(self) -> Path:
        return self._path

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def list_patterns(self, *, state: Optional[str] = None) -> List[dict]:
        """Return all patterns, optionally filtered by *state*."""
        patterns = self._load()
        if state is not None:
            patterns = [p for p in patterns if p.get("status") == state]
        return patterns

    def get(self, pattern_id: str) -> Optional[dict]:
        """Return a single pattern by id, or None."""
        for p in self._load():
            if p.get("pattern_id") == pattern_id:
                return p
        return None

    def add(self, pattern: dict) -> dict:
        """Add a new forbidden pattern (status forced to *active*).

        Required keys: pattern_id, type, summary, reason, failure_mode.
        Returns the stored pattern dict.
        """
        required = {"pattern_id", "type", "summary", "reason", "failure_mode"}
        missing = required - set(pattern.keys())
        if missing:
            raise ValueError(f"Missing required keys: {missing}")

        patterns = self._load()
        if any(p["pattern_id"] == pattern["pattern_id"] for p in patterns):
            raise ValueError(
                f"Pattern {pattern['pattern_id']} already exists"
            )

        entry = dict(pattern)
        entry["status"] = "active"
        entry["created_at"] = now_iso()
        entry["history"] = [
            {"action": "add", "timestamp": entry["created_at"]}
        ]
        patterns.append(entry)
        self._save(patterns)
        return entry

    def reassess(
        self,
        pattern_id: str,
        trigger: str,
        evidence: Optional[str] = None,
    ) -> dict:
        """Move an *active* pattern to *under_review*.

        Parameters
        ----------
        trigger : str
            One of ``REASSESSMENT_TRIGGERS``.
        evidence : str, optional
            Free-text evidence justifying the reassessment.
        """
        if trigger not in REASSESSMENT_TRIGGERS:
            raise ValueError(
                f"Invalid trigger '{trigger}'; must be one of {REASSESSMENT_TRIGGERS}"
            )
        return self._transition(
            pattern_id,
            "reassess",
            extra={"trigger": trigger, "evidence": evidence},
        )

    def retire(self, pattern_id: str, reason: Optional[str] = None) -> dict:
        """Move a pattern to *retired*."""
        return self._transition(
            pattern_id, "retire", extra={"reason": reason}
        )

    def reactivate(
        self, pattern_id: str, reason: Optional[str] = None
    ) -> dict:
        """Move a pattern back to *active*."""
        return self._transition(
            pattern_id, "reactivate", extra={"reason": reason}
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _transition(
        self,
        pattern_id: str,
        action: str,
        extra: Optional[Dict[str, Any]] = None,
    ) -> dict:
        patterns = self._load()
        idx = None
        for i, p in enumerate(patterns):
            if p.get("pattern_id") == pattern_id:
                idx = i
                break
        if idx is None:
            raise KeyError(f"Pattern '{pattern_id}' not found")

        current_state = patterns[idx].get("status", "active")
        allowed = _TRANSITIONS.get(current_state, {})
        if action not in allowed:
            raise ValueError(
                f"Cannot '{action}' pattern in state '{current_state}'. "
                f"Allowed actions: {set(allowed.keys())}"
            )

        new_state = allowed[action]
        patterns[idx]["status"] = new_state
        history_entry: Dict[str, Any] = {
            "action": action,
            "timestamp": now_iso(),
            "from": current_state,
            "to": new_state,
        }
        if extra:
            history_entry.update(extra)
        patterns[idx].setdefault("history", []).append(history_entry)
        self._save(patterns)
        return patterns[idx]

    def _load(self) -> List[dict]:
        if not self._path.exists():
            return []
        text = self._path.read_text(encoding="utf-8")
        if not text.strip():
            return []
        data = yaml.safe_load(text)
        if data is None:
            return []
        # Accept either a top-level list or a dict with 'forbidden_patterns' key.
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and "forbidden_patterns" in data:
            return data["forbidden_patterns"]
        return []

    def _save(self, patterns: List[dict]) -> None:
        atomic_yaml_write(self._path, patterns)
