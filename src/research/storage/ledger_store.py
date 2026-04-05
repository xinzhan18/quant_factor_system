"""SearchLedger, BatchUsage, HoldoutReviewLedger, and WriteAuditLog CRUD.

Provides append-only and section-based operations for the four ledger files
under ``ledger/``.
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
    # search_ledger.yaml — by_logic / by_family / by_experiment_tag
    # ------------------------------------------------------------------

    def load_search_ledger(self) -> dict[str, Any]:
        return load_yaml(self._paths.search_ledger_file)

    def save_search_ledger(self, data: dict[str, Any]) -> None:
        save_yaml(self._paths.search_ledger_file, data)

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
        ledger = self.load_search_ledger()
        sec = ledger.setdefault(section, {})
        old = sec.get(key, 0)
        sec[key] = old + count
        self.save_search_ledger(ledger)
        return sec[key]

    def get_search_count(self, section: str, key: str) -> int:
        ledger = self.load_search_ledger()
        return ledger.get(section, {}).get(key, 0)

    # ------------------------------------------------------------------
    # batch_usage.yaml
    # ------------------------------------------------------------------

    def load_batch_usage(self) -> dict[str, Any]:
        return load_yaml(self._paths.batch_usage_file)

    def save_batch_usage(self, data: dict[str, Any]) -> None:
        save_yaml(self._paths.batch_usage_file, data)

    def record_batch_usage(self, batch_id: str, entry: dict[str, Any]) -> None:
        """Record usage information for a batch."""
        data = self.load_batch_usage()
        batches = data.setdefault("batches", {})
        batches[batch_id] = entry
        self.save_batch_usage(data)

    # ------------------------------------------------------------------
    # holdout_review_ledger.yaml
    # ------------------------------------------------------------------

    def load_holdout_review_ledger(self) -> dict[str, Any]:
        return load_yaml(self._paths.holdout_review_ledger_file)

    def save_holdout_review_ledger(self, data: dict[str, Any]) -> None:
        save_yaml(self._paths.holdout_review_ledger_file, data)

    def append_holdout_review(self, entry: dict[str, Any]) -> None:
        ledger = self.load_holdout_review_ledger()
        items = ledger.setdefault("reviews", [])
        items.append(entry)
        self.save_holdout_review_ledger(ledger)

    # ------------------------------------------------------------------
    # write_audit_log.yaml
    # ------------------------------------------------------------------

    def load_audit_log(self) -> dict[str, Any]:
        return load_yaml(self._paths.write_audit_log_file)

    def save_audit_log(self, data: dict[str, Any]) -> None:
        save_yaml(self._paths.write_audit_log_file, data)

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
