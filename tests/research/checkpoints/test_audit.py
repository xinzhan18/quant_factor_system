"""Tests for checkpoints.audit — the 6 structural checks on judge.md."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from research.checkpoints.audit import (
    ALL_CHECKPOINTS,
    JudgeAuditError,
    audit_judge_md,
    parse_judge_md,
)


def _write_judge(
    tmp_path: Path,
    frontmatter: dict[str, Any],
    body: str = "",
) -> Path:
    fm_text = yaml.dump(frontmatter, sort_keys=False, allow_unicode=True)
    full = f"---\n{fm_text.strip()}\n---\n\n{body}"
    p = tmp_path / "judge.md"
    p.write_text(full, encoding="utf-8")
    return p


def _good_frontmatter() -> dict[str, Any]:
    return {
        "batch_id": "batch_042",
        "judged_at": "2026-04-12T10:00:00Z",
        "direction": "fp_divergence",
        "candidates": [
            {
                "candidate_id": "C001",
                "verdict": "admit",
                "hard_gate_result": "all_pass",
                "checkpoint_positions": {
                    "CP01": "all_pass",
                    "CP02": "aligned",
                    "CP03": "strong",
                    "CP04": "acceptable",
                    "CP05": "low",
                    "CP06": "stable",
                },
                "referenced_context": [
                    "directions/fp_divergence.md#Hypothesis",
                ],
            },
        ],
        "batch_summary": {
            "total": 1,
            "admit": 1,
            "reserve": 0,
            "reject": 0,
        },
    }


def _good_body() -> str:
    lines = ["# Judge Report — batch_042", "", "## C001 — ADMIT", ""]
    for cp in ALL_CHECKPOINTS:
        lines.append(f"### {cp}")
        if cp == "CP03":
            lines.append(
                "ICIR_val=0.338, ls_tstat=3.89, mt_bucket=medium, "
                "search_adjusted=0.41 → strong"
            )
        else:
            lines.append(f"{cp} reasoning goes here.")
        lines.append("")
    return "\n".join(lines)


class TestParseJudgeMd:
    def test_missing_frontmatter_fence_raises(self) -> None:
        with pytest.raises(JudgeAuditError, match="frontmatter fence"):
            parse_judge_md("# just a title\n")

    def test_invalid_yaml_raises(self) -> None:
        with pytest.raises(JudgeAuditError, match="YAML parse"):
            parse_judge_md("---\nbatch_id: batch_1\n  broken: [unclosed\n---\nbody")

    def test_non_mapping_frontmatter_raises(self) -> None:
        with pytest.raises(JudgeAuditError, match="mapping"):
            parse_judge_md("---\n- just\n- a list\n---\nbody")

    def test_good_parse(self) -> None:
        parsed = parse_judge_md(
            f"---\n{yaml.dump(_good_frontmatter())}\n---\n{_good_body()}"
        )
        assert parsed.frontmatter["batch_id"] == "batch_042"
        assert "## C001" in parsed.body


class TestAuditGoodFile:
    def test_clean_judge_passes(self, tmp_path: Path) -> None:
        path = _write_judge(tmp_path, _good_frontmatter(), _good_body())
        parsed = audit_judge_md(path)
        assert parsed.frontmatter["batch_id"] == "batch_042"

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(JudgeAuditError, match="not found"):
            audit_judge_md(tmp_path / "nope.md")


class TestFrontmatterSchema:
    def test_missing_batch_id(self, tmp_path: Path) -> None:
        fm = _good_frontmatter()
        del fm["batch_id"]
        path = _write_judge(tmp_path, fm, _good_body())
        with pytest.raises(JudgeAuditError, match="batch_id"):
            audit_judge_md(path)

    def test_missing_batch_summary(self, tmp_path: Path) -> None:
        fm = _good_frontmatter()
        del fm["batch_summary"]
        path = _write_judge(tmp_path, fm, _good_body())
        with pytest.raises(JudgeAuditError, match="batch_summary"):
            audit_judge_md(path)

    def test_candidate_missing_verdict(self, tmp_path: Path) -> None:
        fm = _good_frontmatter()
        del fm["candidates"][0]["verdict"]
        path = _write_judge(tmp_path, fm, _good_body())
        with pytest.raises(JudgeAuditError, match="verdict"):
            audit_judge_md(path)


class TestVerdictEnum:
    def test_invalid_verdict_rejected(self, tmp_path: Path) -> None:
        fm = _good_frontmatter()
        fm["candidates"][0]["verdict"] = "maybe"
        path = _write_judge(tmp_path, fm, _good_body())
        with pytest.raises(JudgeAuditError, match="invalid verdict"):
            audit_judge_md(path)


class TestHardGateNotOverridden:
    def test_hard_gate_fail_with_admit_raises(self, tmp_path: Path) -> None:
        fm = _good_frontmatter()
        fm["candidates"][0]["hard_gate_result"] = "coverage 0.5 < 0.8"
        # verdict still admit → must raise
        path = _write_judge(tmp_path, fm, _good_body())
        with pytest.raises(JudgeAuditError, match="cannot be overridden"):
            audit_judge_md(path)

    def test_hard_gate_fail_with_reject_passes(self, tmp_path: Path) -> None:
        fm = _good_frontmatter()
        fm["candidates"][0]["hard_gate_result"] = "coverage 0.5 < 0.8"
        fm["candidates"][0]["verdict"] = "reject"
        fm["batch_summary"] = {"total": 1, "admit": 0, "reserve": 0, "reject": 1}
        # Reject body only needs CP01
        body = "## C001 — REJECT\n\n### CP01\nall_pass\n"
        path = _write_judge(tmp_path, fm, body)
        audit_judge_md(path)  # should not raise


class TestBodySections:
    def test_missing_h2_for_candidate(self, tmp_path: Path) -> None:
        fm = _good_frontmatter()
        # body has no H2 for C001
        body = "# header only\n\nno candidate section"
        path = _write_judge(tmp_path, fm, body)
        with pytest.raises(JudgeAuditError, match="H2 section"):
            audit_judge_md(path)

    def test_missing_cp_section_in_non_reject(self, tmp_path: Path) -> None:
        fm = _good_frontmatter()
        # Body has H2 but only CP01-CP05 — CP06 missing
        lines = ["## C001 — ADMIT", ""]
        for cp in ALL_CHECKPOINTS[:-1]:
            lines.append(f"### {cp}")
            if cp == "CP03":
                lines.append("mt_bucket=medium")
            else:
                lines.append("ok")
            lines.append("")
        body = "\n".join(lines)
        path = _write_judge(tmp_path, fm, body)
        with pytest.raises(JudgeAuditError, match="CP06"):
            audit_judge_md(path)

    def test_reject_only_needs_cp01(self, tmp_path: Path) -> None:
        fm = _good_frontmatter()
        fm["candidates"][0]["verdict"] = "reject"
        fm["candidates"][0]["hard_gate_result"] = "coverage 0.4 < 0.8"
        fm["batch_summary"] = {"total": 1, "admit": 0, "reserve": 0, "reject": 1}
        body = "## C001 — REJECT\n\n### CP01\nhard gate failed\n"
        path = _write_judge(tmp_path, fm, body)
        audit_judge_md(path)  # no raise


class TestCp03CitesMtBucket:
    def test_cp03_without_mt_bucket_raises(self, tmp_path: Path) -> None:
        fm = _good_frontmatter()
        lines = ["## C001 — ADMIT", ""]
        for cp in ALL_CHECKPOINTS:
            lines.append(f"### {cp}")
            lines.append("reasoning but no magic string")
            lines.append("")
        body = "\n".join(lines)
        path = _write_judge(tmp_path, fm, body)
        with pytest.raises(JudgeAuditError, match="mt_bucket"):
            audit_judge_md(path)

    def test_reject_cp03_not_checked(self, tmp_path: Path) -> None:
        fm = _good_frontmatter()
        fm["candidates"][0]["verdict"] = "reject"
        fm["candidates"][0]["hard_gate_result"] = "compute_error: NaN"
        fm["batch_summary"] = {"total": 1, "admit": 0, "reserve": 0, "reject": 1}
        body = "## C001 — REJECT\n\n### CP01\nhard gate failed\n"
        # No CP03 section at all — that's fine for reject
        path = _write_judge(tmp_path, fm, body)
        audit_judge_md(path)


class TestReferencedContext:
    def test_fabricated_reference_raises(self, tmp_path: Path) -> None:
        fm = _good_frontmatter()
        fm["candidates"][0]["referenced_context"] = [
            "directions/fp_divergence.md#Hypothesis",
            "directions/imaginary.md#FakeSection",
        ]
        path = _write_judge(tmp_path, fm, _good_body())
        packet_refs = {"directions/fp_divergence.md#Hypothesis"}
        with pytest.raises(JudgeAuditError, match="not in the judge_packet"):
            audit_judge_md(path, packet_refs=packet_refs)

    def test_subset_references_pass(self, tmp_path: Path) -> None:
        fm = _good_frontmatter()
        path = _write_judge(tmp_path, fm, _good_body())
        packet_refs = {
            "directions/fp_divergence.md#Hypothesis",
            "lessons.md#Structural Constraints",
        }
        audit_judge_md(path, packet_refs=packet_refs)  # no raise

    def test_none_packet_refs_skips_check(self, tmp_path: Path) -> None:
        fm = _good_frontmatter()
        fm["candidates"][0]["referenced_context"] = ["anything.md"]
        path = _write_judge(tmp_path, fm, _good_body())
        # packet_refs=None → the authenticity check is skipped
        audit_judge_md(path, packet_refs=None)
