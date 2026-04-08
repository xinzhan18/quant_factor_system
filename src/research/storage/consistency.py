"""Consistency checks across storage truth sources.

``check()`` provides the original baseline checks.
``check_extended()`` runs ``check()`` plus 6 additional rules covering
reflection existence, thread alignment, ledger structure, holdout
metadata, batch dir ↔ ledger phase, and batch usage schema.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from research.domain.batch_phases import (
    BATCH_USAGE_UNIFIED_FIELDS,
    LEDGER_TOP_LEVEL_WHITELIST,
    derive_phase_from_files,
)
from research.governance.holdout_queue import HoldoutQueue
from research.storage.paths import StoragePaths
from research.storage.result_store import ResultStore
from research.storage.state_store import StateStore
from research.storage.yaml_io import load_yaml


@dataclass
class ConsistencyReport:
    ok: bool
    errors: list[str] = field(default_factory=list)


class StorageConsistencyChecker:
    def __init__(self, paths: StoragePaths | None = None) -> None:
        self._paths = paths or StoragePaths()
        self._state = StateStore(self._paths)
        self._results = ResultStore(self._paths)

    def check(self, batch_id: str | None = None) -> ConsistencyReport:
        errors: list[str] = []

        state = self._state.load_state()
        cards = {
            path.stem: load_yaml(path)
            for path in sorted(self._paths.logic_cards_dir.glob("L*.yaml"))
        }
        active = sorted(
            card.get("logic_id", "")
            for card in cards.values()
            if card.get("status") == "active"
        )
        warm = sorted(
            card.get("logic_id", "")
            for card in cards.values()
            if card.get("status") == "warm"
        )
        schedulable = sorted(
            card.get("logic_id", "")
            for card in cards.values()
            if card.get("status") in ("active", "productive", "warm")
        )
        if sorted(state.get("active_logic_ids", [])) != active:
            errors.append("research_state.active_logic_ids does not match logic card statuses")
        if sorted(state.get("warm_logic_ids", [])) != warm:
            errors.append("research_state.warm_logic_ids does not match logic card statuses")
        if sorted(state.get("schedulable_logic_ids", [])) != schedulable:
            errors.append("research_state.schedulable_logic_ids does not match logic card statuses")

        queue = HoldoutQueue.load_yaml(str(self._paths.pending_holdout_queue_file))
        ledger_reviews = load_yaml(self._paths.ledger_file).get("holdout_reviews", {}).get("reviews", [])
        pending_reviews = sorted(
            str(item.get("target_id", ""))
            for item in ledger_reviews
            if isinstance(item, dict) and item.get("status") == "pending"
        )
        pending_queue = sorted(entry.candidate_id for entry in queue.pending())
        if pending_reviews != pending_queue:
            errors.append("holdout queue pending entries do not match governance ledger")

        if batch_id:
            report = self._results.load_judge_report(batch_id)
            recommendations = report.get("logic_recommendations", {})
            if isinstance(recommendations, dict):
                for logic_id, rec in recommendations.items():
                    if not isinstance(rec, dict):
                        continue
                    card = cards.get(logic_id)
                    if not card:
                        errors.append(f"logic card missing for recommendation {logic_id}")
                        continue
                    if card.get("status") != rec.get("recommended_status"):
                        errors.append(
                            f"logic {logic_id} status mismatch: "
                            f"card={card.get('status')} report={rec.get('recommended_status')}"
                        )

        return ConsistencyReport(ok=not errors, errors=errors)

    def check_extended(self, batch_id: str | None = None) -> ConsistencyReport:
        """Run all checks including the 6 new extended rules."""
        report = self.check(batch_id=batch_id)
        errors = report.errors

        errors.extend(self._check_batch_dir_ledger_alignment())
        errors.extend(self._check_reflection_existence())
        errors.extend(self._check_thread_card_alignment())
        errors.extend(self._check_ledger_top_level_keys())
        errors.extend(self._check_holdout_metadata())
        errors.extend(self._check_batch_usage_schema())

        return ConsistencyReport(ok=not errors, errors=errors)

    # ------------------------------------------------------------------
    # Extended checks
    # ------------------------------------------------------------------

    def _check_batch_dir_ledger_alignment(self) -> list[str]:
        """Verify batch dir derived phase matches ledger batch_usage phase."""
        errors: list[str] = []
        ledger = load_yaml(self._paths.ledger_file)
        batch_usage = ledger.get("batch_usage", {}).get("batches", {})

        if not self._paths.batches_dir.exists():
            return errors

        for d in sorted(self._paths.batches_dir.iterdir()):
            if not d.is_dir() or not d.name.startswith("batch_"):
                continue
            bid = d.name
            if bid not in batch_usage:
                errors.append(f"{bid}: on disk but missing from batch_usage")
                continue
            ledger_phase = batch_usage[bid].get("phase", "")
            if ledger_phase in ("finalized", "abandoned"):
                continue
            derived = derive_phase_from_files(d)
            if derived != ledger_phase:
                errors.append(
                    f"{bid}: ledger phase={ledger_phase!r} "
                    f"but disk files imply {derived!r}"
                )
        return errors

    def _check_reflection_existence(self) -> list[str]:
        """Verify reflection .md exists for every logic with last_reflected_batch."""
        errors: list[str] = []
        for card_file in sorted(self._paths.logic_cards_dir.glob("L*.yaml")):
            card = load_yaml(card_file)
            logic_id = card.get("logic_id", card_file.stem)
            if card.get("last_reflected_batch"):
                if not self._paths.logic_reflection_file(logic_id).exists():
                    errors.append(
                        f"{logic_id}: last_reflected_batch="
                        f"{card['last_reflected_batch']!r} but reflection file missing"
                    )
        return errors

    def _check_thread_card_alignment(self) -> list[str]:
        """If card is parked/saturated/dead, no threads should be active."""
        errors: list[str] = []
        terminal = {"parked", "saturated", "dead"}
        for card_file in sorted(self._paths.logic_cards_dir.glob("L*.yaml")):
            card = load_yaml(card_file)
            logic_id = card.get("logic_id", card_file.stem)
            if card.get("status", "") not in terminal:
                continue
            active_threads = [
                t.get("id", "?")
                for t in card.get("deepening_threads", [])
                if isinstance(t, dict) and t.get("status") == "active"
            ]
            if active_threads:
                errors.append(
                    f"{logic_id}: card is {card['status']!r} "
                    f"but has active threads: {active_threads}"
                )
        return errors

    def _check_ledger_top_level_keys(self) -> list[str]:
        """Use whitelist to detect stray top-level keys in ledger."""
        ledger = load_yaml(self._paths.ledger_file)
        unexpected = set(ledger.keys()) - LEDGER_TOP_LEVEL_WHITELIST
        return [
            f"Stray ledger top-level key: {k!r}" for k in sorted(unexpected)
        ]

    def _check_holdout_metadata(self) -> list[str]:
        """Verify pending holdout entries have logic_id and family_id."""
        errors: list[str] = []
        queue = HoldoutQueue.load_yaml(str(self._paths.pending_holdout_queue_file))
        for entry in queue.pending():
            if not entry.logic_id:
                errors.append(
                    f"Holdout {entry.batch_id}/{entry.candidate_id}: "
                    f"pending but missing logic_id"
                )
            if not entry.family_id:
                errors.append(
                    f"Holdout {entry.batch_id}/{entry.candidate_id}: "
                    f"pending but missing family_id"
                )
        return errors

    def _check_batch_usage_schema(self) -> list[str]:
        """Check all batch_usage entries have the unified field set."""
        errors: list[str] = []
        ledger = load_yaml(self._paths.ledger_file)
        batch_usage = ledger.get("batch_usage", {}).get("batches", {})

        for bid, entry in sorted(batch_usage.items()):
            if not isinstance(entry, dict):
                errors.append(f"{bid}: batch_usage entry is not a dict")
                continue
            missing = set(BATCH_USAGE_UNIFIED_FIELDS) - set(entry.keys())
            # logic_id (singular) counts as logic_ids
            if "logic_ids" in missing and "logic_id" in entry:
                missing.discard("logic_ids")
            if missing:
                errors.append(
                    f"{bid}: missing unified schema fields: {sorted(missing)}"
                )
        return errors
