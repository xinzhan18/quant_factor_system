"""Tests for §7.MT multiple testing budget."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

from research.checkpoints.mt_budget import (
    MtBudgetConfig,
    MtCounts,
    _bucket_from_score,
    _raw_mt_score,
    _search_adjusted_strength,
    compute_mt_budget,
    scan_batches_for_mt,
)
from research.storage.yaml_io import save_yaml


def _make_batch(
    root: Path,
    batch_id: str,
    direction: str,
    n_candidates: int,
    with_judge_md: bool,
) -> None:
    """Create a minimal batch directory for the scanner to walk."""
    bdir = root / batch_id
    bdir.mkdir(parents=True, exist_ok=True)
    manifest = {
        "batch_id": batch_id,
        "direction": direction,
        "candidates": [{"candidate_id": f"C{i:03d}"} for i in range(n_candidates)],
    }
    save_yaml(bdir / "manifest.yaml", manifest)
    if with_judge_md:
        (bdir / "judge.md").write_text("# judge\n", encoding="utf-8")


class TestScanBatchesForMt:
    def test_missing_batches_dir_returns_zero(self, tmp_path: Path) -> None:
        counts = scan_batches_for_mt(
            tmp_path / "nope",
            current_batch_id="batch_001",
            current_direction="fp",
        )
        assert counts == MtCounts(0, 0, 0, 0)

    def test_empty_batches_dir_returns_zero(self, tmp_path: Path) -> None:
        (tmp_path / "batches").mkdir()
        counts = scan_batches_for_mt(
            tmp_path / "batches",
            current_batch_id="batch_001",
            current_direction="fp",
        )
        assert counts == MtCounts(0, 0, 0, 0)

    def test_counts_judged_only(self, tmp_path: Path) -> None:
        root = tmp_path / "batches"
        root.mkdir()
        _make_batch(root, "batch_001", "fp", 5, with_judge_md=True)
        _make_batch(root, "batch_002", "fp", 6, with_judge_md=False)
        _make_batch(root, "batch_003", "fp", 4, with_judge_md=True)

        counts = scan_batches_for_mt(
            root,
            current_batch_id="batch_100",
            current_direction="fp",
        )
        assert counts.cumulative_candidates == 5 + 4
        assert counts.n_batches_scanned == 2
        assert counts.validation_exposure == 2

    def test_skips_current_and_later_batches(self, tmp_path: Path) -> None:
        root = tmp_path / "batches"
        root.mkdir()
        _make_batch(root, "batch_001", "fp", 3, with_judge_md=True)
        _make_batch(root, "batch_002", "fp", 4, with_judge_md=True)
        _make_batch(root, "batch_003", "fp", 5, with_judge_md=True)

        counts = scan_batches_for_mt(
            root,
            current_batch_id="batch_002",
            current_direction="fp",
        )
        assert counts.cumulative_candidates == 3
        assert counts.n_batches_scanned == 1

    def test_direction_filtering(self, tmp_path: Path) -> None:
        root = tmp_path / "batches"
        root.mkdir()
        _make_batch(root, "batch_001", "fp", 4, with_judge_md=True)
        _make_batch(root, "batch_002", "momentum", 6, with_judge_md=True)
        _make_batch(root, "batch_003", "fp", 5, with_judge_md=True)

        counts = scan_batches_for_mt(
            root,
            current_batch_id="batch_100",
            current_direction="fp",
        )
        assert counts.cumulative_candidates == 4 + 6 + 5
        assert counts.direction_candidates == 4 + 5


class TestMtBudgetConfig:
    def test_default_values(self) -> None:
        cfg = MtBudgetConfig()
        assert cfg.family_log_base == 600
        assert cfg.direction_log_base == 80
        assert cfg.exposure_divisor == 40
        assert cfg.weight_family + cfg.weight_direction + cfg.weight_exposure == pytest.approx(1.0)
        assert cfg.bucket_low == 0.40
        assert cfg.bucket_high == 0.70
        assert cfg.adjusted_strength_discount == 0.50

    def test_from_config_dict(self) -> None:
        cfg_dict = {
            "family_log_base": 800,
            "direction_log_base": 100,
            "exposure_divisor": 50,
            "weights": {"family": 0.6, "direction": 0.2, "exposure": 0.2},
            "bucket_low": 0.35,
            "bucket_high": 0.75,
            "adjusted_strength_discount": 0.40,
        }
        cfg = MtBudgetConfig.from_config_dict(cfg_dict)
        assert cfg.family_log_base == 800
        assert cfg.weight_family == 0.6
        assert cfg.bucket_low == 0.35


class TestRawMtScore:
    def test_zero_counts_gives_zero_score(self) -> None:
        counts = MtCounts(0, 0, 0, 0)
        cfg = MtBudgetConfig()
        raw = _raw_mt_score(counts, cfg)
        assert raw["score"] == 0.0
        assert raw["terms"]["family"] == 0.0
        assert raw["terms"]["direction"] == 0.0
        assert raw["terms"]["exposure"] == 0.0

    def test_small_counts_low_score(self) -> None:
        counts = MtCounts(5, 2, 1, 1)
        cfg = MtBudgetConfig()
        raw = _raw_mt_score(counts, cfg)
        assert 0.15 < raw["score"] < 0.25

    def test_saturated_counts_clip_to_one(self) -> None:
        counts = MtCounts(5000, 500, 200, 50)
        cfg = MtBudgetConfig()
        raw = _raw_mt_score(counts, cfg)
        assert raw["terms"]["family"] == 1.0
        assert raw["terms"]["direction"] == 1.0
        assert raw["terms"]["exposure"] == 1.0
        assert raw["score"] == pytest.approx(1.0)


class TestBucketFromScore:
    @pytest.mark.parametrize(
        "score,expected",
        [
            (0.0, "low"),
            (0.39, "low"),
            (0.40, "medium"),
            (0.55, "medium"),
            (0.70, "medium"),
            (0.71, "high"),
            (1.0, "high"),
        ],
    )
    def test_bucket_boundaries(self, score: float, expected: str) -> None:
        cfg = MtBudgetConfig()
        assert _bucket_from_score(score, cfg) == expected


class TestSearchAdjustedStrength:
    def test_strong_metrics_no_discount_gives_high(self) -> None:
        result = _search_adjusted_strength(
            ic_mean=0.03,
            ic_ir=0.25,
            mono=0.5,
            expanding_pass=True,
            mt_score=0.0,
            discount=0.5,
        )
        assert result["raw"] == pytest.approx(1.0, abs=0.001)
        assert result["adjusted"] == pytest.approx(1.0, abs=0.001)
        assert result["bucket"] == "high"

    def test_mt_score_discounts_adjusted(self) -> None:
        result = _search_adjusted_strength(
            ic_mean=0.02,
            ic_ir=0.20,
            mono=0.40,
            expanding_pass=True,
            mt_score=1.0,
            discount=0.5,
        )
        assert result["adjusted"] == pytest.approx(0.5, abs=0.01)
        assert result["bucket"] == "medium"

    def test_nan_inputs_treated_as_zero(self) -> None:
        result = _search_adjusted_strength(
            ic_mean=float("nan"),
            ic_ir=float("nan"),
            mono=float("nan"),
            expanding_pass=False,
            mt_score=0.0,
            discount=0.5,
        )
        assert result["raw"] == 0.0
        assert result["adjusted"] == 0.0
        assert result["bucket"] == "low"


class TestComputeMtBudget:
    def test_full_hint_shape(self) -> None:
        counts = MtCounts(
            cumulative_candidates=612,
            direction_candidates=47,
            validation_exposure=5,
            n_batches_scanned=102,
        )
        cfg = MtBudgetConfig()
        hint = compute_mt_budget(
            counts,
            cfg,
            ic_mean=0.016,
            ic_ir=0.338,
            monotonicity=0.85,
            expanding_pass=True,
        )
        assert "mt_score" in hint
        assert "mt_bucket" in hint
        assert "search_adjusted_strength" in hint
        assert "mt_breakdown" in hint

        assert hint["mt_bucket"] in ("low", "medium", "high")

        bd = hint["mt_breakdown"]
        assert bd["cumulative_candidates"] == 612
        assert bd["direction_candidates"] == 47
        assert bd["validation_exposure"] == 5
        assert bd["n_batches_scanned"] == 102
        assert "family" in bd["terms"]
        assert "direction" in bd["terms"]
        assert "exposure" in bd["terms"]

        sas = hint["search_adjusted_strength"]
        assert "raw" in sas
        assert "adjusted" in sas
        assert sas["adjusted"] <= sas["raw"]

    def test_high_cumulative_pushes_to_medium_or_high_bucket(self) -> None:
        counts = MtCounts(
            cumulative_candidates=1000,
            direction_candidates=100,
            validation_exposure=20,
            n_batches_scanned=180,
        )
        hint = compute_mt_budget(counts, MtBudgetConfig(), ic_mean=0.01, ic_ir=0.1)
        assert hint["mt_bucket"] in ("medium", "high")
