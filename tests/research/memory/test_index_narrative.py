"""Tests for INDEX insight-block auto-refresh from consolidation_log.md."""

from __future__ import annotations

from pathlib import Path

from research.memory.index_narrative import (
    INSIGHT_BEGIN,
    INSIGHT_END,
    extract_latest_summary,
    refresh_narrative,
    render_insight_block,
)
from research.storage.paths import StoragePaths


class TestExtractLatestSummary:
    def test_returns_last_section(self) -> None:
        text = (
            "# Consolidation Log\n\n"
            "## batch_010 · Phase 5\nOld summary text.\n\n"
            "## batch_020 · Phase 5\nLatest insight paragraph.\n"
        )
        parsed = extract_latest_summary(text)
        assert parsed is not None
        title, body = parsed
        assert title == "batch_020 · Phase 5"
        assert "Latest insight paragraph." in body
        assert "Old summary" not in body

    def test_no_sections(self) -> None:
        assert extract_latest_summary("# Log\n\nonly body prose") is None


class TestRenderInsightBlock:
    def test_placeholder_when_no_file(self, tmp_path: Path) -> None:
        out = render_insight_block(tmp_path / "missing.md")
        assert INSIGHT_BEGIN in out and INSIGHT_END in out
        assert "暂无 consolidation" in out

    def test_quotes_latest_summary(self, tmp_path: Path) -> None:
        log = tmp_path / "log.md"
        log.write_text(
            "## batch_020 · Phase 5\n"
            "OHLC 5d aggregation 被证实是独立 alpha 维度。\n"
            "下一阶段优先 overnight/intraday 分解。\n",
            encoding="utf-8",
        )
        out = render_insight_block(log)
        assert "batch_020 · Phase 5" in out
        assert "OHLC 5d aggregation" in out
        assert "> OHLC 5d aggregation" in out  # quoted into callout
        assert "完整总结" in out


class TestRefreshNarrative:
    def _seed_index(self, paths: StoragePaths) -> None:
        paths.vault_index_file.write_text(
            "---\nround: 0\n---\n\n# Index\n\n"
            f"{INSIGHT_BEGIN}\n> stale\n{INSIGHT_END}\n\n## bases\n",
            encoding="utf-8",
        )

    def test_replaces_insight_block(self, tmp_path: Path) -> None:
        paths = StoragePaths(tmp_path)
        paths.ensure_dirs()
        self._seed_index(paths)
        paths.consolidation_log_file.parent.mkdir(parents=True, exist_ok=True)
        paths.consolidation_log_file.write_text(
            "## batch_020 · Phase 5\nfresh insight body.\n",
            encoding="utf-8",
        )
        refresh_narrative(paths)
        text = paths.vault_index_file.read_text(encoding="utf-8")
        assert "stale" not in text
        assert "fresh insight body." in text
        assert text.count(INSIGHT_BEGIN) == 1
        assert text.count(INSIGHT_END) == 1

    def test_idempotent(self, tmp_path: Path) -> None:
        paths = StoragePaths(tmp_path)
        paths.ensure_dirs()
        self._seed_index(paths)
        paths.consolidation_log_file.parent.mkdir(parents=True, exist_ok=True)
        paths.consolidation_log_file.write_text(
            "## X\ninsight.\n", encoding="utf-8"
        )
        refresh_narrative(paths)
        first = paths.vault_index_file.read_text(encoding="utf-8")
        refresh_narrative(paths)
        second = paths.vault_index_file.read_text(encoding="utf-8")
        assert first == second
