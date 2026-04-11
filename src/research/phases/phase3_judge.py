"""Phase 3 JUDGE orchestrator.

Runs the five-step judge pipeline from refactor_plan §7 (augmented with
§7.MT pre-pack step 2):

1. **Python hard gates** (CP01) — reject candidates that fail sign_flip /
   coverage / forbidden / sample_policy / compute_error. Collected as a
   list of :class:`HardGateResult` and fed into the packet.
2. **Pre-pack** — scan batches/ for §7.MT counts, compute mt_bucket per
   candidate, render ``_packets/judge_packet.md`` via
   :func:`checkpoints.generator.build_judge_packet`.
3. **LLM write** — the orchestrator does NOT invoke an LLM directly.
   Instead the caller passes a ``llm_judge_callback`` that takes the
   packet text and writes the ``judge.md`` file. In production this is a
   Claude Code subagent dispatch; in tests it's a Python function that
   composes a known-good judge.md so the pipeline is end-to-end
   exercisable without an LLM.
4. **Audit** — run :func:`checkpoints.audit.audit_judge_md` on the
   written file. Any :class:`JudgeAuditError` propagates so the main
   loop can ask for a rewrite.
5. **Cleanup** — the packet file is left in place by default (``debug``
   mode) so a human can inspect LLM inputs after a rewrite loop. Set
   ``cleanup_packet=True`` to remove it after a successful audit.

The orchestrator is single-batch and single-pass — no rewrite loop.
Rewrite retry logic lives one layer up in the autonomous mine CLI.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from research.checkpoints.audit import JudgeAuditError, ParsedJudgeMd, audit_judge_md
from research.checkpoints.generator import (
    PacketContext,
    PacketInputs,
    write_judge_packet,
)
from research.checkpoints.hard_gates import HardGateResult, evaluate_hard_gates
from research.checkpoints.mt_budget import MtBudgetConfig
from research.storage.yaml_io import load_yaml_unsafe

logger = logging.getLogger(__name__)


# ``llm_judge_callback(packet_text, judge_md_path, extra_refs)``:
#
# - ``packet_text``: the full ``judge_packet.md`` string the LLM should read
# - ``judge_md_path``: where to write ``judge.md``
# - ``extra_refs``: set[str] of packet-declared references the LLM may cite
#   (audit's ``_check_referenced_context`` uses this)
#
# Must write ``judge_md_path`` and return None.
LlmJudgeCallback = Callable[[str, Path, set[str]], None]


@dataclass
class Phase3Inputs:
    """Everything Phase 3 needs to judge a single batch."""

    batch_id: str
    direction: str
    batch_dir: Path
    """``storage/batches/batch_{id}/`` — result.yaml + _packets live here."""

    batches_root: Path
    """``storage/batches/`` — parent dir, passed to mt_budget scan."""

    context: PacketContext
    current_sample_policy_version: str
    packet_refs: set[str] = field(default_factory=set)
    """References the packet declares — audit enforces the LLM cites a subset."""

    mt_budget_config: MtBudgetConfig = field(default_factory=MtBudgetConfig)
    cleanup_packet: bool = False


@dataclass
class Phase3Result:
    """What the orchestrator returns to its caller."""

    gates: list[HardGateResult]
    packet_path: Path
    judge_md_path: Path
    parsed: ParsedJudgeMd


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


def run_phase3(
    inputs: Phase3Inputs,
    llm_judge_callback: LlmJudgeCallback,
) -> Phase3Result:
    """Run all five Phase 3 steps end-to-end.

    Raises
    ------
    FileNotFoundError
        If ``result.yaml`` is missing from the batch dir.
    JudgeAuditError
        If the LLM-written ``judge.md`` fails any of the six audit checks.
    """
    result_path = inputs.batch_dir / "result.yaml"
    if not result_path.exists():
        raise FileNotFoundError(
            f"phase3: result.yaml missing at {result_path} — run Phase 2 first"
        )
    result = load_yaml_unsafe(result_path)

    # --- Step 1: Hard gates ---
    gates = evaluate_hard_gates(
        result, inputs.current_sample_policy_version
    )
    n_failed = sum(1 for g in gates if not g.passed)
    logger.info(
        "phase3: %s: %d/%d hard-gate fails",
        inputs.batch_id,
        n_failed,
        len(gates),
    )

    # --- Step 2: Pre-pack (scans batches/ for §7.MT inside build_judge_packet) ---
    packet_path = inputs.batch_dir / "_packets" / "judge_packet.md"
    packet_inputs = PacketInputs(
        batch_id=inputs.batch_id,
        direction=inputs.direction,
        result=result,
        context=inputs.context,
        current_sample_policy_version=inputs.current_sample_policy_version,
        batches_dir=inputs.batches_root,
        mt_budget_config=inputs.mt_budget_config,
    )
    packet_text = write_judge_packet(packet_inputs, packet_path)

    # --- Step 3: LLM writes judge.md via callback ---
    judge_md_path = inputs.batch_dir / "judge.md"
    llm_judge_callback(packet_text, judge_md_path, set(inputs.packet_refs))

    # --- Step 4: Audit ---
    parsed = audit_judge_md(judge_md_path, packet_refs=inputs.packet_refs or None)

    # --- Step 5: Cleanup ---
    if inputs.cleanup_packet:
        try:
            packet_path.unlink()
        except OSError:
            logger.warning("phase3: failed to remove packet %s", packet_path)

    return Phase3Result(
        gates=gates,
        packet_path=packet_path,
        judge_md_path=judge_md_path,
        parsed=parsed,
    )
