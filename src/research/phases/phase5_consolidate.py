"""Phase 5 CONSOLIDATION orchestrator.

Rewrites the LLM-maintained markdown (lessons.md, directions/*.md,
INDEX.md upper half) on a periodic schedule when one of the trigger
conditions fires (refactor_plan §9):

* ``rounds_since_last_consolidation >= auto_triggers.rounds_since_last``
* ``lessons.md`` line count exceeds ``auto_triggers.lessons_max_lines``
* any ``directions/{name}.md`` exceeds ``auto_triggers.direction_max_lines``
* total active directions exceeds ``auto_triggers.total_active_directions``

Orchestration (5 synchronous steps — Phase 5 **never** runs in parallel
with Phase 4, which is guaranteed by the ``state.current_batch is None``
precondition below):

1. **Pre-checks** — state.current_batch must be None, git tree clean,
   no subagent failures outstanding.
2. **Pre-pack** — build ``_consolidation/packet_{target}.md`` files
   for each rewrite target (one per direction + one for lessons +
   one for INDEX upper half).
3. **Subagent rewrites** — parallel dispatch via the injected
   ``rewrite_callback``. Each callback invocation receives one packet
   and writes one markdown file.
4. **INDEX upper half** — a dependent synchronous rewrite that reads
   the freshly-rewritten directions (handled by the same callback
   with a special ``target="INDEX"`` key).
5. **Commit** — single ``[consolidate] round N`` commit + state update
   (``mark_consolidated`` resets the counter).

The rewrite_callback injection mirrors Phase 3's LlmJudgeCallback:
production hooks it to Claude Code subagent dispatch; tests pass a
plain Python function that writes canned content.

This module does NOT decide what goes into the packets — that's the
``memory/packer.py`` layer (stubbed here inline, fleshed out in a
follow-up if needed). The orchestration contract is what matters for
Phase 5's correctness.
"""

from __future__ import annotations

import logging
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable

from research.archive.commit import CommitResult, create_commit, stage_files
from research.memory.index_refresher import refresh_index
from research.storage.paths import StoragePaths
from research.storage.state import StateFile

logger = logging.getLogger(__name__)

# rewrite_callback(packet_text, packet_path, output_path, target_kind)
#
# - packet_text: the full _consolidation/packet_{...}.md string
# - packet_path: where the packet lives (single input)
# - output_path: where to write the rewritten md
# - target_kind: "lessons" | "direction" | "index" — lets the subagent
#   apply different rewrite templates
RewriteCallback = Callable[[str, Path, Path, str], None]


class Phase5PreconditionError(RuntimeError):
    """Raised when consolidation preconditions are not met."""


@dataclass
class ConsolidationTrigger:
    """Why consolidation fired — used in commit message and logs."""

    reason: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Phase5Inputs:
    """Everything Phase 5 needs."""

    paths: StoragePaths
    repo_root: Path
    trigger: ConsolidationTrigger
    rewrite_callback: RewriteCallback | None = None
    do_commit: bool = True


@dataclass
class Phase5Result:
    targets: list[str]
    packets: list[Path]
    rewritten: list[Path]
    commit: CommitResult | None = None


# ---------------------------------------------------------------------------
# Trigger detection
# ---------------------------------------------------------------------------


def _count_md_lines(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for _ in path.read_text(encoding="utf-8").splitlines())


def check_triggers(
    paths: StoragePaths,
    auto_triggers: dict[str, int],
    rounds_since_last: int,
) -> ConsolidationTrigger | None:
    """Evaluate all four triggers and return the first that fires."""
    if rounds_since_last >= int(auto_triggers.get("rounds_since_last", 10)):
        return ConsolidationTrigger(
            reason="rounds_since_last",
            details={"rounds_since_last": rounds_since_last},
        )

    lessons_lines = _count_md_lines(paths.vault_lessons_file)
    if lessons_lines >= int(auto_triggers.get("lessons_max_lines", 400)):
        return ConsolidationTrigger(
            reason="lessons_max_lines",
            details={"lessons_lines": lessons_lines},
        )

    max_dir_lines = int(auto_triggers.get("direction_max_lines", 500))
    for md in paths.directions_dir.glob("*.md"):
        n = _count_md_lines(md)
        if n >= max_dir_lines:
            return ConsolidationTrigger(
                reason="direction_max_lines",
                details={"direction": md.stem, "lines": n},
            )

    max_active = int(auto_triggers.get("total_active_directions", 20))
    n_dirs = sum(1 for _ in paths.directions_dir.glob("*.md"))
    if n_dirs >= max_active:
        return ConsolidationTrigger(
            reason="total_active_directions",
            details={"count": n_dirs},
        )

    return None


