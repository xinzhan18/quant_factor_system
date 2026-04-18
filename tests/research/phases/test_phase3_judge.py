"""Tests for the Phase 3 pre-hint orchestrator."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from research.phases.phase3_judge import (
    Phase3PreHintInputs,
    run_phase3_prehint,
)
from research.storage.yaml_io import save_yaml


def _seed_result_yaml(batch_dir: Path, candidates: list[dict[str, Any]]) -> None:
    batch_dir.mkdir(parents=True, exist_ok=True)
    save_yaml(
        batch_dir / "result.yaml",
        {"batch_id": batch_dir.name, "candidates": candidates},
    )


def _good_candidate(cid: str = "C001", coverage: float = 0.95) -> dict[str, Any]:
    return {
        "candidate_id": cid,
        "expression": "Std($close, 20)",
        "source_type": "dsl",
        "coverage": coverage,
        "compute_error": None,
        "ic": {
            "train": {"ic_mean": 0.015, "ic_ir": 0.32},
            "validation": {"ic_mean": 0.013, "ic_ir": 0.30},
            "train_validation_decay": 0.87,
        },
        "quintile": {
            "train": {"monotonicity": 0.95},
            "validation": {"monotonicity": 0.92},
        },
    }


class TestPhase3PreHint:
    def test_writes_hints_file(self, tmp_path: Path) -> None:
        batches_root = tmp_path / "batches"
        batch_dir = batches_root / "batch_001"
        _seed_result_yaml(batch_dir, [_good_candidate("C001")])

        inputs = Phase3PreHintInputs(
            batch_id="batch_001",
            direction="timing_signals",
            batch_dir=batch_dir,
            batches_root=batches_root,
            hints_path=batch_dir / "_hints.yaml",
        )
        result = run_phase3_prehint(inputs)

        assert result.hints_path.exists()
        loaded = yaml.safe_load(result.hints_path.read_text(encoding="utf-8"))
        assert loaded["batch_id"] == "batch_001"
        assert "C001" in loaded["per_candidate"]
        assert loaded["per_candidate"]["C001"]["hard_gate"]["passed"] is True
        assert "mt_budget" in loaded["per_candidate"]["C001"]

    def test_raises_when_result_missing(self, tmp_path: Path) -> None:
        batches_root = tmp_path / "batches"
        batch_dir = batches_root / "batch_001"
        batch_dir.mkdir(parents=True)
        # no result.yaml written

        inputs = Phase3PreHintInputs(
            batch_id="batch_001",
            direction="timing_signals",
            batch_dir=batch_dir,
            batches_root=batches_root,
            hints_path=batch_dir / "_hints.yaml",
        )
        with pytest.raises(FileNotFoundError, match="result.yaml missing"):
            run_phase3_prehint(inputs)

    def test_hard_gate_fail_omits_mt_budget(self, tmp_path: Path) -> None:
        batches_root = tmp_path / "batches"
        batch_dir = batches_root / "batch_001"
        _seed_result_yaml(
            batch_dir,
            [_good_candidate("C001", coverage=0.5)],  # fails coverage gate
        )

        inputs = Phase3PreHintInputs(
            batch_id="batch_001",
            direction="timing_signals",
            batch_dir=batch_dir,
            batches_root=batches_root,
            hints_path=batch_dir / "_hints.yaml",
        )
        result = run_phase3_prehint(inputs)
        entry = result.hints["per_candidate"]["C001"]
        assert entry["hard_gate"]["passed"] is False
        assert "mt_budget" not in entry

    def test_multiple_candidates_each_indexed(self, tmp_path: Path) -> None:
        batches_root = tmp_path / "batches"
        batch_dir = batches_root / "batch_001"
        _seed_result_yaml(
            batch_dir,
            [
                _good_candidate("C001"),
                _good_candidate("C002"),
                _good_candidate("C003", coverage=0.5),
            ],
        )

        inputs = Phase3PreHintInputs(
            batch_id="batch_001",
            direction="timing_signals",
            batch_dir=batch_dir,
            batches_root=batches_root,
            hints_path=batch_dir / "_hints.yaml",
        )
        result = run_phase3_prehint(inputs)
        assert set(result.hints["per_candidate"].keys()) == {"C001", "C002", "C003"}
        # Passing candidates have mt_budget
        assert "mt_budget" in result.hints["per_candidate"]["C001"]
        assert "mt_budget" in result.hints["per_candidate"]["C002"]
        # Failing candidate omits mt_budget
        assert "mt_budget" not in result.hints["per_candidate"]["C003"]
