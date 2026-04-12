"""``research mine`` main loop — linear 5-phase autonomous driver.

Driven by the autonomous mine mode (CLAUDE.md "Autonomous Mining Mode"):
no user prompts mid-loop; only system errors halt execution. Each call
to :func:`run_mine_once` runs exactly **one** batch end-to-end and
returns a structured result so the outer loop can decide whether to
continue.

Phase transitions (with callbacks for the LLM-driven steps):

1. **Phase 1 START+DESIGN** — build manifest from caller-supplied
   candidates. Caller is the LLM mine skill; in tests it's a canned
   callable.
2. **Phase 2 EXECUTE** — vectorized compute. Always pure Python.
3. **Phase 3 JUDGE** — hard gates + pre-pack + LLM callback + audit.
4. **Phase 4 ARCHIVE** — allocate F{id}, write factor.yaml + direction
   md updates + INDEX refresh + optional report subagent dispatch +
   main git commit.
5. **Phase 5 CONSOLIDATION (conditional)** — fires when the trigger
   check returns non-None; parallel subagent rewrites; second commit.

Every callback is injected so this module is test-friendly and
production-independent. Production wires them to Claude Code subagent
dispatches; tests pass plain Python functions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from research.checkpoints.generator import PacketContext
from research.checkpoints.mt_budget import MtBudgetConfig
from research.phases.phase1_start import FreezeReport, freeze_manifest
from research.phases.phase3_judge import (
    LlmJudgeCallback,
    Phase3Inputs,
    Phase3Result,
    run_phase3,
)
from research.phases.phase4_archive import (
    Phase4Inputs,
    Phase4Result,
    ReportCallback,
    run_phase4_archive,
)
from research.phases.phase5_consolidate import (
    ConsolidationTrigger,
    Phase5Inputs,
    Phase5Result,
    check_triggers,
    run_phase5_consolidation,
)
from research.storage.paths import StoragePaths
from research.storage.state import StateFile
from research.storage.yaml_io import load_yaml

logger = logging.getLogger(__name__)


# Signature: given a batch context dict, return the list of candidates
# the LLM wants to submit. Production = Claude Code subagent; test = fn.
CandidateSupplier = Callable[[dict[str, Any]], list[dict[str, Any]]]

# Phase2ExecutorCallback runs Phase 2 EXECUTE. Injecting this is the
# cleanest way to keep mine.py free of the DB/Qlib data-loading details
# that are out of P1/P6 scope. Production wires it to the real Phase 2
# orchestrator; tests pass a closure that writes a canned result.yaml.
Phase2ExecutorCallback = Callable[[str, StoragePaths], None]


@dataclass
class MineInputs:
    """Inputs to :func:`run_mine_once`."""

    paths: StoragePaths
    repo_root: Path
    direction: str
    batch_goal: str
    existing_canonicals: list[str]
    sample_policy_version: str = "v3"

    # Callbacks
    candidate_supplier: CandidateSupplier = None  # type: ignore[assignment]
    phase2_executor: Phase2ExecutorCallback = None  # type: ignore[assignment]
    llm_judge_callback: LlmJudgeCallback = None  # type: ignore[assignment]
    report_callback: ReportCallback | None = None
    phase5_rewrite_callback: Any = None

    # Options
    do_commit: bool = True
    mt_budget_config: MtBudgetConfig = field(default_factory=MtBudgetConfig)
    direction_excerpt: str = ""


@dataclass
class MineRunResult:
    batch_id: str
    phase1: FreezeReport
    phase3: Phase3Result
    phase4: Phase4Result
    phase5: Phase5Result | None = None


def _next_batch_id(batches_dir: Path) -> str:
    """Return the next ``batch_{NNN}`` id based on existing directories."""
    existing: list[int] = []
    if batches_dir.exists():
        for d in batches_dir.iterdir():
            if d.is_dir() and d.name.startswith("batch_"):
                try:
                    existing.append(int(d.name.split("_", 1)[1]))
                except ValueError:
                    continue
    n = max(existing) + 1 if existing else 1
    return f"batch_{n:03d}"


def run_mine_once(inputs: MineInputs) -> MineRunResult:
    """Run exactly one mine cycle: Phase 1 → 2 → 3 → 4 → (maybe 5).

    Raises any downstream exception as-is so the mine loop can decide
    whether the failure is recoverable.
    """
    paths = inputs.paths
    batch_id = _next_batch_id(paths.batches_dir)

    # --- Transition state to designed ---
    state_file = StateFile(paths.state_file)
    state_file.begin_batch(batch_id)

    # --- Phase 1: ask the caller for candidates, then freeze ---
    ctx = {
        "batch_id": batch_id,
        "direction": inputs.direction,
        "batch_goal": inputs.batch_goal,
    }
    candidates = inputs.candidate_supplier(ctx)
    manifest_path = paths.batch_manifest_file(batch_id)
    phase1_report = freeze_manifest(
        batch_id=batch_id,
        direction=inputs.direction,
        batch_goal=inputs.batch_goal,
        candidates=candidates,
        existing_canonicals=inputs.existing_canonicals,
        manifest_path=manifest_path,
        sample_policy_version=inputs.sample_policy_version,
    )

    # --- Phase 2: EXECUTE (injected) ---
    state_file.transition_phase("executing")
    inputs.phase2_executor(batch_id, paths)

    # --- Phase 3: JUDGE ---
    state_file.transition_phase("judged")
    phase3_inputs = Phase3Inputs(
        batch_id=batch_id,
        direction=inputs.direction,
        batch_dir=paths.batch_dir(batch_id),
        batches_root=paths.batches_dir,
        context=PacketContext(),
        current_sample_policy_version=inputs.sample_policy_version,
        packet_refs=set(),
        mt_budget_config=inputs.mt_budget_config,
    )
    phase3_result = run_phase3(phase3_inputs, inputs.llm_judge_callback)

    # --- Phase 4: ARCHIVE ---
    phase4_inputs = Phase4Inputs(
        batch_id=batch_id,
        direction=inputs.direction,
        paths=paths,
        repo_root=inputs.repo_root,
        do_commit=inputs.do_commit,
        direction_excerpt=inputs.direction_excerpt,
        report_callback=inputs.report_callback,
    )
    phase4_result = run_phase4_archive(phase4_inputs)

    # --- Phase 5: CONSOLIDATION (conditional) ---
    phase5_result: Phase5Result | None = None
    config_dict = load_yaml(paths.config_file) or {}
    auto_triggers = (config_dict.get("consolidation") or {}).get(
        "auto_triggers", {}
    )
    current_state = state_file.read()
    trigger = check_triggers(
        paths,
        auto_triggers=auto_triggers,
        rounds_since_last=current_state.rounds_since_last_consolidation,
    )
    if trigger is not None and inputs.phase5_rewrite_callback is not None:
        phase5_inputs = Phase5Inputs(
            paths=paths,
            repo_root=inputs.repo_root,
            trigger=trigger,
            rewrite_callback=inputs.phase5_rewrite_callback,
            do_commit=inputs.do_commit,
        )
        phase5_result = run_phase5_consolidation(phase5_inputs)

    return MineRunResult(
        batch_id=batch_id,
        phase1=phase1_report,
        phase3=phase3_result,
        phase4=phase4_result,
        phase5=phase5_result,
    )