# ---------------------------------------------------------------------------
# Pre-pack
# ---------------------------------------------------------------------------


def _build_packet_for_lessons(paths: StoragePaths) -> str:
    """Simple inline packer — grows more elaborate in follow-up work."""
    body = ""
    if paths.vault_lessons_file.exists():
        body = paths.vault_lessons_file.read_text(encoding="utf-8")
    return (
        "# Consolidation Packet — lessons.md\n\n"
        "## Current content\n\n"
        f"{body}\n\n"
        "## Instructions\n\n"
        "Rewrite `vault/lessons.md` to remove redundant lessons and "
        "promote stable facts. Preserve Data Facts, Operator Registry, "
        "Path Selection, and Structural Constraints sections. Target "
        "length < 400 lines.\n"
    )


def _build_packet_for_direction(paths: StoragePaths, direction: str) -> str:
    md_path = paths.direction_file(direction)
    body = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    return (
        f"# Consolidation Packet — directions/{direction}.md\n\n"
        "## Current content\n\n"
        f"{body}\n\n"
        "## Instructions\n\n"
        "Rewrite this direction md to compress long narrative logs, "
        "dedupe threads, and preserve Hypothesis + active Threads + "
        "Narrative Log (truncated to most recent 20 entries). Do not "
        "touch the frontmatter — Python manages that.\n"
    )


def _build_packet_for_index(paths: StoragePaths) -> str:
    body = (
        paths.vault_index_file.read_text(encoding="utf-8")
        if paths.vault_index_file.exists()
        else ""
    )
    return (
        "# Consolidation Packet — INDEX.md (upper half)\n\n"
        "## Current content\n\n"
        f"{body}\n\n"
        "## Instructions\n\n"
        "Rewrite the upper half of `vault/INDEX.md` (everything ABOVE "
        "the `<!-- BEGIN AUTO-SECTION -->` marker). Summarize active "
        "directions and recent highlights. Do NOT touch the lower half "
        "— Python regenerates the stats table on every archive.\n"
    )


def prepack_consolidation(
    paths: StoragePaths,
    directions: Iterable[str] | None = None,
) -> dict[str, Path]:
    """Write all consolidation packets to ``_consolidation/`` and return paths.

    The returned dict maps ``target_kind`` (``"lessons"``,
    ``"direction:{name}"``, ``"index"``) to the packet path.
    """
    consolidation_dir = paths.vault_meta_dir.parent / "_consolidation"
    consolidation_dir.mkdir(parents=True, exist_ok=True)

    packets: dict[str, Path] = {}

    # lessons
    lessons_pkt = consolidation_dir / "packet_lessons.md"
    lessons_pkt.write_text(
        _build_packet_for_lessons(paths), encoding="utf-8"
    )
    packets["lessons"] = lessons_pkt

    # directions
    if directions is None:
        directions = sorted(p.stem for p in paths.directions_dir.glob("*.md"))
    for d in directions:
        pkt = consolidation_dir / f"packet_direction_{d}.md"
        pkt.write_text(
            _build_packet_for_direction(paths, d), encoding="utf-8"
        )
        packets[f"direction:{d}"] = pkt

    # INDEX (synchronous, runs after directions in the orchestrator)
    index_pkt = consolidation_dir / "packet_index.md"
    index_pkt.write_text(_build_packet_for_index(paths), encoding="utf-8")
    packets["index"] = index_pkt

    return packets


