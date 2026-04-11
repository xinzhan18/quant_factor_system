"""End-to-end Phase 3 orchestrator tests using a fake LLM callback."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from research.checkpoints.audit import ALL_CHECKPOINTS, JudgeAuditError
from research.checkpoints.generator import PacketContext
from research.checkpoints.mt_budget import MtBudgetConfig
from research.phases.phase3_judge import (
    Phase3Inputs,
    run_phase3,
)
from research.storage.yaml_io import save_yaml


def _seed_result_yaml(
    batch_dir: Path,
    candidates: list[dict[str, Any]],
    sample_policy_version: str = "v3",
) -> None:
    batch_dir.mkdir(parents=True, exist_ok=True)
    save_yaml(
        batch_dir / "result.yaml",
        {
            "schema_version": "1",
            "batch_id": batch_dir.name,
            "sample_policy_version": sample_policy_version,
            "candidates": candidates,
        },
    )


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
                "q1": -0.003, "q2": -0.001, "q3": 0.0, "q4": 0.001, "q5": 0.004,
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


def _make_judge_md(
    candidates: list[dict[str, Any]],
    overrides: dict[str, Any] | None = None,
) -> str:
    """Build a well-formed judge.md that audit would accept."""
    overrides = overrides or {}
    fm_candidates = []
    for c in candidates:
        verdict = overrides.get("verdict", "admit")
        gate = overrides.get("hard_gate_result", "all_pass")
        fm_candidates.append(
            {
                "candidate_id": c["candidate_id"],
                "verdict": verdict,
                "hard_gate_result": gate,
                "checkpoint_positions": {
                    "CP01": "all_pass",
                    "CP02": "aligned",
                    "CP03": "strong",
                    "CP04": "acceptable",
                    "CP05": "low",
                    "CP06": "stable",
                },
                "referenced_context": [],
            }
        )
    summary = {
        "total": len(candidates),
        "admit": sum(1 for c in fm_candidates if c["verdict"] == "admit"),
        "reserve": sum(1 for c in fm_candidates if c["verdict"] == "reserve"),
        "reject": sum(1 for c in fm_candidates if c["verdict"] == "reject"),
    }
    fm = {
        "batch_id": "batch_test",
        "judged_at": "2026-04-12T10:00:00Z",
        "direction": "fp_divergence",
        "candidates": fm_candidates,
        "batch_summary": summary,
    }

    body_lines = ["# Judge Report", ""]
    for c in candidates:
        body_lines.extend([f"## {c['candidate_id']} — ADMIT", ""])
        for cp in ALL_CHECKPOINTS:
            body_lines.append(f"### {cp}")
            if cp == "CP03":
                body_lines.append(
                    "ICIR=0.338 with mt_bucket=low — search adjusted = 0.68 → strong"
                )
            else:
                body_lines.append(f"{cp} reasoning")
            body_lines.append("")
    return f"---\n{yaml.dump(fm, sort_keys=False)}\n---\n\n" + "\n".join(body_lines)


class TestPhase3EndToEnd:
    def test_happy_path_with_fake_llm(self, tmp_path: Path) -> None:
        batches_root = tmp_path / "batches"
        batch_dir = batches_root / "batch_test"
        _seed_result_yaml(batch_dir, [_good_candidate("C001")])

        inputs = Phase3Inputs(
            batch_id="batch_test",
            direction="fp_divergence",
            batch_dir=batch_dir,
            batches_root=batches_root,
            context=PacketContext(),
            current_sample_policy_version="v3",
            packet_refs=set(),
            mt_budget_config=MtBudgetConfig(),
        )

        def fake_llm(packet_text: str, judge_md_path: Path, refs: set[str]) -> None:
            # The LLM would read packet_text; our fake just confirms the
            # packet was rendered, then writes a canned judge.md
            assert "## Candidates" in packet_text
            assert "mt_bucket" in packet_text  # mt hint present in packet
            judge_md_path.write_text(_make_judge_md([_good_candidate("C001")]))

        result = run_phase3(inputs, fake_llm)

        assert result.packet_path.exists()
        assert result.judge_md_path.exists()
        assert result.gates[0].passed is True
        assert result.parsed.frontmatter["batch_id"] == "batch_test"
        assert result.parsed.frontmatter["candidates"][0]["verdict"] == "admit"

    def test_missing_result_yaml_raises(self, tmp_path: Path) -> None:
        batches_root = tmp_path / "batches"
        batch_dir = batches_root / "batch_empty"
        batch_dir.mkdir(parents=True)

        inputs = Phase3Inputs(
            batch_id="batch_empty",
            direction="fp",
            batch_dir=batch_dir,
            batches_root=batches_root,
            context=PacketContext(),
            current_sample_policy_version="v3",
        )

        def fake_llm(*_: Any) -> None:
            raise AssertionError("should not be called")

        with pytest.raises(FileNotFoundError, match="result.yaml missing"):
            run_phase3(inputs, fake_llm)

    def test_llm_writes_invalid_judge_audit_raises(self, tmp_path: Path) -> None:
        batches_root = tmp_path / "batches"
        batch_dir = batches_root / "batch_bad_llm"
        _seed_result_yaml(batch_dir, [_good_candidate("C001")])

        inputs = Phase3Inputs(
            batch_id="batch_bad_llm",
            direction="fp",
            batch_dir=batch_dir,
            batches_root=batches_root,
            context=PacketContext(),
            current_sample_policy_version="v3",
        )

        def naughty_llm(packet_text: str, judge_md_path: Path, refs: set[str]) -> None:
            # LLM writes a judge.md that omits mt_bucket from CP03
            fm = {
                "batch_id": "batch_bad_llm",
                "candidates": [
                    {
                        "candidate_id": "C001",
                        "verdict": "admit",
                        "hard_gate_result": "all_pass",
                    }
                ],
                "batch_summary": {"total": 1, "admit": 1, "reserve": 0, "reject": 0},
            }
            lines = ["## C001 — ADMIT", ""]
            for cp in ALL_CHECKPOINTS:
                lines.append(f"### {cp}")
                lines.append("reasoning")  # no mt_bucket in CP03
                lines.append("")
            body = "\n".join(lines)
            judge_md_path.write_text(
                f"---\n{yaml.dump(fm)}\n---\n\n{body}"
            )

        with pytest.raises(JudgeAuditError, match="mt_bucket"):
            run_phase3(inputs, naughty_llm)

    def test_hard_gate_fail_still_packs(self, tmp_path: Path) -> None:
        """Candidates that fail hard gates should still appear in the packet,
        so the LLM sees the reject reasons."""
        batches_root = tmp_path / "batches"
        batch_dir = batches_root / "batch_hg"
        bad = _good_candidate("C001")
        bad["coverage"] = 0.3  # hard gate fail
        _seed_result_yaml(batch_dir, [bad])

        inputs = Phase3Inputs(
            batch_id="batch_hg",
            direction="fp",
            batch_dir=batch_dir,
            batches_root=batches_root,
            context=PacketContext(),
            current_sample_policy_version="v3",
        )

        captured: dict[str, Any] = {}

        def fake_llm(packet_text: str, judge_md_path: Path, refs: set[str]) -> None:
            captured["packet"] = packet_text
            # LLM must reject the candidate — and that's OK for audit
            judge_md_path.write_text(
                _make_judge_md(
                    [_good_candidate("C001")],
                    overrides={
                        "verdict": "reject",
                        "hard_gate_result": "coverage 0.3 < 0.8",
                    },
                )
            )

        result = run_phase3(inputs, fake_llm)

        # Gate reported failure
        assert result.gates[0].passed is False
        assert any("coverage" in r for r in result.gates[0].reasons)
        # Packet includes the rejection reason for LLM visibility
        assert "coverage" in captured["packet"]
        # Final verdict is reject (hard gate cannot be overridden)
        assert result.parsed.frontmatter["candidates"][0]["verdict"] == "reject"

    def test_cleanup_packet_true_removes_file(self, tmp_path: Path) -> None:
        batches_root = tmp_path / "batches"
        batch_dir = batches_root / "batch_clean"
        _seed_result_yaml(batch_dir, [_good_candidate("C001")])

        inputs = Phase3Inputs(
            batch_id="batch_clean",
            direction="fp_divergence",
            batch_dir=batch_dir,
            batches_root=batches_root,
            context=PacketContext(),
            current_sample_policy_version="v3",
            cleanup_packet=True,
        )

        def fake_llm(packet_text: str, judge_md_path: Path, refs: set[str]) -> None:
            judge_md_path.write_text(_make_judge_md([_good_candidate("C001")]))

        result = run_phase3(inputs, fake_llm)
        assert result.judge_md_path.exists()
        assert not result.packet_path.exists()  # cleaned up
