"""Tests for archive.commit — message builder + subprocess helpers."""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from research.archive.commit import (
    GitCommitError,
    build_commit_message,
    create_commit,
    stage_files,
)


class TestBuildCommitMessage:
    def test_subject_format(self) -> None:
        msg = build_commit_message(
            batch_id="batch_103",
            direction="fp",
            n_admit=2,
            n_reserve=3,
            n_reject=1,
            factor_ids=["F020", "F021"],
            batch_goal="Probe fp divergence",
        )
        first = msg.splitlines()[0]
        assert first == "[mine] batch_103 | fp | admits=2 reserves=3 rejects=1"
        assert "Admitted: F020, F021" in msg
        assert "Co-Authored-By:" in msg

    def test_no_factors_admitted(self) -> None:
        msg = build_commit_message(
            "batch_103", "fp", 0, 3, 1, [], "probe"
        )
        assert "Admitted" not in msg


def _init_git_repo(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "test"], cwd=tmp_path, check=True
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
    )
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"],
        cwd=tmp_path,
        check=True,
    )
    return tmp_path


class TestStageAndCommit:
    def test_stage_and_commit(self, tmp_path: Path) -> None:
        repo = _init_git_repo(tmp_path / "r")
        f = repo / "hello.txt"
        f.write_text("hi")

        staged = stage_files(repo, [f])
        assert staged == ["hello.txt"]

        result = create_commit(repo, "test commit", staged)
        assert result.commit_hash
        assert len(result.commit_hash) == 40
        assert result.files_committed == ["hello.txt"]

    def test_stage_skips_missing(self, tmp_path: Path) -> None:
        repo = _init_git_repo(tmp_path / "r")
        staged = stage_files(repo, [repo / "nope.txt"])
        assert staged == []

    def test_commit_without_staged_raises(self, tmp_path: Path) -> None:
        repo = _init_git_repo(tmp_path / "r")
        with pytest.raises(GitCommitError):
            create_commit(repo, "empty", [])

    def test_git_not_found(self, tmp_path: Path) -> None:
        repo = _init_git_repo(tmp_path / "r")
        f = repo / "real.txt"
        f.write_text("hi")
        with patch(
            "research.archive.commit.subprocess.run",
            side_effect=FileNotFoundError("git"),
        ):
            with pytest.raises(GitCommitError, match="git binary not found"):
                stage_files(repo, [f])
