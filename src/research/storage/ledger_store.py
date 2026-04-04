"""Ledger CRUD — SearchLedger, BatchUsage, HoldoutReviewLedger, WriteAuditLog.

Manages:
- ``ledger/search_ledger.yaml``
- ``ledger/batch_usage.yaml``
- ``ledger/holdout_review_ledger.yaml``
- ``ledger/write_audit_log.yaml``

The search ledger supports sectioned counters (by_logic, by_family,
by_experiment_tag) with atomic increment helpers.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml, save_yaml

logger = logging.getLogger(__name__)


class LedgerStore:
    """CRUD operations for all ledger files."""

    def __init__(self, paths: StoragePaths) -> None:
        self.paths = paths

    # ------------------------------------------------------------------
    # search_ledger.yaml
    # ------------------------------------------------------------------
    def load_search_ledger(self) -> dict:
        """Load the search ledger."""
        return load_yaml(self.paths.search_ledger)

    def save_search_ledger(self, ledger: dict) -> None:
        save_yaml(self.paths.search_ledger, ledger)

    def _ensure_ledger_sections(self, ledger: dict) -> dict:
        """Guarantee the four top-level sections exist."""
        ledger.setdefault("by_logic", {})
        ledger.setdefault("by_family", {})
        ledger.setdefault("by_experiment_tag", {})
        ledger.setdefault("discovery_candidates", [])
        return ledger

    def increment_search_counter(
        self,
        section: str,
        key: str,
        field: str,
        delta: int = 1,
    ) -> int:
        """Atomically increment a counter in the search ledger.

        Parameters
        ----------
        section : str
            One of ``"by_logic"``, ``"by_family"``, ``"by_experiment_tag"``.
        key : str
            The entry key within the section (e.g. logic_id).
        field : str
            The counter field name (e.g. ``"probe_attempts"``).
        delta : int
            Amount to add (default 1).

        Returns
        -------
        int
            The new value of the counter.
        """
        ledger = self._ensure_ledger_sections(self.load_search_ledger())
        bucket: dict = ledger[section].setdefault(key, {})
        old = bucket.get(field, 0)
        new_val = old + delta
        bucket[field] = new_val
        self.save_search_ledger(ledger)
        return new_val

    def append_discovery_candidate(self, candidate: dict) -> None:
        """Append an entry to ``discovery_candidates``."""
        ledger = self._ensure_ledger_sections(self.load_search_ledger())
        ledger["discovery_candidates"].append(candidate)
        self.save_search_ledger(ledger)

    # ------------------------------------------------------------------
    # batch_usage.yaml
    # ------------------------------------------------------------------
    def load_batch_usage(self) -> dict:
        return load_yaml(self.paths.batch_usage)

    def save_batch_usage(self, data: dict) -> None:
        save_yaml(self.paths.batch_usage, data)

    def record_batch(self, batch_id: str, usage: dict) -> None:
        """Record usage for a single batch."""
        data = self.load_batch_usage()
        batches: dict = data.setdefault("batches", {})
        batches[batch_id] = usage
        self.save_batch_usage(data)

    # ------------------------------------------------------------------
    # holdout_review_ledger.yaml
    # ------------------------------------------------------------------
    def load_holdout_review(self) -> dict:
        return load_yaml(self.paths.holdout_review_ledger)

    def save_holdout_review(self, data: dict) -> None:
        save_yaml(self.paths.holdout_review_ledger, data)

    def append_holdout_entry(self, entry: dict) -> None:
        """Append a single holdout review entry."""
        data = self.load_holdout_review()
        entries: list = data.setdefault("entries", [])
        entries.append(entry)
        self.save_holdout_review(data)

    # ------------------------------------------------------------------
    # write_audit_log.yaml
    # ------------------------------------------------------------------
    def load_audit_log(self) -> dict:
        return load_yaml(self.paths.write_audit_log)

    def save_audit_log(self, data: dict) -> None:
        save_yaml(self.paths.write_audit_log, data)

    def append_audit_entry(
        self,
        actor: str,
        action: str,
        target: str,
        detail: Optional[str] = None,
    ) -> None:
        """Append a timestamped audit log entry."""
        data = self.load_audit_log()
        entries: list = data.setdefault("entries", [])
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
            "action": action,
            "target": target,
        }
        if detail is not None:
            entry["detail"] = detail
        entries.append(entry)
        self.save_audit_log(data)
