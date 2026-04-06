"""Unified ledger CRUD — search, batch usage, holdout review, audit log.

All four sections live in a single ``governance/ledger.yaml`` file.
Each public method operates on its own section without touching others.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .paths import StoragePaths
from .yaml_io import load_yaml, save_yaml


class LedgerStore:
    """CRUD for research ledgers (search, batch usage, holdout review, audit)."""

    def __init__(self, paths: StoragePaths) -> None:
        self._paths = paths

    # ------------------------------------------------------------------
    # Private: full-file read/write
    # ------------------------------------------------------------------

    def _load_ledger(self) -> dict[str, Any]:
        return load_yaml(self._paths.ledger_file)

    def _save_ledger(self, data: dict[str, Any]) -> None:
        save_yaml(self._paths.ledger_file, data)

    # ------------------------------------------------------------------
    # search_ledger section — by_logic / by_family / by_experiment_tag
    # ------------------------------------------------------------------

    def load_search_ledger(self) -> dict[str, Any]:
        return self._load_ledger().get("search_ledger", {})

    def save_search_ledger(self, data: dict[str, Any]) -> None:
        ledger = self._load_ledger()
        ledger["search_ledger"] = data
        self._save_ledger(ledger)

    def increment_search(
        self,
        section: str,
        key: str,
        *,
        count: int = 1,
    ) -> int:
        """Atomically increment a counter in *section* (by_logic / by_family / by_experiment_tag).

        Returns the new value after increment.
        """
        if section not in ("by_logic", "by_family", "by_experiment_tag"):
            raise ValueError(
                f"section must be by_logic, by_family, or by_experiment_tag; got {section!r}"
            )
        search = self.load_search_ledger()
        sec = search.setdefault(section, {})
        old = sec.get(key, 0)
        sec[key] = old + count
        self.save_search_ledger(search)
        return sec[key]

    def get_search_count(self, section: str, key: str) -> int:
        return self.load_search_ledger().get(section, {}).get(key, 0)

    def append_discovery_candidate(self, entry: dict[str, Any]) -> None:
        """Append a discovery candidate to search_ledger.discovery_candidates."""
        search = self.load_search_ledger()
        candidates = search.setdefault("discovery_candidates", [])
        candidates.append(entry)
        self.save_search_ledger(search)

    # ------------------------------------------------------------------
    # batch_usage section
    # ------------------------------------------------------------------

    def load_batch_usage(self) -> dict[str, Any]:
        return self._load_ledger().get("batch_usage", {})

    def save_batch_usage(self, data: dict[str, Any]) -> None:
        ledger = self._load_ledger()
        ledger["batch_usage"] = data
        self._save_ledger(ledger)

    def record_batch_usage(self, batch_id: str, entry: dict[str, Any]) -> None:
        """Record usage information for a batch."""
        data = self.load_batch_usage()
        batches = data.setdefault("batches", {})
        batches[batch_id] = entry
        self.save_batch_usage(data)

    # ------------------------------------------------------------------
    # holdout_reviews section
    # ------------------------------------------------------------------

    def load_holdout_review_ledger(self) -> dict[str, Any]:
        return self._load_ledger().get("holdout_reviews", {})

    def save_holdout_review_ledger(self, data: dict[str, Any]) -> None:
        ledger = self._load_ledger()
        ledger["holdout_reviews"] = data
        self._save_ledger(ledger)

    def append_holdout_review(self, entry: dict[str, Any]) -> None:
        data = self.load_holdout_review_ledger()
        items = data.setdefault("reviews", [])
        items.append(entry)
        self.save_holdout_review_ledger(data)

    # ------------------------------------------------------------------
    # write_audit_log section
    # ------------------------------------------------------------------

    def load_audit_log(self) -> dict[str, Any]:
        return self._load_ledger().get("write_audit_log", {})

    def save_audit_log(self, data: dict[str, Any]) -> None:
        ledger = self._load_ledger()
        ledger["write_audit_log"] = data
        self._save_ledger(ledger)

    def append_audit_entry(
        self,
        *,
        actor: str,
        action: str,
        target: str,
        detail: str = "",
    ) -> None:
        """Append a write-audit entry with a UTC timestamp."""
        log = self.load_audit_log()
        entries = log.setdefault("entries", [])
        entries.append(
            {
                "timestamp": _now_iso(),
                "actor": actor,
                "action": action,
                "target": target,
                "detail": detail,
            }
        )
        self.save_audit_log(log)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
