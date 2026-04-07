"""Consistency checks across storage truth sources."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

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
