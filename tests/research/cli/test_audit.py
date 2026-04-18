"""Tests for research audit mt-budget."""

from __future__ import annotations

from pathlib import Path

import pytest

from research.cli.audit import format_mt_budget_report
from research.storage.paths import StoragePaths
from research.storage.yaml_io import save_yaml


def _seed_config(paths: StoragePaths) -> None:
    save_yaml(
        paths.config_file,
        {
            "thresholds": {
                "mt_budget": {
                    "family_log_base": 600,
                    "direction_log_base": 80,
                    "exposure_divisor": 40,
                    "weights": {"family": 0.5, "direction": 0.3, "exposure": 0.2},
                    "bucket_low": 0.40,
                    "bucket_high": 0.70,
                    "adjusted_strength_discount": 0.50,
                }
            },
        },
    )


def _seed_batch(
    paths: StoragePaths,
    batch_id: str,
    direction: str,
    n_candidates: int,
    with_judge: bool = True,
) -> None:
    bdir = paths.batch_dir(batch_id)
    bdir.mkdir(parents=True, exist_ok=True)
    save_yaml(
        bdir / "manifest.yaml",
        {
            "batch_id": batch_id,
            "direction": direction,
            "candidates": [{"candidate_id": f"C{i:03d}"} for i in range(n_candidates)],
        },
    )
    if with_judge:
        (bdir / "judge.md").write_text("# judge\n")


class TestFormatMtBudgetReport:
    def test_empty_batches(self, tmp_path: Path) -> None:
        paths = StoragePaths(tmp_path)
        paths.ensure_dirs()
        _seed_config(paths)
        report = format_mt_budget_report(paths)
        assert "Cumulative candidates: 0" in report
        assert "Validation exposure: 0" in report
        assert "low" in report

    def test_populated_global(self, tmp_path: Path) -> None:
        paths = StoragePaths(tmp_path)
        paths.ensure_dirs()
        _seed_config(paths)
        _seed_batch(paths, "batch_001", "vol", 5)
        _seed_batch(paths, "batch_002", "mom", 6)
        report = format_mt_budget_report(paths)
        assert "Cumulative candidates: 11" in report
        assert "Validation exposure: 2" in report

    def test_direction_scoped(self, tmp_path: Path) -> None:
        paths = StoragePaths(tmp_path)
        paths.ensure_dirs()
        _seed_config(paths)
        _seed_batch(paths, "batch_001", "vol", 5)
        _seed_batch(paths, "batch_002", "mom", 6)
        _seed_batch(paths, "batch_003", "vol", 4)
        report = format_mt_budget_report(paths, direction="vol")
        assert "direction=vol" in report
        assert "Cumulative candidates (all directions): 15" in report
        assert "Direction candidates: 9" in report
