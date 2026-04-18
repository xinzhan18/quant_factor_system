"""Single-input report packet for the factor.md subagent.

Parallels ``checkpoints.generator`` but for Phase 4 Step 3: one packet
per admitted factor, consumed by a sandboxed subagent that writes
``vault/factors/F{id}.md``.

Packet structure (frozen):

.. code-block:: markdown

    ---
    factor_id: F020
    direction: fundamental_price_divergence
    admitted_in_batch: batch_103
    ---

    # Report Packet — F020

    ## Factor YAML Summary
    ```yaml
    name: triple_product_80d_pb
    expression: ...
    validation_metrics: {ic_mean: 0.016, ic_ir: 0.338, ...}
    risk_metrics: {style_r_squared: 0.08, alpha_survival_ratio: 0.69}
    ```

    ## Direction Context
    <excerpt of Hypothesis + most recent thread>

    ## Judge Synthesis (admission reasoning)
    <the C{id} section from judge.md>

    ## Library Context
    - Nearest: F012 (corr=0.30)

    ## Instructions
    Write a deep analytical report on F{id}...

The subagent sandbox protocol (enforced by the mine CLI orchestration
layer, not by this module):

* inputs: ``_packets/report_packet_F{id}.md`` only
* outputs: ``vault/factors/F{id}.md`` only
* forbidden: read any other file / Qlib / DB / network
* on_complete: ``research commit-report F{id}`` hook
* on_failure: append to ``_subagent_failures.log``, main loop unaffected
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ReportPacketInputs:
    """Inputs to :func:`build_report_packet`."""

    factor_id: str
    factor_record: dict[str, Any]
    """The factor.yaml dict we just wrote in Phase 4 Step 1."""

    direction: str
    direction_excerpt: str = ""
    """Optional hypothesis + thread excerpt from directions/{name}.md."""

    judge_synthesis: str = ""
    """Optional ``## C{id}`` section text from the batch's judge.md."""

    nearest_factor_summary: str = ""
    """Optional one-liner about the nearest library factor (for uniqueness)."""

    admitted_in_batch: str = ""

    available_charts: list[str] = field(default_factory=list)
    """Chart basenames (no ``.png``) produced by ``report.render.render_factor``
    in ``vault/factors/F{id}/``. The subagent must embed only charts from
    this whitelist — any image not listed here does not exist on disk."""


def _format_yaml_block(data: dict[str, Any]) -> str:
    """Render a dict as a fenced YAML code block."""
    body = yaml.dump(
        data, sort_keys=False, default_flow_style=False, allow_unicode=True
    )
    return "```yaml\n" + body.rstrip() + "\n```"


def build_report_packet(inputs: ReportPacketInputs) -> str:
    """Compose the full markdown packet string for one factor."""
    factor_id = inputs.factor_id
    record = inputs.factor_record

    summary = {
        "name": record.get("name"),
        "expression": record.get("expression"),
        "source_type": record.get("source_type"),
        "family_tag": record.get("family_tag"),
        "validation_metrics": record.get("validation_metrics", {}),
        "risk_metrics": record.get("risk_metrics", {}),
    }
    if record.get("source_type") == "python":
        summary["python_path"] = record.get("python_path")

    frontmatter = {
        "factor_id": factor_id,
        "direction": inputs.direction or record.get("direction"),
        "admitted_in_batch": inputs.admitted_in_batch
        or record.get("admitted_in_batch"),
    }
    fm_text = yaml.dump(frontmatter, sort_keys=False, default_flow_style=False)

    parts: list[str] = []
    parts.append("---")
    parts.append(fm_text.rstrip())
    parts.append("---")
    parts.append("")
    parts.append(f"# Report Packet — {factor_id}")
    parts.append("")
    parts.append("## Factor YAML Summary")
    parts.append("")
    parts.append(_format_yaml_block(summary))
    parts.append("")

    if inputs.direction_excerpt.strip():
        parts.append("## Direction Context")
        parts.append("")
        parts.append(inputs.direction_excerpt.strip())
        parts.append("")

    if inputs.judge_synthesis.strip():
        parts.append("## Judge Synthesis")
        parts.append("")
        parts.append(inputs.judge_synthesis.strip())
        parts.append("")

    if inputs.nearest_factor_summary.strip():
        parts.append("## Library Context")
        parts.append("")
        parts.append(inputs.nearest_factor_summary.strip())
        parts.append("")

    if inputs.available_charts:
        parts.append("## Available Charts")
        parts.append("")
        parts.append(
            "The following PNG charts exist in `vault/factors/"
            f"{factor_id}/` and may be embedded via "
            f"`![[{factor_id}/<name>.png]]`. **Do not embed any chart "
            "name that is not on this list** — the file would not exist."
        )
        parts.append("")
        for chart in inputs.available_charts:
            parts.append(f"- `{chart}`")
        parts.append("")
    else:
        parts.append("## Available Charts")
        parts.append("")
        parts.append(
            "_No charts generated (report.render.render_factor did not run or failed). "
            "Write a text-only report — do not include any `![[...png]]` embeds._"
        )
        parts.append("")

    parts.append("## Instructions")
    parts.append("")
    parts.append(
        f"Write a deep analytical report on `{factor_id}`. Cover the "
        "economic mechanism, the validation evidence, the risk cleanness, "
        "and the library positioning. Use only the information in this "
        "packet — do not open other files, call Qlib, or reach the DB. "
        "Embed only charts listed in the **Available Charts** section "
        "(skip any section whose chart is unavailable). "
        f"Output path: `vault/factors/{factor_id}.md`."
    )
    parts.append("")

    return "\n".join(parts) + "\n"


def write_report_packet(
    inputs: ReportPacketInputs, output_path: str | Path
) -> str:
    """Build and persist the packet; returns the text for inspection."""
    text = build_report_packet(inputs)
    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return text


def extract_candidate_synthesis(candidate_md_path: str | Path) -> str:
    """Read the full ``candidates/C{id}.md`` file as the judge synthesis.

    Phase 4 injects this text into ``report_packet_F{id}.md`` so the factor
    report subagent can quote the judge's CP reasoning. Returns the raw file
    contents (frontmatter + body); empty string if file is missing.
    """
    p = Path(candidate_md_path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8").strip()
