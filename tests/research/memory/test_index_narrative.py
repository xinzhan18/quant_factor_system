"""Tests for INDEX.md narrative auto-refresh (Bug 4)."""

from __future__ import annotations

from pathlib import Path

import pytest

from research.memory.index_narrative import (
    DIRECTIONS_BEGIN,
    DIRECTIONS_END,
    RECENT_BEGIN,
    RECENT_END,
    extract_abstract_block,
    refresh_narrative,
    render_active_directions,
    render_recent_batches,
)
from research.storage.paths import StoragePaths


def _seed_batch(bdir: Path, batch_id: str, abstract: str) -> None:
    bdir.mkdir(parents=True, exist_ok=True)
    body = (
        "---\n"
        f"batch_id: {batch_id}\n"
        "---\n\n"
        f"# {batch_id}\n\n"
        "> [!abstract]+ " + abstract.replace("\n", "\n> ") + "\n\n"
        "body paragraph.\n"
    )
    (bdir / "judge.md").write_text(body, encoding="utf-8")


def _seed_direction(
    path: Path,
    *,
    status: str = "productive",
    priority: str = "high",
    rounds: int = 3,
    admits: int = 2,
    last_batch: str = "batch_010",
    narrative: str = "",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "---\n"
        f"direction_id: {path.stem}\n"
        f"status: {status}\n"
        f"priority: {priority}\n"
        f"rounds: {rounds}\n"
        f"admits: {admits}\n"
        f"last_batch: {last_batch}\n"
        "---\n\n"
        f"# {path.stem}\n\n"
        "## Narrative Log\n\n" + narrative,
        encoding="utf-8",
    )


class TestExtractAbstractBlock:
    def test_single_line(self) -> None:
        text = (
            "# batch_001\n\n"
            "> [!abstract]+ batch_001 · 3 candidates\n"
            "> admit=2 reject=1\n"
            "\nbody\n"
        )
        out = extract_abstract_block(text)
        assert out is not None
        assert "batch_001" in out
        assert "admit=2 reject=1" in out

    def test_missing_callout(self) -> None:
        assert extract_abstract_block("no callout here") is None


class TestRenderRecentBatches:
    def test_newest_first(self, tmp_path: Path) -> None:
        _seed_batch(tmp_path / "batch_001", "batch_001", "batch_001 · 3 candidates · admit=1")
        _seed_batch(tmp_path / "batch_002", "batch_002", "batch_002 · 2 candidates · admit=0")
        _seed_batch(tmp_path / "batch_010", "batch_010", "batch_010 · 5 candidates · admit=2")
        out = render_recent_batches(tmp_path)
        assert RECENT_BEGIN in out and RECENT_END in out
        # batch_010 first, then batch_002, then batch_001
        pos_010 = out.index("batch_010/judge")
        pos_002 = out.index("batch_002/judge")
        pos_001 = out.index("batch_001/judge")
        assert pos_010 < pos_002 < pos_001

    def test_respects_max_batches(self, tmp_path: Path) -> None:
        for i in range(1, 20):
            bid = f"batch_{i:03d}"
            _seed_batch(tmp_path / bid, bid, f"{bid} · abstract")
        out = render_recent_batches(tmp_path, max_batches=5)
        # Oldest 14 should be absent
        for i in range(1, 15):
            bid = f"batch_{i:03d}"
            assert f"{bid}/judge" not in out
        # Newest 5 present
        for i in range(15, 20):
            bid = f"batch_{i:03d}"
            assert f"{bid}/judge" in out

    def test_skips_batches_without_judge(self, tmp_path: Path) -> None:
        (tmp_path / "batch_001").mkdir()  # no judge.md
        _seed_batch(tmp_path / "batch_002", "batch_002", "batch_002 · ok")
        out = render_recent_batches(tmp_path)
        assert "batch_001/judge" not in out
        assert "batch_002/judge" in out


class TestRenderActiveDirections:
    def test_excludes_dead_and_merged(self, tmp_path: Path) -> None:
        _seed_direction(tmp_path / "live.md", status="productive")
        _seed_direction(tmp_path / "dead.md", status="dead")
        _seed_direction(tmp_path / "merged.md", status="merged")
        out = render_active_directions(tmp_path)
        assert "live" in out
        assert "dead" not in out
        assert "merged" not in out

    def test_orders_productive_before_exploring(self, tmp_path: Path) -> None:
        _seed_direction(tmp_path / "expl.md", status="exploring", priority="high")
        _seed_direction(tmp_path / "prod.md", status="productive", priority="low")
        out = render_active_directions(tmp_path)
        # productive sorts before exploring regardless of priority
        assert out.index("prod") < out.index("expl")

    def test_includes_latest_narrative_line(self, tmp_path: Path) -> None:
        narrative = (
            "### 2026-04-21 [[batches/batch_010/judge|batch_010]]\n"
            "admit=1 / reject=2 — 方向首 admit。\n"
        )
        _seed_direction(tmp_path / "foo.md", narrative=narrative)
        out = render_active_directions(tmp_path)
        assert "admit=1 / reject=2" in out


class TestRefreshNarrative:
    def test_creates_sentinel_blocks_when_absent(self, tmp_path: Path) -> None:
        paths = StoragePaths(tmp_path / "storage")
        paths.ensure_dirs()
        # Minimal pre-existing INDEX.md (no narrative sentinels)
        paths.vault_index_file.write_text(
            "---\nround: 0\n---\n\n# Factor Research Index\n\n## 因子库\n\n",
            encoding="utf-8",
        )
        _seed_batch(paths.batches_dir / "batch_001", "batch_001", "batch_001 · admit=1")
        _seed_direction(paths.directions_dir / "foo.md", status="productive")

        refresh_narrative(paths)
        text = paths.vault_index_file.read_text(encoding="utf-8")
        assert RECENT_BEGIN in text and RECENT_END in text
        assert DIRECTIONS_BEGIN in text and DIRECTIONS_END in text
        assert "batch_001/judge" in text
        assert "foo" in text

    def test_idempotent_on_second_call(self, tmp_path: Path) -> None:
        paths = StoragePaths(tmp_path / "storage")
        paths.ensure_dirs()
        paths.vault_index_file.write_text(
            "---\nround: 0\n---\n\n# INDEX\n\n",
            encoding="utf-8",
        )
        _seed_batch(paths.batches_dir / "batch_001", "batch_001", "batch_001 · admit=1")
        refresh_narrative(paths)
        first = paths.vault_index_file.read_text(encoding="utf-8")
        refresh_narrative(paths)
        second = paths.vault_index_file.read_text(encoding="utf-8")
        assert first == second
