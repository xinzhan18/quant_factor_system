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
from typing import Any, Callable

from research.archive.backfill import (
    backfill_candidate_md,
    backfill_direction_md,
    backfill_judge_md,
)
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
from research.archive.report_packer import (
    ReportPacketInputs,
    cleanup_finished_packets,
    extract_candidate_synthesis,
    write_report_packet,
)
from research.memory.direction_updater import update_direction_frontmatter
from research.memory.index_refresher import refresh_index
from research.storage.paths import StoragePaths
from research.storage.state import StateFile
from research.storage.yaml_io import load_yaml, load_yaml_unsafe

# Subagent dispatch callback signature:
#
#   report_callback(packet_text, packet_path, factor_md_path) -> None
#
# Production wires this to a Claude Code subagent dispatch; tests pass
# a plain Python function. The "sandbox" aspect (one input, one output,
# no DB/Qlib) is enforced by the caller layer, not this module.
ReportCallback = Callable[[str, Path, Path], None]

# Chart builder callback signature:
#
#   chart_builder(factor_id, assets_dir) -> list[str]
#
# Runs the heavy Qlib/DB computation (report.render.render_factor)
# that produces ``vault/factors/F{id}/`` PNG charts + manifest.
# Returns the list of chart basenames (no extension) for packet embedding.
# Injection point: production wires it to :func:`report.render.render_factor`;
# tests pass ``None`` to skip chart generation entirely.
ChartBuilderCallback = Callable[[str, Path], list[str]]

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

    direction_excerpt: str = ""
    """Optional direction md excerpt to include in the report packet."""

    report_callback: ReportCallback | None = None
    """Optional Phase 4 Step 3 subagent dispatch. If None, report packets
    are still written but factor.md is not — useful for tests and for
    running Phase 4 without the report layer (e.g. during bootstrap)."""

    chart_builder: ChartBuilderCallback | None = None
    """Optional Phase 4 Step 2 heavy-compute hook. When provided, runs
    ``report.render.render_factor`` to produce ``vault/factors/F{id}/``
    PNG charts + manifest. The returned chart list is embedded in the
    packet so the subagent knows which images are safe to wikilink. Any
    exception is logged and treated as "no charts" — the main archive
    commit must not be blocked by chart-generation failure."""


@dataclass
class Phase4Result:
    """What the orchestrator returns after archiving."""

    batch_id: str
    admitted: list[AllocatedFactor] = field(default_factory=list)
    python_archives: list[Path] = field(default_factory=list)
    index_path: Path | None = None
    direction_frontmatter: dict[str, Any] | None = None
    commit: CommitResult | None = None
    report_packets: list[Path] = field(default_factory=list)
    factor_md_paths: list[Path] = field(default_factory=list)


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


# Retention policy: admits permanent, non-admits keep current + 2 prior batches.
DIAGNOSTICS_RETENTION_BATCHES = 3


def _admitted_ids_for_batch(paths: StoragePaths, batch_id: str) -> set[str]:
    """Return candidate IDs admitted in a batch by reading its judge.md.

    Returns ``set()`` for batches without a judge.md (e.g. not yet
    judged) — nothing is deleted in that case. This is conservative by
    design: missing evidence → keep data.
    """
    try:
        judge_path = paths.batch_judge_file(batch_id)
        if not judge_path.exists():
            return set()
        fm = _parse_judge_frontmatter(judge_path)
    except Exception:  # noqa: BLE001 — never block archive on retention
        return set()
    return {
        c.get("candidate_id", "")
        for c in (fm.get("candidates") or [])
        if c.get("verdict") == "admit"
    }