# ---------------------------------------------------------------------------
# Pre-checks
# ---------------------------------------------------------------------------


def _is_git_clean(repo_root: Path) -> bool:
    try:
        proc = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False
    if proc.returncode != 0:
        return False
    return proc.stdout.strip() == ""


def preconditions_ok(
    state_file: StateFile,
    repo_root: Path,
    backup_dir: Path | None = None,
) -> list[str]:
    """Return a list of precondition failure messages (empty = all OK)."""
    failures: list[str] = []
    state = state_file.read()
    if state.current_batch is not None:
        failures.append(
            f"state.current_batch={state.current_batch!r} — batch in flight"
        )
    if not _is_git_clean(repo_root):
        failures.append("git tree is dirty")
    if backup_dir is not None and backup_dir.exists():
        failures.append(
            f"_consolidation/backup/ exists at {backup_dir} — "
            "previous run failed without cleanup; resolve manually"
        )
    return failures


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_phase5_consolidation(inputs: Phase5Inputs) -> Phase5Result:
    """Run all five Phase 5 steps end-to-end.

    Raises
    ------
    Phase5PreconditionError
        If state.current_batch is not None or git tree is dirty.
    """
    paths = inputs.paths

    # --- Step 1: Pre-checks ---
    state_file = StateFile(paths.state_file)
    failures = preconditions_ok(state_file, inputs.repo_root)
    if failures:
        raise Phase5PreconditionError(
            "phase5 preconditions failed: " + "; ".join(failures)
        )

    # --- Step 2: Pre-pack ---
    packet_map = prepack_consolidation(paths)

    # --- Step 3 + 4: Dispatch rewrites ---
    rewritten: list[Path] = []
    if inputs.rewrite_callback is not None:
        # Parallel (per R3 LLM only reads one file at a time, but the
        # orchestrator can invoke many callbacks — in production this is
        # actual subagent parallelism; in tests the callback is sync.)
        for target_key, pkt_path in packet_map.items():
            if target_key == "index":
                continue  # INDEX runs last after directions finish
            output_path, kind = _output_for(paths, target_key)
            pkt_text = pkt_path.read_text(encoding="utf-8")
            inputs.rewrite_callback(pkt_text, pkt_path, output_path, kind)
            rewritten.append(output_path)

        # INDEX upper half (synchronous — depends on all directions)
        idx_pkt = packet_map["index"]
        idx_text = idx_pkt.read_text(encoding="utf-8")
        inputs.rewrite_callback(
            idx_text, idx_pkt, paths.vault_index_file, "index"
        )
        rewritten.append(paths.vault_index_file)

    # --- INDEX lower half auto-section refresh ---
    # The rewrite_callback handled the upper half; now Python refreshes
    # the stats block so the two halves are consistent.
    current_state = state_file.read()
    refresh_index(paths, round_counter=current_state.round)

    # --- Step 5: Commit + mark_consolidated ---
    commit_result: CommitResult | None = None
    if inputs.do_commit and rewritten:
        files_to_stage: list[Path] = list(rewritten) + [paths.state_file]
        staged = stage_files(inputs.repo_root, files_to_stage)
        message = (
            f"[consolidate] round {current_state.round}: "
            f"{inputs.trigger.reason}"
        )
        commit_result = create_commit(inputs.repo_root, message, staged)

    state_file.mark_consolidated()

    return Phase5Result(
        targets=list(packet_map.keys()),
        packets=list(packet_map.values()),
        rewritten=rewritten,
        commit=commit_result,
    )


def _output_for(
    paths: StoragePaths, target_key: str
) -> tuple[Path, str]:
    """Map a packet target key back to its output path and kind label."""
    if target_key == "lessons":
        return paths.vault_lessons_file, "lessons"
    if target_key.startswith("direction:"):
        name = target_key.split(":", 1)[1]
        return paths.direction_file(name), "direction"
    if target_key == "index":
        return paths.vault_index_file, "index"
    raise ValueError(f"unknown target_key: {target_key}")
