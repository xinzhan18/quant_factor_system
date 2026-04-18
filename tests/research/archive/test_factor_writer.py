"""Tests for factor_writer allocation + yaml write."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from research.archive.factor_writer import (
    FIRST_FACTOR_ID,
    FactorAllocationError,
    allocate_and_write_factor,
    allocate_next_factor_id,
    build_factor_record,
    scan_existing_factor_ids,
    write_factor_yaml,
)
from research.storage.yaml_io import load_yaml, save_yaml


def _candidate(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "candidate_id": "C001",
        "source_type": "dsl",
        "expression": "Std($close, 20)",
        "ic": {
            "validation": {"ic_mean": 0.016, "ic_ir": 0.338, "ic_win_rate": 0.6}
        },
        "quintile": {
            "validation": {
                "monotonicity": 0.95,
                "ls_mean": 0.007,
            },
        },
        "barra": {"style_r_squared": 0.08, "alpha_survival_ratio": 0.81},
    }
    base.update(overrides)
    return base


def _manifest_entry(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "candidate_id": "C001",
        "source_type": "dsl",
        "expression": "Std($close, 20)",
        "canonical": "Std($close,20)",
    }
    base.update(overrides)
    return base


class TestScanExistingFactorIds:
    def test_empty_dir(self, tmp_path: Path) -> None:
        d = tmp_path / "factors"
        assert scan_existing_factor_ids(d) == set()

    def test_missing_dir(self, tmp_path: Path) -> None:
        assert scan_existing_factor_ids(tmp_path / "absent") == set()

    def test_parses_ids(self, tmp_path: Path) -> None:
        d = tmp_path / "factors"
        d.mkdir()
        for name in ["F001.yaml", "F002.yaml", "F025.yaml", ".DS_Store", "notes.md"]:
            (d / name).write_text("")
        assert scan_existing_factor_ids(d) == {1, 2, 25}


class TestAllocateNextFactorId:
    def test_empty_vault_starts_at_first(self, tmp_path: Path) -> None:
        assert allocate_next_factor_id(tmp_path / "factors") == f"F{FIRST_FACTOR_ID:03d}"

    def test_monotonic_from_existing(self, tmp_path: Path) -> None:
        d = tmp_path / "factors"
        d.mkdir()
        (d / "F001.yaml").write_text("")
        (d / "F025.yaml").write_text("")
        assert allocate_next_factor_id(d) == "F026"

    def test_id_never_reused(self, tmp_path: Path) -> None:
        d = tmp_path / "factors"
        d.mkdir()
        (d / "F001.yaml").write_text("")
        # Skipped ids don't get filled — we always go past the max
        (d / "F030.yaml").write_text("")
        assert allocate_next_factor_id(d) == "F031"


class TestBuildFactorRecord:
    def test_dsl_record_shape(self) -> None:
        rec = build_factor_record(
            factor_id="F001",
            admit_entry=_candidate(),
            manifest_entry=_manifest_entry(),
            batch_id="batch_001",
            direction="volatility",
        )
        assert rec["factor_id"] == "F001"
        assert rec["family_tag"] == "volatility"
        assert rec["source_type"] == "dsl"
        assert rec["expression"] == "Std($close, 20)"
        assert rec["canonical"] == "Std($close,20)"
        assert rec["status"] == "active"
        assert rec["admitted_in_batch"] == "batch_001"
        assert rec["validation_metrics"]["ic_mean"] == 0.016
        assert rec["risk_metrics"]["style_r_squared"] == 0.08

    def test_diagnostics_ref_from_admit_entry(self) -> None:
        rec = build_factor_record(
            factor_id="F001",
            admit_entry=_candidate(diagnostics_relpath="cache/batch_diagnostics/batch_001/C001"),
            manifest_entry=_manifest_entry(),
            batch_id="batch_001",
            direction="vol",
        )
        assert rec["diagnostics_ref"] == "cache/batch_diagnostics/batch_001/C001"
        assert "signal_ref" not in rec

    def test_diagnostics_ref_falls_back_to_canonical_path(self) -> None:
        rec = build_factor_record(
            factor_id="F001",
            admit_entry=_candidate(),  # no diagnostics_relpath
            manifest_entry=_manifest_entry(),
            batch_id="batch_001",
            direction="vol",
        )
        assert rec["diagnostics_ref"] == "cache/batch_diagnostics/batch_001/C001"

    def test_factor_name_override_from_llm(self) -> None:
        rec = build_factor_record(
            factor_id="F001",
            admit_entry=_candidate(),
            manifest_entry=_manifest_entry(),
            batch_id="batch_001",
            direction="vol",
            factor_name="pv_corr_20d_vol20d",
        )
        assert rec["name"] == "pv_corr_20d_vol20d"

    def test_name_falls_back_to_factor_id(self) -> None:
        rec = build_factor_record(
            factor_id="F001",
            admit_entry=_candidate(),
            manifest_entry=_manifest_entry(),
            batch_id="batch_001",
            direction="vol",
        )
        assert rec["name"] == "F001"

    def test_python_record_shape(self) -> None:
        rec = build_factor_record(
            factor_id="F001",
            admit_entry=_candidate(source_type="python"),
            manifest_entry=_manifest_entry(
                source_type="python", path="storage/batches/batch_001/python_candidates/C001.py"
            ),
            batch_id="batch_001",
            direction="structural",
        )
        assert rec["source_type"] == "python"
        assert rec["python_path"].endswith("C001.py")


class TestWriteFactorYaml:
    def test_writes_and_reads_back(self, tmp_path: Path) -> None:
        rec = build_factor_record(
            "F001", _candidate(), _manifest_entry(), "batch_001", "vol"
        )
        path = write_factor_yaml(tmp_path / "factors", rec)
        assert path.exists()
        loaded = load_yaml(path)
        assert loaded["factor_id"] == "F001"

    def test_rejects_overwrite(self, tmp_path: Path) -> None:
        d = tmp_path / "factors"
        d.mkdir()
        (d / "F001.yaml").write_text("existing")

        rec = build_factor_record(
            "F001", _candidate(), _manifest_entry(), "batch_001", "vol"
        )
        with pytest.raises(FactorAllocationError, match="already exists"):
            write_factor_yaml(d, rec)


class TestAllocateAndWrite:
    def test_end_to_end(self, tmp_path: Path) -> None:
        allocated = allocate_and_write_factor(
            factors_dir=tmp_path / "factors",
            admit_entry=_candidate(),
            manifest_entry=_manifest_entry(),
            batch_id="batch_001",
            direction="vol",
        )
        assert allocated.factor_id == "F001"
        assert allocated.yaml_path.exists()
        assert allocated.record["factor_id"] == "F001"

    def test_sequential_allocation(self, tmp_path: Path) -> None:
        a1 = allocate_and_write_factor(
            factors_dir=tmp_path / "factors",
            admit_entry=_candidate(candidate_id="C001"),
            manifest_entry=_manifest_entry(candidate_id="C001"),
            batch_id="batch_001",
            direction="vol",
        )
        a2 = allocate_and_write_factor(
            factors_dir=tmp_path / "factors",
            admit_entry=_candidate(candidate_id="C002"),
            manifest_entry=_manifest_entry(candidate_id="C002"),
            batch_id="batch_001",
            direction="vol",
        )
        assert a1.factor_id == "F001"
        assert a2.factor_id == "F002"
