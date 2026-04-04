"""Tests for research.storage.ledger_store.LedgerStore."""

from __future__ import annotations

from pathlib import Path

from research.storage.paths import StoragePaths
from research.storage.ledger_store import LedgerStore


def _make_store(tmp_path: Path) -> LedgerStore:
    paths = StoragePaths(root=str(tmp_path / "store"))
    paths.ensure_dirs()
    return LedgerStore(paths)


class TestSearchLedger:

    def test_load_empty(self, tmp_path: Path):
        store = _make_store(tmp_path)
        assert store.load_search_ledger() == {}

    def test_increment_new_key(self, tmp_path: Path):
        store = _make_store(tmp_path)
        new_val = store.increment_search_counter(
            "by_logic", "L001", "probe_attempts"
        )
        assert new_val == 1

        ledger = store.load_search_ledger()
        assert ledger["by_logic"]["L001"]["probe_attempts"] == 1

    def test_increment_existing_key(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.increment_search_counter("by_logic", "L001", "probe_attempts")
        store.increment_search_counter("by_logic", "L001", "probe_attempts")
        new_val = store.increment_search_counter("by_logic", "L001", "probe_attempts")
        assert new_val == 3

    def test_increment_custom_delta(self, tmp_path: Path):
        store = _make_store(tmp_path)
        new_val = store.increment_search_counter(
            "by_family", "FM_breakout", "eval_attempts", delta=5
        )
        assert new_val == 5

    def test_append_discovery_candidate(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.append_discovery_candidate({"candidate_id": "C042_01"})
        store.append_discovery_candidate({"candidate_id": "C042_02"})

        ledger = store.load_search_ledger()
        assert len(ledger["discovery_candidates"]) == 2
        assert ledger["discovery_candidates"][0]["candidate_id"] == "C042_01"

    def test_sections_auto_created(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.increment_search_counter("by_experiment_tag", "exp_001", "runs")
        ledger = store.load_search_ledger()
        assert "by_logic" in ledger
        assert "by_family" in ledger
        assert "by_experiment_tag" in ledger
        assert "discovery_candidates" in ledger


class TestBatchUsage:

    def test_record_batch(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.record_batch("batch_042", {
            "candidate_count": 6,
            "admitted": 2,
            "rejected": 4,
        })
        usage = store.load_batch_usage()
        assert "batch_042" in usage["batches"]
        assert usage["batches"]["batch_042"]["admitted"] == 2


class TestHoldoutReview:

    def test_append_entry(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.append_holdout_entry({"factor_id": "F013", "verdict": "pass"})
        data = store.load_holdout_review()
        assert len(data["entries"]) == 1


class TestWriteAuditLog:

    def test_append_audit_entry(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.append_audit_entry(
            actor="judge",
            action="admit",
            target="F013",
            detail="Admitted with score 78.2",
        )
        log = store.load_audit_log()
        assert len(log["entries"]) == 1
        entry = log["entries"][0]
        assert entry["actor"] == "judge"
        assert entry["action"] == "admit"
        assert entry["target"] == "F013"
        assert "timestamp" in entry
        assert entry["detail"] == "Admitted with score 78.2"

    def test_append_without_detail(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.append_audit_entry(actor="logic", action="create", target="L005")
        entry = store.load_audit_log()["entries"][0]
        assert "detail" not in entry
