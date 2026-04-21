"""Tests for ``research commit-report F{id}`` CLI command.

This is the link from the /factor-report subagent back to git — without it,
deep-report markdown + chart PNGs sit untracked on disk.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from research.cli.main import _cmd_commit_report
from research.storage.paths import StoragePaths
from research.storage.yaml_io import save_yaml


def _init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"], cwd=root, check=True
    )


def _bootstrap_factor(
    paths: StoragePaths, fid: str, name: str, *, with_assets: bool = True
) -> None:
    save_yaml(paths.factor_yaml_file(fid), {"factor_id": fid, "name": name})
    md_body = (
        "---\n"
        f"id: {fid!r}\n"
        f"name: {name}\n"
        "composite_grade: B\n"
        "composite_score: 67.8\n"
        "---\n\n"
        f"# {fid} — {name}\n\nreport body.\n"
    )
    paths.factor_md_file(fid).write_text(md_body, encoding="utf-8")
    if with_assets:
        adir = paths.factor_assets_dir(fid)
        adir.mkdir(parents=True, exist_ok=True)
        (adir / "ic_timeseries.png").write_bytes(b"\x89PNG\r\n\x1a\nfake")
        (adir / "report.json").write_text('{"ic":0.02}', encoding="utf-8")


def _git_head_msg(root: Path) -> str:
    out = subprocess.run(
        ["git", "log", "-1", "--format=%s"],
        cwd=root, capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


def _git_head_files(root: Path) -> list[str]:
    out = subprocess.run(
        ["git", "log", "-1", "--name-only", "--format="],
        cwd=root, capture_output=True, text=True, check=True,
    )
    return [line for line in out.stdout.splitlines() if line.strip()]


class TestCommitReport:
    def test_commits_md_plus_assets(self, tmp_path: Path, monkeypatch) -> None:
        _init_repo(tmp_path)
        paths = StoragePaths(tmp_path / "storage")
        paths.ensure_dirs()
        _bootstrap_factor(paths, "F042", "demo_factor")

        monkeypatch.chdir(tmp_path)
        monkeypatch.setenv("PWD", str(tmp_path))

        # StoragePaths() with no arg resolves off cwd — patch the class factory
        def _patched():
            return paths
        monkeypatch.setattr(
            "research.storage.paths.StoragePaths", lambda *a, **k: paths
        )

        _cmd_commit_report(SimpleNamespace(factor_id="F042"))

        msg = _git_head_msg(tmp_path)
        assert msg.startswith("[report] F042 demo_factor — deep report")
        assert "(B/67.8)" in msg

        files = _git_head_files(tmp_path)
        assert any("F042.md" in f for f in files)
        assert any("ic_timeseries.png" in f for f in files)
        assert any("report.json" in f for f in files)

    def test_missing_yaml_exits(self, tmp_path: Path, monkeypatch) -> None:
        _init_repo(tmp_path)
        paths = StoragePaths(tmp_path / "storage")
        paths.ensure_dirs()
        monkeypatch.setattr(
            "research.storage.paths.StoragePaths", lambda *a, **k: paths
        )
        with pytest.raises(SystemExit) as exc:
            _cmd_commit_report(SimpleNamespace(factor_id="F999"))
        assert exc.value.code == 1

    def test_missing_md_exits(self, tmp_path: Path, monkeypatch) -> None:
        _init_repo(tmp_path)
        paths = StoragePaths(tmp_path / "storage")
        paths.ensure_dirs()
        save_yaml(paths.factor_yaml_file("F042"), {"factor_id": "F042", "name": "x"})
        monkeypatch.setattr(
            "research.storage.paths.StoragePaths", lambda *a, **k: paths
        )
        with pytest.raises(SystemExit) as exc:
            _cmd_commit_report(SimpleNamespace(factor_id="F042"))
        assert exc.value.code == 1
