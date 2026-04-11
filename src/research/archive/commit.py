"""Git commit helper — main Phase 4 commit with hard-fail on hook failure.

Per refactor_plan §8 + Q47.3:

* ``git add <specific paths>`` (never ``git add -A``)
* ``git commit -m "[mine] batch_{id} | {direction} | admits={N} ..."``
* Pre-commit hook failure → ``GitCommitError`` raised (not silently
  swallowed)
* Returns the resulting commit hash

The commit message follows a structured template so downstream tooling
(``research audit failures``, ``research audit mt-budget``) can parse
batch outcomes from ``git log`` without needing a separate ledger.

Note on subprocess use: this module is one of the few new P1-P6 modules
that invokes ``subprocess``. That's legal because new **code** can
invoke subprocess — the R8 Python factor whitelist forbids it for
user-written factor modules, but infrastructure like commit helpers
are unaffected.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


class GitCommitError(RuntimeError):
    """Raised when ``git commit`` or a prerequisite command fails."""


@dataclass
class CommitResult:
    """What :func:`create_commit` returns on success."""

    commit_hash: str
    message: str
    files_committed: list[str]


def _run(
    cmd: list[str],
    *,
    cwd: Path,
    description: str,
) -> subprocess.CompletedProcess:
    """Run a git subprocess, raising :class:`GitCommitError` on non-zero exit."""
    try:
        proc = subprocess.run(
            cmd, cwd=str(cwd), capture_output=True, text=True, check=False
        )
    except FileNotFoundError as exc:
        raise GitCommitError(
            f"{description}: git binary not found ({exc})"
        ) from exc

    if proc.returncode != 0:
        raise GitCommitError(
            f"{description} failed (exit {proc.returncode}): "
            f"stdout={proc.stdout!r} stderr={proc.stderr!r}"
        )
    return proc


def stage_files(repo_root: str | Path, paths: Iterable[str | Path]) -> list[str]:
    """``git add`` each path; returns the list of absolute paths staged.

    Never calls ``git add -A``. Missing files are skipped silently so
    the caller can safely over-declare (e.g. include ``vault/INDEX.md``
    even when it wasn't touched — it'll be a no-op).
    """
    root = Path(repo_root)
    staged: list[str] = []
    for p in paths:
        ap = Path(p)
        if not ap.is_absolute():
            ap = root / ap
        if not ap.exists():
            continue
        rel = str(ap.relative_to(root))
        _run(["git", "add", rel], cwd=root, description=f"git add {rel}")
        staged.append(rel)
    return staged


def build_commit_message(
    batch_id: str,
    direction: str,
    n_admit: int,
    n_reserve: int,
    n_reject: int,
    factor_ids: list[str],
    batch_goal: str,
) -> str:
    """Render the structured commit message for a Phase 4 main commit."""
    subject = (
        f"[mine] {batch_id} | {direction} | "
        f"admits={n_admit} reserves={n_reserve} rejects={n_reject}"
    )
    lines = [subject, ""]
    if factor_ids:
        lines.append("Admitted: " + ", ".join(factor_ids))
    if batch_goal:
        lines.append(f"Batch goal: {batch_goal.strip()}")
    lines.append("")
    lines.append("Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>")
    return "\n".join(lines)


def create_commit(
    repo_root: str | Path,
    message: str,
    staged_files: list[str],
) -> CommitResult:
    """Run ``git commit -m`` with the given message and staged files.

    Assumes files have already been staged via :func:`stage_files`.
    Hard-fails on pre-commit hook failure (never uses ``--no-verify``).
    """
    root = Path(repo_root)
    proc = _run(
        ["git", "commit", "-m", message],
        cwd=root,
        description="git commit",
    )

    # Resolve HEAD commit hash
    hash_proc = _run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        description="git rev-parse HEAD",
    )
    commit_hash = hash_proc.stdout.strip()

    return CommitResult(
        commit_hash=commit_hash,
        message=message,
        files_committed=staged_files,
    )
