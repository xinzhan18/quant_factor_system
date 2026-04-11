"""Tests for python_archiver."""

from __future__ import annotations

from pathlib import Path

import pytest

from research.archive.python_archiver import PythonArchiveError, archive_python_factor


def test_copies_to_target(tmp_path: Path) -> None:
    src = tmp_path / "C001.py"
    src.write_text("REQUIRED_FIELDS=['$close']\nVECTORIZED=True\n", encoding="utf-8")
    out_dir = tmp_path / "python_factors"
    dst = archive_python_factor(src, out_dir, "F020", "triple_product")
    assert dst == out_dir / "F020_triple_product.py"
    assert dst.exists()
    assert "REQUIRED_FIELDS" in dst.read_text(encoding="utf-8")


def test_missing_source_raises(tmp_path: Path) -> None:
    with pytest.raises(PythonArchiveError, match="source missing"):
        archive_python_factor(
            tmp_path / "nope.py", tmp_path / "python_factors", "F020", "x"
        )


def test_collision_raises(tmp_path: Path) -> None:
    src = tmp_path / "C001.py"
    src.write_text("content", encoding="utf-8")
    out_dir = tmp_path / "python_factors"
    archive_python_factor(src, out_dir, "F020", "x")
    with pytest.raises(PythonArchiveError, match="already exists"):
        archive_python_factor(src, out_dir, "F020", "x")


def test_no_tmp_files_left(tmp_path: Path) -> None:
    src = tmp_path / "C001.py"
    src.write_text("content", encoding="utf-8")
    out_dir = tmp_path / "python_factors"
    archive_python_factor(src, out_dir, "F020", "x")
    leftover = list(out_dir.glob("*.tmp"))
    assert leftover == []
