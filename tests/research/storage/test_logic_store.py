"""Tests for research.storage.logic_store.LogicStore."""

from __future__ import annotations

from pathlib import Path

from research.storage.paths import StoragePaths
from research.storage.logic_store import LogicStore


def _make_store(tmp_path: Path) -> LogicStore:
    paths = StoragePaths(root=str(tmp_path / "store"))
    paths.ensure_dirs()
    return LogicStore(paths)


class TestLogicRegistry:

    def test_load_empty_registry(self, tmp_path: Path):
        store = _make_store(tmp_path)
        assert store.load_registry() == {}

    def test_save_and_list(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.save_registry({
            "logics": [
                {"logic_id": "L001", "name": "vol_breakout", "status": "active"},
            ]
        })
        assert len(store.list_logics()) == 1
        assert store.list_logics()[0]["logic_id"] == "L001"

    def test_upsert_insert(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.save_registry({"logics": []})
        store.upsert_registry_entry({
            "logic_id": "L002",
            "name": "reversal",
            "status": "warm",
        })
        assert len(store.list_logics()) == 1
        assert store.list_logics()[0]["logic_id"] == "L002"

    def test_upsert_update(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.save_registry({
            "logics": [{"logic_id": "L001", "status": "active"}]
        })
        store.upsert_registry_entry({"logic_id": "L001", "status": "saturated"})
        logics = store.list_logics()
        assert len(logics) == 1
        assert logics[0]["status"] == "saturated"

    def test_logics_by_status(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.save_registry({
            "logics": [
                {"logic_id": "L001", "status": "active"},
                {"logic_id": "L002", "status": "warm"},
                {"logic_id": "L003", "status": "active"},
            ]
        })
        active = store.logics_by_status("active")
        assert len(active) == 2
        assert {l["logic_id"] for l in active} == {"L001", "L003"}


class TestLogicCards:

    def test_card_round_trip(self, tmp_path: Path):
        store = _make_store(tmp_path)
        card = {
            "logic_id": "L001",
            "name": "compression_breakout",
            "status": "active",
            "hypothesis": {"condition": "vol compression"},
        }
        store.save_card("L001", card)
        loaded = store.load_card("L001")
        assert loaded == card

    def test_list_card_ids(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.save_card("L001", {"logic_id": "L001"})
        store.save_card("L002", {"logic_id": "L002"})
        ids = store.list_card_ids()
        assert ids == ["L001", "L002"]


class TestLogicProposalsAndReviews:

    def test_proposal_round_trip(self, tmp_path: Path):
        store = _make_store(tmp_path)
        proposal = {"proposal_id": "P021", "name": "test_proposal"}
        store.save_proposal("P021", proposal)
        assert store.load_proposal("P021") == proposal

    def test_review_round_trip(self, tmp_path: Path):
        store = _make_store(tmp_path)
        review = {"proposal_id": "P021", "verdict": "pass"}
        store.save_review("P021", review)
        assert store.load_review("P021") == review


class TestLogicSnapshots:

    def test_snapshot_round_trip(self, tmp_path: Path):
        store = _make_store(tmp_path)
        snap = {"active_pool": ["L001"]}
        store.save_snapshot("schedule_20260405", snap)
        assert store.load_snapshot("schedule_20260405") == snap

    def test_list_snapshots(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.save_snapshot("schedule_a", {"x": 1})
        store.save_snapshot("schedule_b", {"x": 2})
        assert store.list_snapshots() == ["schedule_a", "schedule_b"]
