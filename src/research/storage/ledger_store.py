"""Unified ledger CRUD — search, batch usage, holdout review, audit log.

All four sections live in a single ``governance/ledger.yaml`` file.
Each public method operates on its own section without touching others.

The ``_save_ledger`` method validates top-level keys against a whitelist
to prevent stray writes (e.g. writing ``batches:`` instead of
``batch_usage.batches``).
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from research.domain.batch_phases import LEDGER_TOP_LEVEL_WHITELIST

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
        # Guard: reject stray top-level keys before writing
        unexpected = set(data.keys()) - LEDGER_TOP_LEVEL_WHITELIST
        if unexpected:
            raise ValueError(
                f"Refusing to write ledger with unexpected top-level keys: "
                f"{sorted(unexpected)}. All batch data must go under "
                f"batch_usage.batches, not as top-level keys."
            )
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
        field: str | None = None,
    ) -> dict[str, Any]:
        """Atomically increment a counter in *section* (by_logic / by_family / by_experiment_tag).

        Returns the new value after increment.
        """
        if section not in ("by_logic", "by_family", "by_experiment_tag"):
            raise ValueError(
                f"section must be by_logic, by_family, or by_experiment_tag; got {section!r}"
            )
        search = self.load_search_ledger()
        sec = search.setdefault(section, {})
        record = sec.get(key, {})
        if isinstance(record, int):
            record = {"count": record}
        if not isinstance(record, dict):
            record = {}
        target_field = field or _default_counter_field(section)
        record[target_field] = int(record.get(target_field, 0)) + count
        sec[key] = record
        self.save_search_ledger(search)
        return record

    def get_search_count(self, section: str, key: str) -> int:
        value = self.load_search_ledger().get(section, {}).get(key, 0)
        if isinstance(value, int):
            return value
        if isinstance(value, dict):
            return int(value.get(_default_counter_field(section), 0))
        return 0

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

    def record_batch_usage_from_sources(
        self,
        batch_id: str,
        manifest: dict[str, Any],
        judge_report: dict[str, Any] | None = None,
        judge_packet: dict[str, Any] | None = None,
        *,
        phase: str = "finalized",
    ) -> None:
        """Build unified-schema entry from manifest + judge_report + judge_packet.

        judge_packet provides sample_policy ranges as fallback when
        judge_report lacks them.
        """
        candidates = manifest.get("candidates", [])
        logic_ids = sorted({
            str(c.get("logic_id", ""))
            for c in candidates if c.get("logic_id")
        })

        # Derive ranges from packet sample_policy, then manifest
        train_range = ["2015-01-01", "2021-12-31"]
        validation_range = ["2022-01-01", "2023-12-31"]
        validation_window_id = "val_2022_2023"
        holdout_used = False

        if judge_packet:
            sp = judge_packet.get("sample_policy_version", "")
            # Try to extract from packet directly
            pkt = judge_packet.get("judge_packet", judge_packet)
            if pkt.get("sample_policy"):
                policy = pkt["sample_policy"]
                train_range = policy.get("train_range", train_range)
                validation_range = policy.get("validation_range", validation_range)
                validation_window_id = policy.get(
                    "validation_window_id", validation_window_id
                )

        if judge_report:
            holdout_used = bool(judge_report.get("holdout_used", False))

        # Check candidate briefs for holdout info
        if not holdout_used and judge_packet:
            pkt = judge_packet.get("judge_packet", judge_packet)
            for brief in pkt.get("candidate_briefs", []):
                if brief.get("holdout_review_recommended"):
                    holdout_used = True
                    break

        entry = {
            "batch_id": batch_id,
            "candidate_count": len(candidates),
            "logic_ids": logic_ids,
            "phase": phase,
            "holdout_used": holdout_used,
            "train_range": train_range,
            "validation_range": validation_range,
            "validation_window_id": validation_window_id,
        }
        self.record_batch_usage(batch_id, entry)

    def update_batch_phase(self, batch_id: str, phase: str) -> None:
        """Update the phase field for a specific batch in batch_usage."""
        data = self.load_batch_usage()
        batches = data.get("batches", {})
        if batch_id in batches:
            batches[batch_id]["phase"] = phase
            self.save_batch_usage(data)

    def validate_ledger_structure(self) -> list[str]:
        """Check for stray top-level keys. Returns list of violations."""
        from research.domain.batch_phases import validate_ledger_top_level_keys
        return validate_ledger_top_level_keys(self._load_ledger())

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


def _default_counter_field(section: str) -> str:
    if section == "by_logic":
        return "logic_attempt_count_to_date"
    if section == "by_family":
        return "family_attempt_count_to_date"
    return "batches_seen"