def _prune_non_admit_diagnostics(
    paths: StoragePaths,
    current_batch_id: str,
    retention: int = DIAGNOSTICS_RETENTION_BATCHES,
) -> list[Path]:
    """Delete non-admit candidate diagnostics older than ``retention`` batches.

    Sorts batch dirs lexicographically (assumes ``batch_NNN`` monotone
    pad-3 IDs) and deletes every non-admit candidate subdir in batches
    strictly older than the last ``retention`` batches ending at
    ``current_batch_id``. Admitted candidates are never deleted.

    Returns the list of deleted directories for audit logging.
    """
    import shutil

    root = paths.batch_diagnostics_root
    if not root.exists():
        return []

    all_batches = sorted(
        [p.name for p in root.iterdir() if p.is_dir() and p.name.startswith("batch_")]
    )
    if not all_batches:
        return []

    # Keep the last `retention` batches up to and including current_batch_id.
    # Anything older is eligible for non-admit pruning.
    if current_batch_id in all_batches:
        cutoff_idx = all_batches.index(current_batch_id) - retention + 1
    else:
        cutoff_idx = len(all_batches) - retention + 1
    eligible = all_batches[:cutoff_idx] if cutoff_idx > 0 else []

    deleted: list[Path] = []
    for batch_id in eligible:
        batch_diag_dir = paths.batch_diagnostics_dir(batch_id)
        if not batch_diag_dir.exists():
            continue
        admitted_ids = _admitted_ids_for_batch(paths, batch_id)
        for cand_dir in list(batch_diag_dir.iterdir()):
            if not cand_dir.is_dir():
                continue
            if cand_dir.name in admitted_ids:
                continue
            try:
                shutil.rmtree(cand_dir)
                deleted.append(cand_dir)
            except OSError as exc:
                logger.warning("phase4: failed to prune %s: %s", cand_dir, exc)
        # If the whole batch dir is empty (all candidates pruned), remove it
        try:
            if not any(batch_diag_dir.iterdir()):
                batch_diag_dir.rmdir()
        except OSError:
            pass
    return deleted


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

    hints_path = paths.batch_hints_file(inputs.batch_id)
    hints_per_cand: dict[str, dict[str, Any]] = {}
    if hints_path.exists():
        hints_doc = load_yaml(hints_path) or {}
        hints_per_cand = hints_doc.get("per_candidate") or {}

    admits = _find_admits(judge_fm)
    logger.info(
        "phase4: %s has %d admits to archive", inputs.batch_id, len(admits)
    )

    archived: list[AllocatedFactor] = []
    py_archives: list[Path] = []

    for admit in admits:
        cid = admit["candidate_id"]
        result_entry = _result_entry_by_id(result, cid)
        manifest_entry = _manifest_entry_by_id(manifest, cid)
        factor_name = admit.get("factor_name")

        allocated = allocate_and_write_factor(
            factors_dir=paths.factors_dir,
            admit_entry=result_entry,
            manifest_entry=manifest_entry,
            batch_id=inputs.batch_id,
            direction=inputs.direction,
            factor_name=factor_name,
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

    # --- Back-fill F{id} into Phase 3 artifacts (candidates/judge/direction) ---
    # Surgical Python edits — must run AFTER allocation (fid known) and
    # BEFORE packet write so downstream consumers see the fills.
    cand_to_fid: dict[str, str] = {
        admits[i]["candidate_id"]: archived[i].factor_id
        for i in range(len(archived))
    }
    for cid, fid in cand_to_fid.items():
        cand_path = paths.batch_candidate_md_file(inputs.batch_id, cid)
        if cand_path.exists():
            backfill_candidate_md(cand_path, fid)
    if cand_to_fid:
        judge_path_for_backfill = paths.batch_judge_file(inputs.batch_id)
        if judge_path_for_backfill.exists():
            backfill_judge_md(judge_path_for_backfill, cand_to_fid)
        dir_path_for_backfill = paths.direction_file(inputs.direction)
        if dir_path_for_backfill.exists():
            backfill_direction_md(
                dir_path_for_backfill, cand_to_fid, inputs.batch_id
            )

    # --- Step 2b: heavy-compute charts + Step 3 packet + optional subagent ---
    report_packets: list[Path] = []
    factor_md_paths: list[Path] = []
    for a in archived:
        # --- Chart generation (report.render.render_factor) ---
        # Runs BEFORE packet write so the chart list can be embedded.
        # Must never block the main commit — any failure → empty list.
        available_charts: list[str] = []
        if inputs.chart_builder is not None:
            assets_dir = paths.factor_assets_dir(a.factor_id)
            try:
                available_charts = list(
                    inputs.chart_builder(a.factor_id, assets_dir) or []
                )
            except Exception as exc:
                logger.warning(
                    "phase4: chart_builder failed for %s: %s — "
                    "packet will list no charts",
                    a.factor_id, exc,
                )

        packet_path = batch_dir / "_packets" / f"report_packet_{a.factor_id}.md"
        # Match admit entry by same index (admits list is ordered the
        # same way we iterated in the allocation loop above, so this
        # lines up positionally)
        idx = archived.index(a)
        admit_entry = admits[idx] if idx < len(admits) else {}
        synthesis = extract_candidate_synthesis(
            paths.batch_candidate_md_file(
                inputs.batch_id, admit_entry.get("candidate_id", "")
            )
        )
        cand_hints = hints_per_cand.get(admit_entry.get("candidate_id", ""), {})
        packet_text = write_report_packet(
            ReportPacketInputs(
                factor_id=a.factor_id,
                factor_record=a.record,
                direction=inputs.direction,
                direction_excerpt=inputs.direction_excerpt,
                judge_synthesis=synthesis,
                admitted_in_batch=inputs.batch_id,
                available_charts=available_charts,
                hints_per_candidate=cand_hints,
            ),
            packet_path,
        )
        report_packets.append(packet_path)

        factor_md_path = paths.factor_md_file(a.factor_id)
        factor_md_paths.append(factor_md_path)
        if inputs.report_callback is not None:
            inputs.report_callback(packet_text, packet_path, factor_md_path)

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

    # --- Diagnostics retention: admits permanent, non-admits keep 3 batches ---
    pruned = _prune_non_admit_diagnostics(paths, inputs.batch_id)
    if pruned:
        logger.info(
            "phase4: pruned %d non-admit diagnostic dirs under batch_diagnostics/",
            len(pruned),
        )

    # --- Packet cleanup: delete scratch packets whose factor.md now exists ---
    # Skip the current batch — its subagents may still be running and reading
    # their packets. Prior batches' subagents have had time to finish.
    cleaned_packets = cleanup_finished_packets(paths, skip_batch=inputs.batch_id)
    if cleaned_packets:
        logger.info(
            "phase4: cleaned %d finished report packet(s)", len(cleaned_packets)
        )

    # --- Finish batch (clears current_batch, increments round) ---
    state_file.finish_batch()

    return Phase4Result(
        batch_id=inputs.batch_id,
        admitted=archived,
        python_archives=py_archives,
        index_path=index_path,
        direction_frontmatter=direction_fm,
        commit=commit_result,
        report_packets=report_packets,
        factor_md_paths=factor_md_paths,
    )
