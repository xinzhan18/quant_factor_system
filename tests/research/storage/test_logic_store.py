"""Tests for LogicStore (registry, cards, proposals, reviews, snapshots)."""

from __future__ import annotations

from pathlib import Path

from research.storage.paths import StoragePaths
from research.storage.logic_store import LogicStore


def _make_store(tmp_path: Path) -> LogicStore:
    sp = StoragePaths(tmp_path / "s")
    sp.ensure_dirs()
    return LogicStore(sp)


class TestLogicRegistry:

    def test_empty_registry(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        assert store.load_registry() == {}

    def test_upsert_insert(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.upsert_registry_entry("L001", {"name": "breakout", "status": "active"})
        reg = store.load_registry()
        assert len(reg["logics"]) == 1
        assert reg["logics"][0]["logic_id"] == "L001"
        assert reg["logics"][0]["name"] == "breakout"

    def test_upsert_update(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.upsert_registry_entry("L001", {"name": "breakout", "status": "active"})
        store.upsert_registry_entry("L001", {"name": "breakout", "status": "warm"})
        reg = store.load_registry()
        assert len(reg["logics"]) == 1
        assert reg["logics"][0]["status"] == "warm"

    def test_remove_entry(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.upsert_registry_entry("L001", {"name": "a"})
        store.upsert_registry_entry("L002", {"name": "b"})
        store.remove_registry_entry("L001")
        reg = store.load_registry()
        assert len(reg["logics"]) == 1
        assert reg["logics"][0]["logic_id"] == "L002"


class TestLogicCards:

    def test_save_and_load_card(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        card = {"name": "breakout", "status": "active", "hypothesis": {"condition": "vol squeeze"}}
        store.save_card("L001", card)
        loaded = store.load_card("L001")
        assert loaded["logic_id"] == "L001"
        assert loaded["name"] == "breakout"
        assert loaded["hypothesis"]["condition"] == "vol squeeze"

    def test_list_cards(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save_card("L001", {"name": "a"})
        store.save_card("L002", {"name": "b"})
        assert store.list_cards() == ["L001", "L002"]

    def test_list_cards_empty(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        assert store.list_cards() == []

    def test_delete_card(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save_card("L001", {"name": "a"})
        store.delete_card("L001")
        assert store.load_card("L001") == {}

    def test_delete_nonexistent(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.delete_card("L999")  # should not raise


class TestProposalsAndReviews:

    def test_proposal_roundtrip(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save_proposal("P001", {"name": "test", "origin_type": "canonical"})
        loaded = store.load_proposal("P001")
        assert loaded["proposal_id"] == "P001"
        assert loaded["origin_type"] == "canonical"

    def test_list_proposals(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save_proposal("P001", {"name": "a"})
        store.save_proposal("P002", {"name": "b"})
        assert store.list_proposals() == ["P001", "P002"]

    def test_review_roundtrip(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save_review("P001", {"verdict": "pass", "score": 0.84})
        loaded = store.load_review("P001")
        assert loaded["verdict"] == "pass"

    def test_snapshot_roundtrip(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save_snapshot("schedule_20260405", {"active_pool": ["L001"]})
        loaded = store.load_snapshot("schedule_20260405")
        assert loaded["active_pool"] == ["L001"]

    def test_list_snapshots(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save_snapshot("s1", {"a": 1})
        store.save_snapshot("s2", {"b": 2})
        assert store.list_snapshots() == ["s1", "s2"]
