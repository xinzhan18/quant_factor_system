"""Tests for INDEX.md auto-section regeneration."""

from __future__ import annotations

from pathlib import Path

import pytest

from research.memory.direction_updater import update_direction_frontmatter
from research.memory.index_refresher import (
    BEGIN_SENTINEL,
    END_SENTINEL,
    collect_direction_stats,
    count_admitted_factors,
    refresh_index,
    render_auto_section,
)
from research.storage.paths import StoragePaths
from research.storage.yaml_io import save_yaml


def _bootstrap(tmp_path: Path) -> StoragePaths:
    paths = StoragePaths(tmp_path)
    paths.ensure_dirs()
    return paths


class TestCollectDirectionStats:
    def test_empty_returns_empty_list(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        assert collect_direction_stats(paths.directions_dir) == []

    def test_reads_frontmatter(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        update_direction_frontmatter(
            paths.direction_file("vol"), batch_id="batch_001", new_admits=["F020"]
        )
        update_direction_frontmatter(
            paths.direction_file("mom"),
            batch_id="batch_002",
            new_admits=["F021", "F022"],
        )
        rows = collect_direction_stats(paths.directions_dir)
        by_id = {r["direction_id"]: r for r in rows}
        assert by_id["vol"]["rounds"] == 1
        assert by_id["vol"]["admits"] == 1
        assert by_id["mom"]["admits"] == 2


class TestCountAdmittedFactors:
    def test_counts_F_yaml_only(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        save_yaml(paths.factors_dir / "F020.yaml", {"factor_id": "F020"})
        save_yaml(paths.factors_dir / "F021.yaml", {"factor_id": "F021"})
        (paths.factors_dir / ".DS_Store").write_text("")
        (paths.factors_dir / "notes.md").write_text("notes")
        assert count_admitted_factors(paths.factors_dir) == 2


class TestRenderAutoSection:
    def test_empty_directions_placeholder(self) -> None:
        text = render_auto_section([], total_admitted=0, round_counter=0, last_consolidation_round=None)
        assert BEGIN_SENTINEL in text
        assert END_SENTINEL in text
        assert "no directions yet" in text

    def test_rows_formatted_as_table(self) -> None:
        rows = [
            {
                "direction_id": "vol",
                "status": "active",
                "rounds": 3,
                "admits": 2,
                "last_batch": "batch_010",
            }
        ]
        text = render_auto_section(rows, total_admitted=2, round_counter=10, last_consolidation_round=5)
        assert "| vol | active | 3 | 2 | batch_010 |" in text
        assert "| Total factors admitted | 2 |" in text
        assert "| Current round | 10 |" in text
        assert "round 5" in text


class TestRefreshIndex:
    def test_creates_skeleton_when_missing(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        # Remove the INDEX created by ensure_dirs (if any)
        if paths.vault_index_file.exists():
            paths.vault_index_file.unlink()
        refresh_index(paths, round_counter=0)
        assert paths.vault_index_file.exists()
        text = paths.vault_index_file.read_text(encoding="utf-8")
        assert BEGIN_SENTINEL in text
        assert END_SENTINEL in text

    def test_preserves_upper_half(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        paths.vault_index_file.write_text(
            "# Header\n\nUpper half narrative text.\n\n"
            f"{BEGIN_SENTINEL}\nold table\n{END_SENTINEL}\n",
            encoding="utf-8",
        )
        refresh_index(paths, round_counter=5)
        text = paths.vault_index_file.read_text(encoding="utf-8")
        assert "Upper half narrative text." in text
        assert "old table" not in text  # replaced
        assert "Current round | 5" in text

    def test_appends_when_sentinels_missing(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        paths.vault_index_file.write_text(
            "# No sentinels here", encoding="utf-8"
        )
        refresh_index(paths, round_counter=1)
        text = paths.vault_index_file.read_text(encoding="utf-8")
        assert "# No sentinels here" in text
        assert BEGIN_SENTINEL in text
