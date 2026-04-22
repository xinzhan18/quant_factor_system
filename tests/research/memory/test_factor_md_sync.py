"""Tests for factor_md_sync — yaml → md frontmatter lifecycle sync."""

from __future__ import annotations

from pathlib import Path

from research.memory.factor_md_sync import (
    sync_all_factor_md,
    sync_factor_md_frontmatter,
)
from research.storage.paths import StoragePaths
from research.storage.yaml_io import save_yaml


def _write_md(path: Path, status: str = "active") -> None:
    path.write_text(
        "---\n"
        "id: F001\ndecision: admit\n"
        f"status: {status}\n"
        "composite_grade: A\n"
        "---\n# F001\n\nBody text stays untouched.\n",
        encoding="utf-8",
    )


class TestSyncFactorMdFrontmatter:
    def test_pushes_retired_into_md(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / "F001.yaml"
        md_path = tmp_path / "F001.md"
        save_yaml(yaml_path, {"factor_id": "F001", "status": "retired"})
        _write_md(md_path, status="active")
        assert sync_factor_md_frontmatter(yaml_path, md_path) is True
        text = md_path.read_text(encoding="utf-8")
        assert "status: retired" in text
        assert "status: active" not in text
        assert "Body text stays untouched." in text

    def test_noop_when_already_synced(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / "F001.yaml"
        md_path = tmp_path / "F001.md"
        save_yaml(yaml_path, {"factor_id": "F001", "status": "active"})
        _write_md(md_path, status="active")
        assert sync_factor_md_frontmatter(yaml_path, md_path) is False

    def test_adds_duplicate_of(self, tmp_path: Path) -> None:
        yaml_path = tmp_path / "F005.yaml"
        md_path = tmp_path / "F005.md"
        save_yaml(
            yaml_path,
            {"factor_id": "F005", "status": "retired", "duplicate_of": "F004"},
        )
        _write_md(md_path, status="active")
        sync_factor_md_frontmatter(yaml_path, md_path)
        text = md_path.read_text(encoding="utf-8")
        assert "duplicate_of: F004" in text
        assert "status: retired" in text


class TestSyncAllFactorMd:
    def test_counts_all_and_touched(self, tmp_path: Path) -> None:
        paths = StoragePaths(tmp_path)
        paths.ensure_dirs()
        # F001: yaml=retired, md=active → touched
        save_yaml(
            paths.factors_dir / "F001.yaml",
            {"factor_id": "F001", "status": "retired"},
        )
        _write_md(paths.factors_dir / "F001.md", status="active")
        # F002: yaml=active, md=active → no touch
        save_yaml(
            paths.factors_dir / "F002.yaml",
            {"factor_id": "F002", "status": "active"},
        )
        _write_md(paths.factors_dir / "F002.md", status="active")
        total, touched = sync_all_factor_md(paths)
        assert total == 2
        assert touched == 1
