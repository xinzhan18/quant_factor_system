"""Phase 3 pre-pack — generate ``_packets/judge_packet.md``.

The LLM judge sees **exactly one input** (R3 "single main input"): a
markdown packet produced here. This module takes all the raw artifacts
(``result.yaml``, ``direction.md``, ``lessons.md``, nearest factor
``F{id}.md``, §7.MT counters) and composes a single structured document
the LLM can read top-to-bottom without any additional file lookup.

Packet structure (frozen by audit):

.. code-block:: markdown

    ---
    batch_id: batch_103
    direction: fundamental_price_divergence
    n_candidates: 6
    sample_policy_version: v3
    mt_budget:
      cumulative_candidates: 612
      direction_candidates: 47
      validation_exposure: 5
      score: 0.52
      bucket: medium
    ---

    # Batch batch_103 — Judge Packet

    ## Direction Context
    <excerpt of direction.md>

    ## Lessons Excerpt
    <structural constraints + data facts>

    ## Nearest Library Factor
    <F{id}.md summary if applicable>

    ## Candidates

    ### C001 — Std($close, 20)
    **Hard Gate**: all_pass  (or reject reason list)
    **Numeric hint**:
    - CP01 coverage=0.97 sign=+1
    - CP03 ic_mean_val=0.016 ic_ir_val=0.338 ls_tstat=3.89
           mt_bucket=medium search_adjusted=0.41
    - CP04 barra_residual_ic=0.013 style_r²=0.08 alpha_survival=0.69
    - CP05 max_lib_corr=0.30 nearest=F012
    - CP06 split_stability=high expanding_window_pass=true

    (...body repeats per candidate)

The packet is deliberately flat markdown — LLM reads it top-to-bottom,
no cross-references, no ``[[wiki links]]`` (those are resolved at
pre-pack time into inline excerpts).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from research.checkpoints.hard_gates import HardGateResult, evaluate_hard_gates
from research.checkpoints.mt_budget import (
    MtBudgetConfig,
    MtCounts,
    compute_mt_budget,
    scan_batches_for_mt,
)


# ---------------------------------------------------------------------------
# Inputs + context bundles
# ---------------------------------------------------------------------------


@dataclass
class PacketContext:
    """Optional context snippets the LLM needs to reason about candidates."""

    direction_excerpt: str = ""
    """Hypothesis + most-recent thread entries from ``directions/{name}.md``."""

    lessons_excerpt: str = ""
    """Data Facts + Operator Registry + Structural Constraints from ``lessons.md``."""

    nearest_factor_excerpt: str = ""
    """Top-of-report summary from the nearest ``factors/F{id}.md``, if any."""


@dataclass
class PacketInputs:
    """Everything needed to pre-pack a judge_packet for one batch."""

    batch_id: str
    direction: str
    result: dict[str, Any]  # parsed result.yaml
    context: PacketContext
    current_sample_policy_version: str
    batches_dir: Path
    mt_budget_config: MtBudgetConfig = field(default_factory=MtBudgetConfig)


# ---------------------------------------------------------------------------
# Packet serialization
# ---------------------------------------------------------------------------


def _format_numeric_hint_line(label: str, fields: dict[str, Any]) -> str:
    pairs = [f"{k}={_fmt(v)}" for k, v in fields.items() if v is not None]
    return f"- **{label}**: " + " ".join(pairs)


def _fmt(v: Any) -> str:
    if isinstance(v, float):
        return f"{v:.4f}"
    if isinstance(v, bool):
        return "true" if v else "false"
    return str(v)


def _candidate_section(
    candidate: dict[str, Any],
    gate: HardGateResult,
    mt_hint: dict[str, Any],
) -> str:
    cid = candidate["candidate_id"]
    expr = candidate.get("expression", "?")
    source = candidate.get("source_type", "dsl")

    lines: list[str] = [
        f"### {cid} — `{expr}` ({source})",
        "",
    ]

    # Hard gate status
    if gate.passed:
        lines.append("**Hard Gate (CP01)**: `all_pass`")
    else:
        lines.append("**Hard Gate (CP01)**: `reject`")
        for r in gate.reasons:
            lines.append(f"  - {r}")
    lines.append("")

    # If compute_error or any hard gate fail: skip numeric hints
    if not gate.passed or candidate.get("compute_error"):
        lines.append("_Numeric hints omitted — hard gate failed._")
        lines.append("")
        return "\n".join(lines)

    lines.append("**Numeric hints**:")

    # CP01 basics
    lines.append(
        _format_numeric_hint_line(
            "CP01 (context)",
            {"coverage": candidate.get("coverage"), "sign": candidate.get("sign")},
        )
    )

    # CP03 — effect strength + §7.MT
    es = candidate.get("effect_strength", {})
    val = es.get("validation", {})
    qt = candidate.get("quintile", {})
    cp03_fields = {
        "ic_mean_val": val.get("ic_mean"),
        "ic_ir_val": val.get("ic_ir"),
        "ic_win_rate_val": val.get("ic_win_rate"),
        "ls_mean": qt.get("long_short_mean_validation"),
        "mono_val": qt.get("monotonicity_validation"),
        "mt_score": mt_hint.get("mt_score"),
        "mt_bucket": mt_hint.get("mt_bucket"),
        "search_adjusted": mt_hint.get("search_adjusted_strength", {}).get("adjusted"),
    }
    lines.append(_format_numeric_hint_line("CP03 (strength)", cp03_fields))

    # CP04 — Barra
    barra = candidate.get("barra", {}) or {}
    cp04_fields = {
        "style_r2": barra.get("style_r_squared"),
        "barra_residual_ic": barra.get("barra_residual_ic"),
        "alpha_survival": barra.get("alpha_survival_ratio"),
        "crowding": barra.get("style_crowding_risk"),
        "dominant_style": barra.get("dominant_style_exposure"),
    }
    lines.append(_format_numeric_hint_line("CP04 (risk)", cp04_fields))

    # CP05 — redundancy
    red = candidate.get("redundancy", {}) or {}
    cp05_fields = {
        "max_lib_corr": red.get("max_lib_corr"),
        "nearest": red.get("nearest_factor_id"),
        "exceeds_threshold": red.get("exceeds_threshold"),
    }
    lines.append(_format_numeric_hint_line("CP05 (redundancy)", cp05_fields))

    # CP06 — stability
    stab = candidate.get("stability", {}) or {}
    split = stab.get("split_stability", {}) or {}
    cp06_fields = {
        "split_bucket": split.get("bucket"),
        "split_sign_consistency": split.get("sign_consistency"),
        "split_dispersion": split.get("dispersion"),
        "train_val_sign_ok": stab.get("sign_consistency_train_validation"),
        "train_val_decay": stab.get("train_validation_decay"),
    }
    lines.append(_format_numeric_hint_line("CP06 (stability)", cp06_fields))

    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def build_judge_packet(inputs: PacketInputs) -> str:
    """Produce the full ``judge_packet.md`` text for *inputs*.

    This is pure — no file I/O. The phase3 orchestrator writes the
    return value to ``batches/{batch_id}/_packets/judge_packet.md``.
    """
    # --- 1. Hard gates on every candidate ---
    gates = evaluate_hard_gates(
        inputs.result, inputs.current_sample_policy_version
    )
    gate_by_id = {g.candidate_id: g for g in gates}

    # --- 2. §7.MT: scan batches, compute once per batch ---
    counts: MtCounts = scan_batches_for_mt(
        inputs.batches_dir,
        current_batch_id=inputs.batch_id,
        current_direction=inputs.direction,
        sample_policy_version=inputs.current_sample_policy_version,
    )

    # --- 3. Per-candidate MT hint (same counts, different val metrics) ---
    def _mt_hint_for(cand: dict[str, Any]) -> dict[str, Any]:
        val = (cand.get("effect_strength") or {}).get("validation") or {}
        qt = cand.get("quintile") or {}
        expanding = (cand.get("stability") or {}).get("expanding_window", {}) or {}
        return compute_mt_budget(
            counts,
            inputs.mt_budget_config,
            ic_mean=val.get("ic_mean"),
            ic_ir=val.get("ic_ir"),
            monotonicity=qt.get("monotonicity_validation"),
            expanding_pass=bool(expanding.get("pass", False)),
        )

    # --- 4. Frontmatter ---
    frontmatter = {
        "batch_id": inputs.batch_id,
        "direction": inputs.direction,
        "n_candidates": len(inputs.result.get("candidates", [])),
        "sample_policy_version": inputs.current_sample_policy_version,
        "mt_budget": {
            "cumulative_candidates": counts.cumulative_candidates,
            "direction_candidates": counts.direction_candidates,
            "validation_exposure": counts.validation_exposure,
            "n_batches_scanned": counts.n_batches_scanned,
        },
    }
    fm_text = yaml.dump(
        frontmatter, default_flow_style=False, sort_keys=False
    )

    # --- 5. Body ---
    parts: list[str] = []
    parts.append("---")
    parts.append(fm_text.rstrip())
    parts.append("---")
    parts.append("")
    parts.append(f"# Batch {inputs.batch_id} — Judge Packet")
    parts.append("")
    parts.append(f"Direction: **{inputs.direction}**")
    parts.append("")

    if inputs.context.direction_excerpt.strip():
        parts.append("## Direction Context")
        parts.append("")
        parts.append(inputs.context.direction_excerpt.strip())
        parts.append("")

    if inputs.context.lessons_excerpt.strip():
        parts.append("## Lessons Excerpt")
        parts.append("")
        parts.append(inputs.context.lessons_excerpt.strip())
        parts.append("")

    if inputs.context.nearest_factor_excerpt.strip():
        parts.append("## Nearest Library Factor")
        parts.append("")
        parts.append(inputs.context.nearest_factor_excerpt.strip())
        parts.append("")

    parts.append("## Candidates")
    parts.append("")

    for cand in inputs.result.get("candidates", []):
        cid = cand.get("candidate_id", "?")
        gate = gate_by_id.get(
            cid,
            HardGateResult(candidate_id=cid, passed=False, reasons=["gate missing"]),
        )
        mt_hint = _mt_hint_for(cand) if gate.passed and not cand.get("compute_error") else {}
        parts.append(_candidate_section(cand, gate, mt_hint))

    return "\n".join(parts) + "\n"


def write_judge_packet(
    inputs: PacketInputs, output_path: str | Path
) -> str:
    """Build the packet text and write it to *output_path*.

    Returns the text for in-process inspection. Output file directory is
    created on demand.
    """
    text = build_judge_packet(inputs)
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return text
