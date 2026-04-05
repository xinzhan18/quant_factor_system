"""Tests for LedgerStore (unified ledger: search, batch usage, holdout review, audit log)."""

from __future__ import annotations

from pathlib import Path

import pytest

from research.storage.paths import StoragePaths
from research.storage.ledger_store import LedgerStore


def _make_store(tmp_path: Path) -> LedgerStore:
    sp = StoragePaths(tmp_path / "s")
    sp.ensure_dirs()
    return LedgerStore(sp)


class TestSearchLedger:

    def test_empty_ledger(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        assert store.load_search_ledger() == {}

    def test_increment_by_logic(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        val = store.increment_search("by_logic", "L001")
        assert val == 1
        val = store.increment_search("by_logic", "L001")
        assert val == 2
        assert store.get_search_count("by_logic", "L001") == 2

    def test_increment_by_family(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.increment_search("by_family", "FM_breakout", count=3)
        assert store.get_search_count("by_family", "FM_breakout") == 3

    def test_increment_by_experiment_tag(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.increment_search("by_experiment_tag", "vol_squeeze_v2")
        assert store.get_search_count("by_experiment_tag", "vol_squeeze_v2") == 1

    def test_invalid_section_raises(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        with pytest.raises(ValueError, match="section must be"):
            store.increment_search("by_invalid", "key")

    def test_get_missing_key_returns_zero(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        assert store.get_search_count("by_logic", "MISSING") == 0


class TestBatchUsage:

    def test_record_and_load(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.record_batch_usage("batch_042", {"candidates": 6, "admitted": 2})
        data = store.load_batch_usage()
        assert data["batches"]["batch_042"]["candidates"] == 6

    def test_overwrite_batch(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.record_batch_usage("batch_042", {"candidates": 6})
        store.record_batch_usage("batch_042", {"candidates": 8})
        data = store.load_batch_usage()
        assert data["batches"]["batch_042"]["candidates"] == 8


class TestHoldoutReviewLedger:

    def test_append_review(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.append_holdout_review({"factor_id": "F001", "verdict": "pass"})
        store.append_holdout_review({"factor_id": "F002", "verdict": "fail"})
        data = store.load_holdout_review_ledger()
        assert len(data["reviews"]) == 2
        assert data["reviews"][0]["factor_id"] == "F001"


class TestAuditLog:

    def test_append_audit_entry(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.append_audit_entry(
            actor="judge",
            action="admit",
            target="F013",
            detail="Score 79.9",
        )
        log = store.load_audit_log()
        assert len(log["entries"]) == 1
        entry = log["entries"][0]
        assert entry["actor"] == "judge"
        assert entry["action"] == "admit"
        assert entry["target"] == "F013"
        assert "timestamp" in entry

    def test_multiple_entries(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.append_audit_entry(actor="judge", action="admit", target="F001")
        store.append_audit_entry(actor="judge", action="reject", target="F002")
        log = store.load_audit_log()
        assert len(log["entries"]) == 2


class TestSectionIsolation:
    """Verify that writing to one section does not clobber another."""

    def test_sections_coexist(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)

        # Write to all four sections
        store.increment_search("by_logic", "L001")
        store.record_batch_usage("batch_001", {"candidates": 3})
        store.append_holdout_review({"factor_id": "F001", "verdict": "pass"})
        store.append_audit_entry(actor="judge", action="admit", target="F001")

        # Verify all sections survive
        assert store.get_search_count("by_logic", "L001") == 1
        assert store.load_batch_usage()["batches"]["batch_001"]["candidates"] == 3
        assert len(store.load_holdout_review_ledger()["reviews"]) == 1
        assert len(store.load_audit_log()["entries"]) == 1

        # Write again to one section
        store.increment_search("by_logic", "L001")

        # All other sections still intact
        assert store.get_search_count("by_logic", "L001") == 2
        assert store.load_batch_usage()["batches"]["batch_001"]["candidates"] == 3
        assert len(store.load_holdout_review_ledger()["reviews"]) == 1
        assert len(store.load_audit_log()["entries"]) == 1
