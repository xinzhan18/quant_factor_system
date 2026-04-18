"""Tests for report_packer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from research.archive.report_packer import (
    ReportPacketInputs,
    build_report_packet,
    extract_candidate_synthesis,
    write_report_packet,
)


def _record(source_type: str = "dsl") -> dict[str, Any]:
    base = {
        "factor_id": "F020",
        "name": "triple_product_80d_pb",
        "source_type": source_type,
        "family_tag": "fp_divergence",
        "validation_metrics": {
            "ic_mean": 0.016,
            "ic_ir": 0.338,
            "ic_win_rate": 0.60,
            "monotonicity": 0.95,
            "long_short_mean": 0.007,
        },
        "risk_metrics": {"style_r_squared": 0.08, "alpha_survival_ratio": 0.69},
    }
    if source_type == "dsl":
        base["expression"] = "Mul(Corr($pe_ratio, Mean($close, 80), 80), $turnover_rate)"
    else:
        base["python_path"] = "F020_triple_product.py"
    return base


def _inputs(**overrides: Any) -> ReportPacketInputs:
    defaults = {
        "factor_id": "F020",
        "factor_record": _record(),
        "direction": "fp_divergence",
        "direction_excerpt": "Hypothesis: fundamental × price divergence",
        "judge_synthesis": "## C001 — ADMIT\n\n### CP03 strong\nmt_bucket=medium",
        "nearest_factor_summary": "Nearest: F012 (corr=0.30)",
        "admitted_in_batch": "batch_103",
    }
    defaults.update(overrides)
    return ReportPacketInputs(**defaults)


class TestBuildReportPacket:
    def test_frontmatter_fields(self) -> None:
        text = build_report_packet(_inputs())
        assert text.startswith("---\n")
        assert "factor_id: F020" in text
        assert "direction: fp_divergence" in text
        assert "admitted_in_batch: batch_103" in text

    def test_factor_yaml_block_rendered(self) -> None:
        text = build_report_packet(_inputs())
        assert "## Factor YAML Summary" in text
        assert "```yaml" in text
        assert "triple_product_80d_pb" in text
        assert "ic_mean" in text

    def test_direction_section_optional(self) -> None:
        text = build_report_packet(_inputs(direction_excerpt=""))
        assert "## Direction Context" not in text

    def test_judge_synthesis_section(self) -> None:
        text = build_report_packet(_inputs())
        assert "## Judge Synthesis" in text
        assert "mt_bucket=medium" in text

    def test_library_context_section(self) -> None:
        text = build_report_packet(_inputs())
        assert "## Library Context" in text
        assert "Nearest: F012" in text

    def test_instructions_always_present(self) -> None:
        text = build_report_packet(_inputs())
        assert "## Instructions" in text
        assert "do not open other files" in text

    def test_python_factor_includes_path(self) -> None:
        text = build_report_packet(_inputs(factor_record=_record("python")))
        assert "python_path" in text
        assert "F020_triple_product.py" in text

    def test_available_charts_listed(self) -> None:
        text = build_report_packet(
            _inputs(available_charts=["ic_timeseries", "quintile_bar"])
        )
        assert "## Available Charts" in text
        assert "- `ic_timeseries`" in text
        assert "- `quintile_bar`" in text
        # Whitelist warning is present in the section body
        assert "Do not embed any chart name that is not on this list" in text

    def test_empty_available_charts_warns_no_embeds(self) -> None:
        text = build_report_packet(_inputs(available_charts=[]))
        assert "## Available Charts" in text
        assert "No charts generated" in text
        # Instructions must steer the subagent toward text-only output
        assert "do not include any `![[...png]]` embeds" in text


class TestWriteReportPacket:
    def test_writes_to_disk(self, tmp_path: Path) -> None:
        out = tmp_path / "_packets" / "report_packet_F020.md"
        text = write_report_packet(_inputs(), out)
        assert out.exists()
        assert out.read_text(encoding="utf-8") == text


class TestExtractCandidateSynthesis:
    def test_reads_full_candidate_md(self, tmp_path: Path) -> None:
        p = tmp_path / "C001.md"
        p.write_text(
            "---\ncandidate_id: C001\nverdict: admit\n---\n\n"
            "## CP03\nstrong, mt_bucket=medium, search_adjusted=0.41\n",
            encoding="utf-8",
        )
        text = extract_candidate_synthesis(p)
        assert "candidate_id: C001" in text
        assert "mt_bucket=medium" in text

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert extract_candidate_synthesis(tmp_path / "nope.md") == ""
