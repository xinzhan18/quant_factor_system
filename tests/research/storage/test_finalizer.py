"""Tests for batch finalization and storage consistency."""

from __future__ import annotations

from pathlib import Path

from research.storage.consistency import StorageConsistencyChecker
from research.storage.finalizer import BatchFinalizer
from research.storage.paths import StoragePaths
from research.storage.state_store import StateStore
from research.storage.yaml_io import load_yaml, save_yaml


def _minimal_card(logic_id: str, status: str = "active") -> dict:
    return {
        "logic_id": logic_id,
        "name": f"logic {logic_id}",
        "category": "volume_price",
        "status": status,
        "priority": "high",
        "hypothesis": {"condition": "x", "behavior": "y", "timeframe": "z"},
        "contract": {
            "current_focus_question": "start",
            "preferred_families": [],
            "suggested_ops": [],
            "avoid_patterns": [],
        },
        "evidence_summary": {
            "factors_generated": 0,
            "factors_admitted": 0,
            "rounds_without_admit": 0,
            "productive_families": [],
            "failed_families": [],
            "exhausted_routes": [],
            "current_bottleneck": "",
            "transitions": [],
            "promoted_families": [],
        },
        "deepening_threads": [],
        "next_actions": [],
        "last_reflected_batch": "",
        "created_at": "2026-01-01",
        "updated_at": "2026-01-01",
    }


def _setup_paths(tmp_path: Path) -> StoragePaths:
    paths = StoragePaths(tmp_path / "storage")
    paths.ensure_dirs()
    return paths


class TestBatchFinalizer:
    def test_finalize_updates_cards_and_state(self, tmp_path: Path) -> None:
        paths = _setup_paths(tmp_path)
        save_yaml(paths.logic_card_file("L001"), _minimal_card("L001", "active"))
        save_yaml(paths.logic_card_file("L002"), _minimal_card("L002", "active"))
        StateStore(paths).save_state({"current_batch": "batch_002", "current_batch_phase": "judged"})
        save_yaml(
            paths.judge_report_file("batch_002"),
            {
                "batch_id": "batch_002",
                "candidate_verdicts": [
                    {"logic_id": "L001", "candidate_id": "C001", "verdict": "admit"},
                    {"logic_id": "L001", "candidate_id": "C002", "verdict": "reject"},
                    {"logic_id": "L002", "candidate_id": "C003", "verdict": "reject"},
                ],
                "logic_recommendations": {
                    "L001": {"recommended_status": "productive", "reason": "breakthrough"},
                    "L002": {"recommended_status": "parked", "reason": "pause"},
                },
                "logic_diagnostics": {
                    "L001": {
                        "thesis_update": "shadow x amihud works",
                        "failure_boundary": "Do not retry shadow x vol\nDo not retry shadow x turnover",
                        "next_best_probes": [{"expr": "ExprA()", "why": "test conditional route"}],
                    },
                    "L002": {
                        "thesis_update": "cross covariance absorbed by style",
                        "failure_boundary": "Do not retry amount x turnover covariance",
                        "next_best_probes": [],
                    },
                },
            },
        )

        result = BatchFinalizer(paths).finalize_batch("batch_002")

        card1 = load_yaml(paths.logic_card_file("L001"))
        card2 = load_yaml(paths.logic_card_file("L002"))
        state = StateStore(paths).load_state()

        assert result.updated_logic_ids == ["L001", "L002"]
        assert card1["status"] == "productive"
        assert "Do not retry shadow x vol" in card1["contract"]["avoid_patterns"]
        assert card1["next_actions"] == ["ExprA() — test conditional route"]
        assert card1["evidence_summary"]["factors_generated"] == 2
        assert card1["evidence_summary"]["factors_admitted"] == 1
        assert card2["status"] == "parked"
        assert state["active_logic_ids"] == []
        assert state["warm_logic_ids"] == []
        assert state["last_completed_batch"] == "batch_002"
        # productive logics should appear in schedulable_logic_ids
        assert "L001" in state["schedulable_logic_ids"]
        assert "L002" not in state["schedulable_logic_ids"]  # parked
        assert result.schedulable_logic_ids == state["schedulable_logic_ids"]


class TestStorageConsistencyChecker:
    def test_detects_status_mismatch(self, tmp_path: Path) -> None:
        paths = _setup_paths(tmp_path)
        save_yaml(paths.logic_card_file("L001"), _minimal_card("L001", "active"))
        StateStore(paths).save_state({"active_logic_ids": ["L001"], "warm_logic_ids": []})
        save_yaml(
            paths.judge_report_file("batch_002"),
            {"logic_recommendations": {"L001": {"recommended_status": "parked"}}},
        )

        report = StorageConsistencyChecker(paths).check(batch_id="batch_002")

        assert not report.ok
        assert any("status mismatch" in err for err in report.errors)
