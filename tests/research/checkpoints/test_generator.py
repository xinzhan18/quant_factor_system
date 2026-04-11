"""Tests for checkpoints.generator.build_judge_packet."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from research.checkpoints.generator import (
    PacketContext,
    PacketInputs,
    build_judge_packet,
    write_judge_packet,
)
from research.checkpoints.mt_budget import MtBudgetConfig
from research.storage.yaml_io import save_yaml


def _make_result(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "schema_version": "1",
        "batch_id": "batch_042",
        "sample_policy_version": "v3",
        "candidates": candidates,
    }


def _good_candidate(cid: str = "C001") -> dict[str, Any]:
    return {
        "candidate_id": cid,
        "expression": "Std($close, 20)",
        "source_type": "dsl",
        "coverage": 0.95,
        "sign": 1,
        "compute_error": None,
        "effect_strength": {
            "train": {"ic_mean": 0.018, "ic_ir": 0.30, "ic_win_rate": 0.58},
            "validation": {"ic_mean": 0.016, "ic_ir": 0.338, "ic_win_rate": 0.60},
        },
        "quintile": {
            "quintile_returns_validation": {
                "q1": -0.003,
                "q2": -0.001,
                "q3": 0.0,
                "q4": 0.001,
                "q5": 0.004,
            },
            "monotonicity_validation": 0.95,
            "long_short_mean_validation": 0.007,
            "long_short_n_days": 240,
        },
        "stability": {
            "split_stability": {
                "bucket": "high",
                "sign_consistency": 1.0,
                "dispersion": 0.3,
            },
            "sign_consistency_train_validation": True,
            "train_validation_decay": 0.89,
            "expanding_window": {"pass": True},
        },
        "redundancy": {
            "max_lib_corr": 0.3,
            "nearest_factor_id": "F012",
            "exceeds_threshold": False,
        },
        "feasibility": {"turnover_mean": 1.2},
        "barra": {
            "style_r_squared": 0.08,
            "barra_residual_ic": 0.013,
            "alpha_survival_ratio": 0.81,
            "dominant_style_exposure": "vol_20d",
            "style_crowding_risk": "low",
        },
    }


def _bare_inputs(
    batches_dir: Path,
    candidates: list[dict[str, Any]] | None = None,
) -> PacketInputs:
    return PacketInputs(
        batch_id="batch_042",
        direction="fp_divergence",
        result=_make_result(candidates or [_good_candidate()]),
        context=PacketContext(
            direction_excerpt="Hypothesis: value × fundamentals improving",
            lessons_excerpt="- no short-side\n- market_cap guardrail 0.3",
            nearest_factor_excerpt="F012 summary …",
        ),
        current_sample_policy_version="v3",
        batches_dir=batches_dir,
        mt_budget_config=MtBudgetConfig(),
    )


class TestBuildJudgePacket:
    def test_frontmatter_fields(self, tmp_path: Path) -> None:
        packet = build_judge_packet(_bare_inputs(tmp_path / "batches"))
        assert packet.startswith("---\n")
        assert "batch_id: batch_042" in packet
        assert "direction: fp_divergence" in packet
        assert "n_candidates: 1" in packet
        assert "sample_policy_version: v3" in packet
        assert "mt_budget:" in packet

    def test_context_sections_rendered(self, tmp_path: Path) -> None:
        packet = build_judge_packet(_bare_inputs(tmp_path / "batches"))
        assert "## Direction Context" in packet
        assert "Hypothesis: value × fundamentals improving" in packet
        assert "## Lessons Excerpt" in packet
        assert "no short-side" in packet
        assert "## Nearest Library Factor" in packet
        assert "F012 summary" in packet

    def test_empty_context_sections_skipped(self, tmp_path: Path) -> None:
        inputs = _bare_inputs(tmp_path / "batches")
        inputs.context = PacketContext()  # all empty
        packet = build_judge_packet(inputs)
        assert "## Direction Context" not in packet
        assert "## Lessons Excerpt" not in packet
        assert "## Nearest Library Factor" not in packet

    def test_candidate_hard_gate_pass(self, tmp_path: Path) -> None:
        packet = build_judge_packet(_bare_inputs(tmp_path / "batches"))
        assert "### C001" in packet
        assert "Hard Gate (CP01)**: `all_pass`" in packet
        # numeric hints included
        assert "CP03" in packet
        assert "mt_bucket" in packet
        assert "CP04" in packet

    def test_candidate_hard_gate_fail_omits_numeric(
        self, tmp_path: Path
    ) -> None:
        bad = _good_candidate("C001")
        bad["compute_error"] = "ValueError: empty"
        packet = build_judge_packet(
            _bare_inputs(tmp_path / "batches", candidates=[bad])
        )
        assert "reject" in packet
        assert "compute_error" in packet
        assert "Numeric hints omitted" in packet

    def test_mt_budget_hint_included_per_candidate(self, tmp_path: Path) -> None:
        packet = build_judge_packet(_bare_inputs(tmp_path / "batches"))
        # Each good candidate should have the mt_bucket string rendered
        # inline — this is what audit.py grep-checks.
        assert "mt_bucket" in packet
        assert "search_adjusted" in packet

    def test_multiple_candidates(self, tmp_path: Path) -> None:
        cs = [_good_candidate("C001"), _good_candidate("C002"), _good_candidate("C003")]
        packet = build_judge_packet(
            _bare_inputs(tmp_path / "batches", candidates=cs)
        )
        assert "### C001" in packet
        assert "### C002" in packet
        assert "### C003" in packet
        assert "n_candidates: 3" in packet


class TestMtCountsFromBatches:
    def _seed_batches(self, root: Path) -> None:
        root.mkdir(parents=True, exist_ok=True)
        for i in range(3):
            bid = f"batch_{i:03d}"
            bdir = root / bid
            bdir.mkdir()
            save_yaml(
                bdir / "manifest.yaml",
                {
                    "batch_id": bid,
                    "direction": "fp_divergence",
                    "sample_policy_version": "v3",
                    "candidates": [{"candidate_id": f"C{j:03d}"} for j in range(5)],
                },
            )
            (bdir / "judge.md").write_text("# judge\n")

    def test_frontmatter_reflects_historical_counts(
        self, tmp_path: Path
    ) -> None:
        batches_dir = tmp_path / "batches"
        self._seed_batches(batches_dir)

        inputs = _bare_inputs(batches_dir)
        packet = build_judge_packet(inputs)

        # 3 batches × 5 candidates = 15
        assert "cumulative_candidates: 15" in packet
        assert "direction_candidates: 15" in packet
        assert "validation_exposure: 3" in packet


class TestWriteJudgePacket:
    def test_write_creates_file_and_dirs(self, tmp_path: Path) -> None:
        inputs = _bare_inputs(tmp_path / "batches")
        out = tmp_path / "nested" / "_packets" / "judge_packet.md"
        text = write_judge_packet(inputs, out)
        assert out.exists()
        assert out.read_text(encoding="utf-8") == text
