"""Phase 5 CONSOLIDATION orchestrator.

Rewrites the LLM-maintained markdown (lessons.md, directions/*.md)
on a periodic schedule when one of the trigger
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
   for each rewrite target (one per direction + one for lessons).
3. **Subagent rewrites** — parallel dispatch via the injected
   ``rewrite_callback``. Each callback invocation receives one packet
   and writes one markdown file.
4. **INDEX refresh** — Python regenerates the MOC/cockpit skeleton and
   preserves the valid HOT-TOPICS-LLM block.
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
from research.memory.finding_filter import (
    FindingMeta,
    findings_for_direction,
    findings_for_lessons,
    load_findings,
    touched_directions,
)
from research.memory.index_refresher import refresh_index
from research.storage.paths import StoragePaths
from research.storage.state import StateFile

logger = logging.getLogger(__name__)

# rewrite_callback(packet_text, packet_path, output_path, target_kind)
#
# - packet_text: the full _consolidation/packet_{...}.md string
# - packet_path: where the packet lives (single input)
# - output_path: where to write the rewritten md
# - target_kind: "lessons" | "direction" — lets the subagent
#   apply different rewrite templates
RewriteCallback = Callable[[str, Path, Path, str], None]

# specialist_callback(packet_text, packet_path, findings_dir, specialist_name)
#
# - Used for Phase-5 Stage-A distillation. The subagent reads the packet
#   and writes one or more ``F00N.md`` files into ``findings_dir``. Return
#   value is ignored — orchestrator re-scans the dir afterward.
# - ``specialist_name`` is one of ``pattern_analyst``, ``library_gap``,
#   ``calibration``, ``hypothesis_promoter``.
SpecialistCallback = Callable[[str, Path, Path, str], None]

SPECIALIST_NAMES: tuple[str, ...] = (
    "pattern_analyst",
    "library_gap",
    "calibration",
    "hypothesis_promoter",
)


class Phase5PreconditionError(RuntimeError):
    """Raised when consolidation preconditions are not met."""


@dataclass
class ConsolidationTrigger:
    """Why consolidation fired — used in commit message and logs."""

    reason: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class Phase5Inputs:
    """Everything Phase 5 needs.

    Backward-compatible: if ``specialist_callback`` is ``None`` the
    orchestrator runs the **legacy single-stage flow** (all directions
    rewritten, one packet per). When ``specialist_callback`` is provided,
    the new **two-stage flow** runs: 4 distillation specialists first
    produce ``_consolidation/findings/*.md``, then writer dispatch is
    scoped to only the directions those findings touch.
    """

    paths: StoragePaths
    repo_root: Path
    trigger: ConsolidationTrigger
    rewrite_callback: RewriteCallback | None = None
    specialist_callback: SpecialistCallback | None = None
    do_commit: bool = True


@dataclass
class Phase5Result:
    targets: list[str]
    packets: list[Path]
    rewritten: list[Path]
    findings: list[Path] = field(default_factory=list)
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


def _findings_section(findings: list[FindingMeta]) -> str:
    """Inline the full body of each finding into a packet section.

    Writers consume findings as prose — frontmatter is machine metadata.
    Emit ``## Related findings`` only when the list is non-empty so
    packets for directions without findings stay tight.
    """
    if not findings:
        return ""
    chunks = ["## Related findings (from distillation specialists)\n"]
    for f in findings:
        # Read body directly from disk so the section shows exactly what
        # the specialist subagent wrote.
        try:
            raw = f.path.read_text(encoding="utf-8")
        except OSError:
            continue
        chunks.append(f"### {f.finding_id} · severity={f.severity}\n")
        chunks.append(raw)
        chunks.append("")
    return "\n".join(chunks)


def _build_packet_for_lessons(
    paths: StoragePaths, findings: list[FindingMeta] | None = None
) -> str:
    """Packet for the lessons writer — may include distilled findings."""
    body = ""
    if paths.vault_lessons_file.exists():
        body = paths.vault_lessons_file.read_text(encoding="utf-8")
    findings_block = _findings_section(findings or [])
    return (
        "# Consolidation Packet — lessons.md\n\n"
        "## Current content\n\n"
        f"{body}\n\n"
        + (findings_block + "\n\n" if findings_block else "")
        + "## Instructions\n\n"
        "Rewrite `vault/lessons.md` to remove redundant lessons and "
        "promote stable facts. Preserve Data Facts, Operator Registry, "
        "Path Selection, and Structural Constraints sections. If "
        "'Related findings' is present, integrate each finding's "
        "`suggested_lesson_text` (if any) into the appropriate existing "
        "section — do not create a new section just for findings. "
        "Target length < 400 lines.\n"
    )


def _build_packet_for_direction(
    paths: StoragePaths,
    direction: str,
    findings: list[FindingMeta] | None = None,
) -> str:
    """Packet for one direction writer. Optionally includes related findings."""
    md_path = paths.direction_file(direction)
    body = md_path.read_text(encoding="utf-8") if md_path.exists() else ""
    findings_block = _findings_section(findings or [])
    return (
        f"# Consolidation Packet — directions/{direction}.md\n\n"
        "## Current content\n\n"
        f"{body}\n\n"
        + (findings_block + "\n\n" if findings_block else "")
        + "## Instructions\n\n"
        "Rewrite this direction md to compress long narrative logs, "
        "dedupe threads, and preserve Hypothesis + active Threads + "
        "Narrative Log (truncated to most recent 20 entries). If "
        "'Related findings' is present, use it to decide which narrative "
        "entries to promote / remove (e.g. a high-severity finding that "
        "names this direction implies the related failure should be "
        "upgraded to Hypothesis ⚠️). Do not touch the frontmatter — "
        "Python manages that.\n"
    )


# --- Specialist packets (Stage A of 2-stage flow) -------------------------

def _recent_judge_bodies(paths: StoragePaths, limit: int = 10) -> str:
    """Concatenate recent judge.md bodies for specialist packets.

    Returns an empty string if no batches exist yet. Caller embeds this
    block into the specialist packet — kept as raw markdown so the LLM
    can navigate the judge structure it already knows.
    """
    if not paths.batches_dir.exists():
        return ""
    batch_dirs = sorted(
        (d for d in paths.batches_dir.glob("batch_*") if d.is_dir()),
        key=lambda d: d.name,
    )
    recent = batch_dirs[-limit:] if limit > 0 else batch_dirs
    chunks: list[str] = []
    for d in recent:
        judge = d / "judge.md"
        if not judge.exists():
            continue
        chunks.append(f"### {d.name}\n")
        chunks.append(judge.read_text(encoding="utf-8"))
        chunks.append("")
    return "\n".join(chunks)


def _all_direction_bodies(paths: StoragePaths) -> str:
    """Concatenate all direction.md bodies (frontmatter + body) for
    the hypothesis_promoter / pattern_analyst specialists."""
    if not paths.directions_dir.exists():
        return ""
    chunks: list[str] = []
    for md in sorted(paths.directions_dir.glob("*.md")):
        chunks.append(f"### {md.stem}")
        chunks.append(md.read_text(encoding="utf-8"))
        chunks.append("")
    return "\n".join(chunks)


def _all_factor_yaml_summary(paths: StoragePaths) -> str:
    """Compact summary of admitted factors — name + expression per line."""
    if not paths.factors_dir.exists():
        return ""
    lines: list[str] = ["| factor_id | name | expression |", "|---|---|---|"]
    import yaml as _yaml

    for y in sorted(paths.factors_dir.glob("F*.yaml")):
        try:
            data = _yaml.safe_load(y.read_text(encoding="utf-8")) or {}
        except Exception:
            continue
        lines.append(
            f"| {y.stem} | {data.get('name') or ''} "
            f"| `{data.get('expression') or ''}` |"
        )
    return "\n".join(lines)


def _build_specialist_packet_pattern_analyst(paths: StoragePaths) -> str:
    return (
        "# Distillation Packet — pattern_analyst\n\n"
        "## Task\n\n"
        "Scan recent judge.md bodies + all direction bodies. Identify "
        "**cross-direction patterns** that recur (same dominant_style "
        "absorption, same rejection mechanism, same failure mode). Each "
        "pattern you surface must become one `{NNN}.md` in "
        "`storage/vault/_consolidation/findings/pattern_analyst/` "
        "(zero-padded 3-digit number, mkdir -p the subfolder if missing) "
        "with the frontmatter shape:\n\n"
        "```yaml\n---\n"
        "finding_id: 001               # plain digits; specialist namespace via path + field\n"
        "specialist: pattern_analyst\n"
        "severity: high|medium|low\n"
        "affected_directions: [...]\n"
        "touches_lessons: true|false\n"
        "batches_referenced: [...]\nsuggested_lesson_text: \"...\"\n"
        "---\n```\n\n"
        "## Recent judge.md bodies\n\n"
        f"{_recent_judge_bodies(paths)}\n\n"
        "## All direction bodies\n\n"
        f"{_all_direction_bodies(paths)}\n"
    )


def _build_specialist_packet_library_gap(paths: StoragePaths) -> str:
    return (
        "# Distillation Packet — library_gap\n\n"
        "## Task\n\n"
        "Inspect admitted factors + recent reject patterns. Identify "
        "**signal families that are structurally missing** from the "
        "library (e.g. 'all admitted factors are single-window; "
        "multi-horizon blends never tried'). Each gap becomes one "
        "`{NNN}.md` in "
        "`storage/vault/_consolidation/findings/library_gap/` "
        "(zero-padded, mkdir -p). Frontmatter must set "
        "`specialist: library_gap` and `finding_id` to the digits.\n\n"
        "## Admitted factors\n\n"
        f"{_all_factor_yaml_summary(paths)}\n\n"
        "## Recent judge.md bodies\n\n"
        f"{_recent_judge_bodies(paths)}\n"
    )


def _build_specialist_packet_calibration(paths: StoragePaths) -> str:
    from research.cli.audit_reserves import collect_reserves, render_report

    try:
        reserve_rows = collect_reserves(paths, refresh_uniqueness=False)
        reserve_audit = render_report(reserve_rows)
    except Exception as exc:  # noqa: BLE001 — best-effort packet enrichment
        reserve_audit = (
            f"_reserve audit unavailable: {type(exc).__name__}: {exc}_\n"
        )

    return (
        "# Distillation Packet — calibration\n\n"
        "## Task\n\n"
        "**Two perspectives are mandatory** — both must produce findings:\n\n"
        "**(A) Trigger-driven (recent batches)**: Scan recent judge.md "
        "`阈值校准诊断` sections. Identify **threshold tuning proposals** "
        "with concrete evidence (which threshold, current value, proposed "
        "value, which reserve candidates would have flipped).\n\n"
        "**(B) Asset-driven (full reserve pool retro triage)**: Process "
        "the `## Reserve Pool Retro Audit` section below — it lists "
        "**every** historical reserve re-evaluated under current "
        "config.yaml. For every `re-judge` flip-candidate row with "
        "ic_oos_clean + mono_strong flags, decide whether to "
        "**recommend revival** (via `suggested_revival_path`: change "
        "RHS basis / Python residualize / window sweep / etc.). "
        "Asset-driven findings do **not** propose threshold changes — "
        "they propose **revival paths** that work under current "
        "thresholds. This perspective catches single-edge-borderline "
        "candidates (e.g. only `incr_ic` NEG, only `max_corr` 0.40-0.50) "
        "that fail trigger-driven gates but have 4+ CP top-tier metrics.\n\n"
        "Each finding becomes one `{NNN}.md` in "
        "`storage/vault/_consolidation/findings/calibration/` "
        "(zero-padded, mkdir -p). Frontmatter must set "
        "`specialist: calibration` and `finding_id` to the digits. "
        "Severity reflects how many retro candidates would flip / "
        "how many revivals are recommended.\n\n"
        "**Required asset-driven coverage**: at least one finding "
        "must summarize the reserve-pool triage outcome — list top-N "
        "revival recommendations with concrete `suggested_revival_path` "
        "for each, even if zero threshold changes are proposed.\n\n"
        "## Recent judge.md bodies\n\n"
        f"{_recent_judge_bodies(paths)}\n\n"
        "## Reserve Pool Retro Audit (full history, current thresholds)\n\n"
        f"{reserve_audit}\n"
    )


def _build_specialist_packet_hypothesis_promoter(paths: StoragePaths) -> str:
    return (
        "# Distillation Packet — hypothesis_promoter\n\n"
        "## Task\n\n"
        "Scan direction bodies (especially `dead` / `saturated` statuses) "
        "for **hypothesis elements worth promoting to `lessons.md`** "
        "(reusable across future directions). Each promotion becomes one "
        "`{NNN}.md` in "
        "`storage/vault/_consolidation/findings/hypothesis_promoter/` "
        "(zero-padded, mkdir -p). Frontmatter must set "
        "`specialist: hypothesis_promoter`, `finding_id` to the digits, "
        "`touches_lessons: true`, and a concrete `suggested_lesson_text` "
        "(the exact prose to integrate).\n\n"
        "## All direction bodies\n\n"
        f"{_all_direction_bodies(paths)}\n"
    )


_SPECIALIST_BUILDERS: dict[str, Callable[[StoragePaths], str]] = {
    "pattern_analyst": _build_specialist_packet_pattern_analyst,
    "library_gap": _build_specialist_packet_library_gap,
    "calibration": _build_specialist_packet_calibration,
    "hypothesis_promoter": _build_specialist_packet_hypothesis_promoter,
}


def prepack_specialists(paths: StoragePaths) -> dict[str, Path]:
    """Write 4 distillation packets to ``_consolidation/``. Pure I/O."""
    consolidation_dir = paths.vault_meta_dir.parent / "_consolidation"
    consolidation_dir.mkdir(parents=True, exist_ok=True)
    (consolidation_dir / "findings").mkdir(exist_ok=True)

    out: dict[str, Path] = {}
    for name in SPECIALIST_NAMES:
        pkt = consolidation_dir / f"packet_specialist_{name}.md"
        pkt.write_text(_SPECIALIST_BUILDERS[name](paths), encoding="utf-8")
        out[name] = pkt
    return out


def prepack_consolidation(
    paths: StoragePaths,
    directions: Iterable[str] | None = None,
) -> dict[str, Path]:
    """Write all consolidation packets to ``_consolidation/`` and return paths.

    The returned dict maps ``target_kind`` (``"lessons"``,
    ``"direction:{name}"``) to the packet path.
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


def _backup_dir(paths: StoragePaths) -> Path:
    return paths.vault_meta_dir.parent / "_consolidation" / "backup"


def _backup_targets(paths: StoragePaths, targets: Iterable[Path]) -> dict[Path, Path]:
    """Copy each existing target md into _consolidation/backup/ keyed by path.

    Returns a map from original path → backup path. Missing targets are
    skipped (brand-new files are fine to write without a backup).
    """
    bdir = _backup_dir(paths)
    bdir.mkdir(parents=True, exist_ok=True)
    mapping: dict[Path, Path] = {}
    for i, tgt in enumerate(targets):
        if not tgt.exists():
            continue
        # Flatten paths — use index + stem so directions/vol.md and
        # lessons.md never collide.
        backup_path = bdir / f"{i:03d}_{tgt.name}"
        shutil.copy2(tgt, backup_path)
        mapping[tgt] = backup_path
    return mapping


def _restore_from_backup(mapping: dict[Path, Path]) -> None:
    """Copy backups back to their original paths."""
    for original, backup in mapping.items():
        if backup.exists():
            shutil.copy2(backup, original)


def run_phase5_consolidation(inputs: Phase5Inputs) -> Phase5Result:
    """Run all five Phase 5 steps end-to-end.

    Raises
    ------
    Phase5PreconditionError
        If state.current_batch is not None, git tree is dirty, or a
        stale ``_consolidation/backup/`` dir exists.
    Exception
        Any exception raised by ``rewrite_callback`` propagates after
        all partially-written files are restored from backup.
    """
    paths = inputs.paths
    backup_dir = _backup_dir(paths)

    # --- Step 1: Pre-checks ---
    state_file = StateFile(paths.state_file)
    failures = preconditions_ok(state_file, inputs.repo_root, backup_dir)
    if failures:
        raise Phase5PreconditionError(
            "phase5 preconditions failed: " + "; ".join(failures)
        )

    # Two-stage mode when a specialist callback is present; otherwise the
    # legacy single-stage flow (all directions rewritten).
    if inputs.specialist_callback is not None:
        return _run_two_stage(inputs, state_file, backup_dir)
    return _run_legacy(inputs, state_file, backup_dir)


def _run_legacy(
    inputs: Phase5Inputs, state_file: StateFile, backup_dir: Path
) -> Phase5Result:
    """Legacy single-stage flow: all directions rewritten. Kept for
    backward-compat; no findings, no per-direction filtering."""
    paths = inputs.paths
    packet_map = prepack_consolidation(paths)

    all_targets: list[Path] = []
    for target_key in packet_map:
        output_path, _ = _output_for(paths, target_key)
        all_targets.append(output_path)
    backup_map = _backup_targets(paths, all_targets)

    rewritten: list[Path] = []
    try:
        if inputs.rewrite_callback is not None:
            for target_key, pkt_path in packet_map.items():
                output_path, kind = _output_for(paths, target_key)
                pkt_text = pkt_path.read_text(encoding="utf-8")
                inputs.rewrite_callback(pkt_text, pkt_path, output_path, kind)
                rewritten.append(output_path)
    except Exception:
        logger.exception("phase5 rewrite failed — restoring from backup")
        _restore_from_backup(backup_map)
        raise

    return _finalize_consolidation(
        inputs,
        state_file,
        backup_dir,
        target_keys=list(packet_map.keys()),
        packet_paths=list(packet_map.values()),
        rewritten=rewritten,
        findings_files=[],
    )


def _run_two_stage(
    inputs: Phase5Inputs, state_file: StateFile, backup_dir: Path
) -> Phase5Result:
    """Stage A (4 specialists → findings) + Stage B (writers, scoped by
    findings.affected_directions). See Phase5Inputs docstring for flow
    rationale."""
    paths = inputs.paths
    consolidation_dir = paths.vault_meta_dir.parent / "_consolidation"
    findings_dir = consolidation_dir / "findings"

    # --- Stage A: specialists --------------------------------------------
    specialist_packets = prepack_specialists(paths)
    try:
        for name, pkt_path in specialist_packets.items():
            pkt_text = pkt_path.read_text(encoding="utf-8")
            # specialist_callback is guaranteed non-None (caller dispatched here)
            assert inputs.specialist_callback is not None
            inputs.specialist_callback(pkt_text, pkt_path, findings_dir, name)
    except Exception:
        logger.exception(
            "phase5 specialist dispatch failed — no writer targets touched "
            "yet, so no restoration needed"
        )
        # Findings dir may contain partial files but vault is untouched.
        # Leave findings for post-mortem; orchestrator's backup guard
        # catches any re-run attempt.
        raise

    findings: list[FindingMeta] = load_findings(findings_dir)

    # --- Stage B: compute writer targets from findings -------------------
    touched = touched_directions(findings)
    write_lessons = bool(findings_for_lessons(findings))

    # Backup only what we're about to overwrite.
    all_targets: list[Path] = []
    if write_lessons:
        all_targets.append(paths.vault_lessons_file)
    for d in touched:
        all_targets.append(paths.direction_file(d))
    backup_map = _backup_targets(paths, all_targets)

    # Pack writer packets with their filtered findings.
    writer_packets: dict[str, Path] = {}
    if write_lessons:
        lessons_pkt = consolidation_dir / "packet_lessons.md"
        lessons_pkt.write_text(
            _build_packet_for_lessons(
                paths, findings=findings_for_lessons(findings)
            ),
            encoding="utf-8",
        )
        writer_packets["lessons"] = lessons_pkt
    for d in touched:
        pkt = consolidation_dir / f"packet_direction_{d}.md"
        pkt.write_text(
            _build_packet_for_direction(
                paths, d, findings=findings_for_direction(d, findings)
            ),
            encoding="utf-8",
        )
        writer_packets[f"direction:{d}"] = pkt
    rewritten: list[Path] = []
    try:
        if inputs.rewrite_callback is not None:
            for target_key, pkt_path in writer_packets.items():
                output_path, kind = _output_for(paths, target_key)
                pkt_text = pkt_path.read_text(encoding="utf-8")
                inputs.rewrite_callback(pkt_text, pkt_path, output_path, kind)
                rewritten.append(output_path)
    except Exception:
        logger.exception("phase5 writer dispatch failed — restoring")
        _restore_from_backup(backup_map)
        raise

    findings_files = [f.path for f in findings]
    return _finalize_consolidation(
        inputs,
        state_file,
        backup_dir,
        target_keys=list(writer_packets.keys()),
        packet_paths=(
            list(specialist_packets.values()) + list(writer_packets.values())
        ),
        rewritten=rewritten,
        findings_files=findings_files,
    )


def _finalize_consolidation(
    inputs: Phase5Inputs,
    state_file: StateFile,
    backup_dir: Path,
    *,
    target_keys: list[str],
    packet_paths: list[Path],
    rewritten: list[Path],
    findings_files: list[Path],
) -> Phase5Result:
    """Common post-rewrite steps: refresh index, mark consolidated, commit,
    cleanup. Used by both legacy and two-stage flows so they share a single
    definition of 'what a successful consolidation commit looks like'."""
    paths = inputs.paths
    current_state = state_file.read()
    index_path = refresh_index(paths, round_counter=current_state.round)
    rewritten_with_index = list(rewritten)
    if index_path not in rewritten_with_index:
        rewritten_with_index.append(index_path)

    state_file.mark_consolidated()

    commit_result: CommitResult | None = None
    if inputs.do_commit and rewritten_with_index:
        files_to_stage: list[Path] = (
            list(rewritten_with_index) + list(findings_files) + [paths.state_file]
        )
        staged = stage_files(inputs.repo_root, files_to_stage)
        message = (
            f"[consolidate] round {current_state.round}: "
            f"{inputs.trigger.reason}"
        )
        commit_result = create_commit(inputs.repo_root, message, staged)

    if backup_dir.exists():
        shutil.rmtree(backup_dir, ignore_errors=True)

    return Phase5Result(
        targets=target_keys + (["index"] if "index" not in target_keys else []),
        packets=packet_paths,
        rewritten=rewritten_with_index,
        findings=findings_files,
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
