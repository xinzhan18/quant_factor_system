"""Phase 4 ARCHIVE orchestrator — the Python (synchronous) side.

Step layout per refactor_plan §8:

1. **Python (sync)** — allocate F{id}, write factor.yaml, archive
   Python source if applicable.
2. **Python (sync)** — generate report packet (deferred to P5).
3. **Subagent (async, deferred to P5)** — write factor.md in the
   background via sandboxed subagent.
4. **LLM (sync)** — update direction.md (handled by the autonomous
   mine loop, not this orchestrator).
5. **Python (sync)** — refresh INDEX.md, advance state, create the
   main git commit.

P4 (this Part) implements Steps 1, 5, and the phase-state transition.
Step 3 is wired in P5. Step 4 is the LLM's job.

Idempotency (Q32): this orchestrator calls
``StateFile.transition_phase("archived")`` before doing any work, which
raises :class:`research.storage.state.InvalidPhaseTransition` if the
batch is already archived. Double-archive is therefore impossible —
the exception propagates to the mine loop.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from research.archive.commit import (
    CommitResult,
    build_commit_message,
    create_commit,
    stage_files,
)
from research.archive.factor_writer import (
    AllocatedFactor,
    allocate_and_write_factor,
)
from research.archive.python_archiver import archive_python_factor
from research.memory.direction_updater import update_direction_frontmatter
from research.memory.index_refresher import refresh_index
from research.storage.paths import StoragePaths
from research.storage.state import StateFile
from research.storage.yaml_io import load_yaml, load_yaml_unsafe

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Inputs + result
# ---------------------------------------------------------------------------


@dataclass
class Phase4Inputs:
    """Everything Phase 4 needs to archive a single batch."""

    batch_id: str
    direction: str
    paths: StoragePaths
    repo_root: Path
    do_commit: bool = True
    """If False, archive without running git commit (useful for tests)."""


@dataclass
class Phase4Result:
    """What the orchestrator returns after archiving."""

    batch_id: str
    admitted: list[AllocatedFactor] = field(default_factory=list)
    python_archives: list[Path] = field(default_factory=list)
    index_path: Path | None = None
    direction_frontmatter: dict[str, Any] | None = None
    commit: CommitResult | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_judge_frontmatter(judge_md_path: Path) -> dict[str, Any]:
    """Read just the frontmatter from a judge.md (audited elsewhere)."""
    import re
    import yaml as _yaml

    text = judge_md_path.read_text(encoding="utf-8")
    m = re.match(r"\A---\s*\n(?P<fm>.*?)\n---\s*\n", text, re.DOTALL)
    if not m:
        raise RuntimeError(
            f"judge.md at {judge_md_path} has no frontmatter — run Phase 3 audit first"
        )
    return _yaml.safe_load(m.group("fm")) or {}


def _find_admits(judge_frontmatter: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        c
        for c in (judge_frontmatter.get("candidates") or [])
        if c.get("verdict") == "admit"
    ]


def _manifest_entry_by_id(
    manifest: dict[str, Any], candidate_id: str
) -> dict[str, Any]:
    for c in manifest.get("candidates") or []:
        if c.get("candidate_id") == candidate_id:
            return c
    return {}


def _result_entry_by_id(
    result: dict[str, Any], candidate_id: str
) -> dict[str, Any]:
    for c in result.get("candidates") or []:
        if c.get("candidate_id") == candidate_id:
            return c
    return {}


def _sanitize_name(name: str) -> str:
    """Safe name for ``python_factors/F{id}_{name}.py``."""
    import re

    s = re.sub(r"[^a-zA-Z0-9_]+", "_", name)
    return s.strip("_") or "factor"


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_phase4_archive(inputs: Phase4Inputs) -> Phase4Result:
    """Run the synchronous side of Phase 4 and return a structured result.

    Preconditions enforced:

    * ``result.yaml`` exists in the batch dir
    * ``judge.md`` exists and has frontmatter (audit should have run)
    * ``state.yaml`` current_batch == inputs.batch_id and phase == "judged"
      (otherwise transition_phase raises)
    """
    paths = inputs.paths
    batch_dir = paths.batch_dir(inputs.batch_id)
    result_path = paths.batch_result_file(inputs.batch_id)
    judge_path = paths.batch_judge_file(inputs.batch_id)

    if not result_path.exists():
        raise FileNotFoundError(f"phase4: result.yaml missing at {result_path}")
    if not judge_path.exists():
        raise FileNotFoundError(f"phase4: judge.md missing at {judge_path}")

    # Transition first — InvalidPhaseTransition raised on Q32 double-archive
    state_file = StateFile(paths.state_file)
    state_file.transition_phase("archived")

    result = load_yaml_unsafe(result_path)
    manifest = load_yaml(paths.batch_manifest_file(inputs.batch_id))
    judge_fm = _parse_judge_frontmatter(judge_path)

    admits = _find_admits(judge_fm)
    logger.info(
        "phase4: %s has %d admits to archive", inputs.batch_id, len(admits)
    )

    archived: list[AllocatedFactor] = []
    py_archives: list[Path] = []
    sample_policy_version = result.get("sample_policy_version", "v3")

    for admit in admits:
        cid = admit["candidate_id"]
        result_entry = _result_entry_by_id(result, cid)
        manifest_entry = _manifest_entry_by_id(manifest, cid)

        allocated = allocate_and_write_factor(
            factors_dir=paths.factors_dir,
            admit_entry=result_entry,
            manifest_entry=manifest_entry,
            batch_id=inputs.batch_id,
            direction=inputs.direction,
            sample_policy_version=sample_policy_version,
        )
        archived.append(allocated)

        if allocated.record.get("source_type") == "python":
            py_path = allocated.record.get("python_path")
            if py_path:
                src = batch_dir / "python_candidates" / Path(py_path).name
                name = _sanitize_name(
                    allocated.record.get("name", allocated.factor_id)
                )
                dst = archive_python_factor(
                    src, paths.python_factors_dir, allocated.factor_id, name
                )
                py_archives.append(dst)

    # --- Update direction frontmatter ---
    new_ids = [a.factor_id for a in archived]
    direction_path = paths.direction_file(inputs.direction)
    direction_fm = update_direction_frontmatter(
        direction_path,
        batch_id=inputs.batch_id,
        new_admits=new_ids,
        goal=manifest.get("batch_goal"),
    )

    # --- Refresh INDEX.md lower half ---
    current_state = state_file.read()
    index_path = refresh_index(
        paths,
        round_counter=current_state.round,
        last_consolidation_round=None,
    )

    # --- Commit ---
    commit_result: CommitResult | None = None
    if inputs.do_commit:
        files_to_stage = [
            paths.state_file,
            paths.vault_index_file,
            direction_path,
        ]
        for a in archived:
            files_to_stage.append(a.yaml_path)
        for py in py_archives:
            files_to_stage.append(py)

        summary = judge_fm.get("batch_summary") or {}
        message = build_commit_message(
            batch_id=inputs.batch_id,
            direction=inputs.direction,
            n_admit=int(summary.get("admit", len(archived))),
            n_reserve=int(summary.get("reserve", 0)),
            n_reject=int(summary.get("reject", 0)),
            factor_ids=new_ids,
            batch_goal=manifest.get("batch_goal", ""),
        )
        staged = stage_files(inputs.repo_root, files_to_stage)
        commit_result = create_commit(inputs.repo_root, message, staged)

    # --- Finish batch (clears current_batch, increments round) ---
    state_file.finish_batch()

    return Phase4Result(
        batch_id=inputs.batch_id,
        admitted=archived,
        python_archives=py_archives,
        index_path=index_path,
        direction_frontmatter=direction_fm,
        commit=commit_result,
    )
