"""Tests for StateStore (research state + holdout queue)."""

from __future__ import annotations

from pathlib import Path

from research.storage.paths import StoragePaths
from research.storage.state_store import StateStore


def _make_store(tmp_path: Path) -> StateStore:
    sp = StoragePaths(tmp_path / "s")
    sp.ensure_dirs()
    return StateStore(sp)


class TestResearchState:

    def test_load_empty(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        assert store.load_state() == {}

    def test_save_and_load(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        state = {"current_batch": "batch_042", "active_logic_ids": ["L001"]}
        store.save_state(state)
        loaded = store.load_state()
        assert loaded["current_batch"] == "batch_042"
        assert loaded["active_logic_ids"] == ["L001"]
        assert "last_updated_at" in loaded

    def test_update_state_merges(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save_state({"current_batch": "batch_001", "flag": True})
        result = store.update_state({"current_batch": "batch_002"})
        assert result["current_batch"] == "batch_002"
        assert result["flag"] is True


    def test_recompute_from_cards_includes_schedulable(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        sp = StoragePaths(tmp_path / "s")
        from research.storage.yaml_io import save_yaml

        save_yaml(sp.logic_card_file("L001"), {"logic_id": "L001", "status": "productive"})
        save_yaml(sp.logic_card_file("L002"), {"logic_id": "L002", "status": "active"})
        save_yaml(sp.logic_card_file("L003"), {"logic_id": "L003", "status": "warm"})
        save_yaml(sp.logic_card_file("L004"), {"logic_id": "L004", "status": "parked"})

        state = store.recompute_from_cards(sp.logic_cards_dir)

        assert state["active_logic_ids"] == ["L002"]
        assert state["warm_logic_ids"] == ["L003"]
        assert state["schedulable_logic_ids"] == ["L001", "L002", "L003"]


class TestHoldoutQueue:

    def test_empty_queue(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        assert store.load_holdout_queue() == {"holdout_queue": []}

    def test_enqueue_and_dequeue(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.enqueue_holdout({"factor_id": "F001"})
        store.enqueue_holdout({"factor_id": "F002"})

        first = store.dequeue_holdout()
        assert first["candidate_id"] == "F001"

        second = store.dequeue_holdout()
        assert second["candidate_id"] == "F002"

        assert store.dequeue_holdout() is None

    def test_dequeue_empty(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        assert store.dequeue_holdout() is None
