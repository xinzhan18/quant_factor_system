"""Tests for INDEX.md auto-section regeneration."""

from __future__ import annotations

from pathlib import Path

import pytest

from research.memory.direction_updater import update_direction_frontmatter
from research.memory.index_refresher import (
    BEGIN_SENTINEL,
    END_SENTINEL,
    FACTOR_LIB_BEGIN_SENTINEL,
    FACTOR_LIB_END_SENTINEL,
    collect_admitted_factors,
    collect_direction_stats,
    count_admitted_factors,
    refresh_index,
    render_auto_section,
    render_factor_library,
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
                "status": "exploring",
                "priority": "medium",
                "rounds": 3,
                "admits": 2,
                "last_batch": "batch_010",
            }
        ]
        text = render_auto_section(rows, total_admitted=2, round_counter=10, last_consolidation_round=5)
        assert "vol" in text
        assert "exploring" in text
        assert "| Total factors admitted | 2 |" in text
        assert "| Current round | 10 |" in text
        assert "round 5" in text


class TestPriorityColumn:
    def test_direction_stats_include_priority(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        d = paths.direction_file("micro")
        d.write_text(
            "---\ndirection_id: micro\nstatus: exploring\npriority: high\n"
            "rounds: 2\nadmits: 1\nlast_batch: batch_005\nmembers: [F053]\n---\n"
            "\n# micro\n",
            encoding="utf-8",
        )
        rows = collect_direction_stats(paths.directions_dir)
        assert len(rows) == 1
        assert rows[0]["priority"] == "high"

    def test_render_includes_priority(self) -> None:
        rows = [{
            "direction_id": "micro", "status": "exploring",
            "priority": "high", "rounds": 2, "admits": 1,
            "last_batch": "batch_005",
        }]
        text = render_auto_section(rows, total_admitted=1, round_counter=5, last_consolidation_round=None)
        assert "| micro |" in text
        assert "high" in text
        assert "Priority" in text


class TestThreadsColumn:
    def test_active_threads_counted(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        d = paths.direction_file("cov")
        d.write_text(
            "---\ndirection_id: cov\nstatus: exploring\npriority: high\n"
            "rounds: 2\nadmits: 1\nlast_batch: batch_006\nmembers: [F007]\n---\n"
            "\n# cov\n\n## Threads\n\n"
            "### T001: question [◉ ACTIVE]\n"
            "### T002: answered [✓ ANSWERED batch_005]\n"
            "### T003: another [◉ ACTIVE]\n",
            encoding="utf-8",
        )
        rows = collect_direction_stats(paths.directions_dir)
        assert len(rows) == 1
        assert rows[0]["active_threads"] == 2

    def test_render_includes_threads_column(self) -> None:
        rows = [{
            "direction_id": "cov", "status": "exploring",
            "priority": "high", "rounds": 2, "admits": 1,
            "last_batch": "batch_006", "active_threads": 2,
        }]
        text = render_auto_section(rows, total_admitted=1, round_counter=6, last_consolidation_round=None)
        assert "Threads" in text
        assert "| 2 |" in text


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


class TestRefreshIndexFrontmatter:
    def _write_state(self, paths: StoragePaths, **overrides: object) -> None:
        base = {
            "current_batch": None,
            "current_batch_phase": None,
            "last_batch": "batch_001",
            "round": 1,
            "last_activity": "2026-04-18T15:00:00Z",
            "rounds_since_last_consolidation": 1,
        }
        base.update(overrides)
        save_yaml(paths.state_file, base)

    def test_creates_frontmatter_when_absent(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        self._write_state(paths)
        update_direction_frontmatter(
            paths.direction_file("vol"), batch_id="batch_001", new_admits=["F001"]
        )
        save_yaml(paths.factors_dir / "F001.yaml", {"factor_id": "F001"})
        paths.vault_index_file.write_text(
            "# Factor Research Index\n\nSome narrative.\n\n"
            f"{BEGIN_SENTINEL}\nold\n{END_SENTINEL}\n",
            encoding="utf-8",
        )
        refresh_index(paths, round_counter=1)
        text = paths.vault_index_file.read_text(encoding="utf-8")
        assert text.startswith("---\n")
        assert "round: 1" in text
        assert "total_active_directions: 1" in text
        assert "total_factors_admitted: 1" in text
        assert "last_batch: batch_001" in text
        assert "Some narrative." in text  # upper half preserved

    def test_replaces_stale_frontmatter(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        self._write_state(paths, round=3, last_batch="batch_003")
        update_direction_frontmatter(
            paths.direction_file("vol"), batch_id="batch_003", new_admits=["F001"]
        )
        update_direction_frontmatter(
            paths.direction_file("mom"), batch_id="batch_002", new_admits=["F002"]
        )
        save_yaml(paths.factors_dir / "F001.yaml", {"factor_id": "F001"})
        save_yaml(paths.factors_dir / "F002.yaml", {"factor_id": "F002"})
        paths.vault_index_file.write_text(
            "---\n"
            "generated_at: 2020-01-01T00:00:00Z\n"
            "round: 0\n"
            "total_active_directions: 0\n"
            "total_factors_admitted: 0\n"
            "last_batch: null\n"
            "last_consolidation_round: null\n"
            "---\n\n"
            "# Factor Research Index\n\nUpper-half narrative.\n\n"
            f"{BEGIN_SENTINEL}\nold\n{END_SENTINEL}\n",
            encoding="utf-8",
        )
        refresh_index(paths, round_counter=3)
        text = paths.vault_index_file.read_text(encoding="utf-8")
        assert "round: 3" in text
        assert "round: 0" not in text
        assert "last_batch: batch_003" in text
        assert "total_factors_admitted: 2" in text
        assert "total_active_directions: 2" in text
        assert "Upper-half narrative." in text
        assert "generated_at: 2020-01-01T00:00:00Z" not in text

    def test_factor_library_block_replaced(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        self._write_state(paths, round=1, last_batch="batch_001")
        save_yaml(
            paths.factors_dir / "F001.yaml",
            {
                "factor_id": "F001",
                "name": "amount_cv_10",
                "direction": "amount_volatility_signal",
                "expression": "Div(Std($amount, 10), Mean($amount, 10))",
                "validation_metrics": {
                    "ic_ir": -0.7158,
                    "monotonicity": -0.9999,
                },
            },
        )
        # Sibling F001.md contributes composite_grade via frontmatter
        (paths.factors_dir / "F001.md").write_text(
            "---\nid: F001\ncomposite_grade: B\n---\n# F001\n",
            encoding="utf-8",
        )
        paths.vault_index_file.write_text(
            "---\nround: 0\nlast_batch: null\n---\n\n"
            "# Factor Research Index\n\n"
            "## 因子库\n\n"
            f"{FACTOR_LIB_BEGIN_SENTINEL}\n"
            "stale placeholder\n"
            f"{FACTOR_LIB_END_SENTINEL}\n\n"
            f"{BEGIN_SENTINEL}\nold\n{END_SENTINEL}\n",
            encoding="utf-8",
        )
        refresh_index(paths, round_counter=1)
        text = paths.vault_index_file.read_text(encoding="utf-8")
        assert "stale placeholder" not in text
        assert "[[factors/F001|amount_cv_10]]" in text
        assert "`B`" in text
        assert "amount_volatility_signal" in text
        assert "ICIR_oos=-0.716" in text
        assert "Mono=-1.00" in text
        assert "Div(Std($amount, 10), Mean($amount, 10))" in text

    def test_factor_library_no_grade_when_md_missing(
        self, tmp_path: Path
    ) -> None:
        paths = _bootstrap(tmp_path)
        self._write_state(paths)
        save_yaml(
            paths.factors_dir / "F001.yaml",
            {
                "factor_id": "F001",
                "name": "amount_cv_10",
                "direction": "amount_volatility_signal",
                "expression": "Div(Std($amount, 10), Mean($amount, 10))",
                "validation_metrics": {"ic_ir": -0.72, "monotonicity": -1.0},
            },
        )
        paths.vault_index_file.write_text(
            f"# I\n\n{FACTOR_LIB_BEGIN_SENTINEL}\n{FACTOR_LIB_END_SENTINEL}\n",
            encoding="utf-8",
        )
        refresh_index(paths, round_counter=1)
        text = paths.vault_index_file.read_text(encoding="utf-8")
        # No composite_grade → no `B` / `A` / etc token before the direction
        assert "`B`" not in text
        assert "[[factors/F001|amount_cv_10]]" in text
        assert " · amount_volatility_signal" in text

    def test_factor_library_sorted_numerically(self, tmp_path: Path) -> None:
        paths = _bootstrap(tmp_path)
        self._write_state(paths)
        for fid in ("F002", "F010", "F001"):
            save_yaml(
                paths.factors_dir / f"{fid}.yaml",
                {
                    "factor_id": fid,
                    "name": fid.lower(),
                    "direction": "d",
                    "expression": "expr",
                    "validation_metrics": {},
                },
            )
        rows = collect_admitted_factors(paths.factors_dir)
        assert [r["factor_id"] for r in rows] == ["F001", "F002", "F010"]

    def test_factor_library_block_no_sentinel_is_noop(
        self, tmp_path: Path
    ) -> None:
        """INDEX without factor-library sentinels should stay untouched."""
        paths = _bootstrap(tmp_path)
        self._write_state(paths)
        save_yaml(paths.factors_dir / "F001.yaml", {"factor_id": "F001"})
        paths.vault_index_file.write_text(
            f"# Factor Research Index\n\n{BEGIN_SENTINEL}\nx\n{END_SENTINEL}\n",
            encoding="utf-8",
        )
        refresh_index(paths, round_counter=1)
        text = paths.vault_index_file.read_text(encoding="utf-8")
        assert FACTOR_LIB_BEGIN_SENTINEL not in text  # not injected unsolicited

    def test_render_factor_library_empty(self) -> None:
        text = render_factor_library([])
        assert FACTOR_LIB_BEGIN_SENTINEL in text
        assert FACTOR_LIB_END_SENTINEL in text
        assert "暂无" in text

    def test_excludes_dead_and_merged_from_active_count(
        self, tmp_path: Path
    ) -> None:
        paths = _bootstrap(tmp_path)
        self._write_state(paths)
        live = paths.direction_file("live")
        live.write_text(
            "---\ndirection_id: live\nstatus: exploring\npriority: medium\n"
            "rounds: 1\nadmits: 0\nlast_batch: batch_001\nmembers: []\n---\n# live\n",
            encoding="utf-8",
        )
        dead = paths.direction_file("dead")
        dead.write_text(
            "---\ndirection_id: dead\nstatus: dead\npriority: low\n"
            "rounds: 2\nadmits: 0\nlast_batch: batch_000\nmembers: []\n---\n# dead\n",
            encoding="utf-8",
        )
        merged = paths.direction_file("merged")
        merged.write_text(
            "---\ndirection_id: merged\nstatus: merged\npriority: low\n"
            "rounds: 2\nadmits: 0\nlast_batch: batch_000\nmembers: []\n---\n# merged\n",
            encoding="utf-8",
        )
        refresh_index(paths, round_counter=1)
        text = paths.vault_index_file.read_text(encoding="utf-8")
        assert "total_active_directions: 1" in text
