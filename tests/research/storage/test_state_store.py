"""Tests for research.storage.state_store.StateStore."""

from __future__ import annotations

from pathlib import Path

from research.storage.paths import StoragePaths
from research.storage.state_store import StateStore


def _make_store(tmp_path: Path) -> StateStore:
    paths = StoragePaths(root=str(tmp_path / "store"))
    paths.ensure_dirs()
    return StateStore(paths)


class TestStateStore:

    def test_load_empty(self, tmp_path: Path):
        store = _make_store(tmp_path)
        assert store.load() == {}

    def test_save_and_load(self, tmp_path: Path):
        store = _make_store(tmp_path)
        state = {
            "current_batch": "batch_042",
            "active_logic_ids": ["L001"],
        }
        store.save(state)
        loaded = store.load()
        assert loaded["current_batch"] == "batch_042"
        assert loaded["active_logic_ids"] == ["L001"]
        # save() should auto-set last_updated_at
        assert "last_updated_at" in loaded

    def test_save_updates_timestamp(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.save({"current_batch": None})
        t1 = store.load()["last_updated_at"]

        store.save({"current_batch": "batch_043"})
        t2 = store.load()["last_updated_at"]
        assert t2 >= t1

    def test_holdout_queue_round_trip(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.save_holdout_queue({"queue": ["F001", "F002"]})
        loaded = store.load_holdout_queue()
        assert loaded["queue"] == ["F001", "F002"]
