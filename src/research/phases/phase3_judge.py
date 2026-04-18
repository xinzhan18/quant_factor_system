"""Phase 3 JUDGE orchestrator (graph-judge schema).

Post-refactor, Phase 3 has two CLI-driven Python steps with the LLM's
subagent work happening in between:

1. ``research judge batch_N pre-hint`` — build and write ``_hints.yaml``
   (hard gates + §7.MT counts + per-candidate mt_budget).
2. *(LLM main agent dispatches per-candidate subagents that write*
   ``candidates/C{id}.md`` *then main agent writes* ``judge.md``.)
3. ``research judge batch_N audit`` — run ``audit_batch_judge`` on the
   written artifacts.

This module provides ``run_phase3_prehint(inputs)`` which performs step 1
purely. The old ``run_phase3`` (packet + LLM callback + audit pipeline)
is deleted — no production caller used it, and the new flow is
CLI-driven from ``/factor-judge``.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path

from research.checkpoints.hard_gates import HardGatesConfig
from research.checkpoints.hints import build_hints, write_hints
from research.checkpoints.mt_budget import MtBudgetConfig
from research.storage.yaml_io import load_yaml_unsafe

logger = logging.getLogger(__name__)


@dataclass
class Phase3PreHintInputs:
    """Inputs needed to produce ``_hints.yaml`` for one batch."""

    batch_id: str
    direction: str
    batch_dir: Path
    """``storage/vault/batches/batch_{id}/`` — contains result.yaml."""

    batches_root: Path
    """``storage/vault/batches/`` — scanned for §7.MT counts."""

    hints_path: Path
    """Destination for the written ``_hints.yaml``."""

    factors_dir: Path | None = None
    """``storage/vault/factors/`` — used to resolve nearest_factor_expression."""

    hard_gates_config: HardGatesConfig = field(default_factory=HardGatesConfig)
    mt_budget_config: MtBudgetConfig = field(default_factory=MtBudgetConfig)


@dataclass
class Phase3PreHintResult:
    hints_path: Path
    hints: dict


def run_phase3_prehint(inputs: Phase3PreHintInputs) -> Phase3PreHintResult:
    """Produce and persist ``_hints.yaml`` for a single batch.

    Raises
    ------
    FileNotFoundError
        If ``result.yaml`` is missing for the batch.
    """
    result_path = inputs.batch_dir / "result.yaml"
    if not result_path.exists():
        raise FileNotFoundError(
            f"phase3: result.yaml missing at {result_path} — run Phase 2 first"
        )
    result = load_yaml_unsafe(result_path)
    hints = build_hints(
        batch_id=inputs.batch_id,
        direction=inputs.direction,
        result=result,
        batches_dir=inputs.batches_root,
        hard_gates_config=inputs.hard_gates_config,
        mt_budget_config=inputs.mt_budget_config,
        factors_dir=inputs.factors_dir,
    )
    write_hints(inputs.hints_path, hints)
    n_failed = sum(
        1 for e in hints["per_candidate"].values()
        if not e.get("hard_gate", {}).get("passed")
    )
    n_total = len(hints["per_candidate"])
    logger.info(
        "phase3 pre-hint: %s: %d/%d hard-gate fails; hints written to %s",
        inputs.batch_id,
        n_failed,
        n_total,
        inputs.hints_path,
    )
    return Phase3PreHintResult(hints_path=inputs.hints_path, hints=hints)
