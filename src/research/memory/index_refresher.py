"""Regenerate the machine-maintained parts of ``vault/INDEX.md``.

INDEX.md has two halves plus a YAML frontmatter block:

* **Frontmatter** — summary counters (``round``, ``last_batch``,
  ``total_active_directions``, ``total_factors_admitted``,
  ``generated_at``). Python-maintained.
* **Upper half** — LLM-maintained narrative listing active directions
  and recent highlights. Phase 5 CONSOLIDATION rewrites it.
* **Lower half** — machine-generated statistics table bounded by the
  HTML comments ``<!-- BEGIN AUTO-SECTION -->`` and
  ``<!-- END AUTO-SECTION -->``. Python regenerates it after every
  archive based on scanning ``directions/`` and ``factors/``.

This module only touches the frontmatter and the lower half. It:

1. Reads every ``directions/{name}.md`` frontmatter and collects
   ``direction_id``, ``status``, ``rounds``, ``admits``, ``last_batch``.
2. Reads every ``factors/F*.yaml`` to count totals.
3. Reads ``state.yaml`` for ``round`` + ``last_batch``.
4. Rewrites the frontmatter in place, preserving the LLM-authored
   narrative and the sentinel-bounded lower half.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml

BEGIN_SENTINEL = "<!-- BEGIN AUTO-SECTION -->"
END_SENTINEL = "<!-- END AUTO-SECTION -->"
FACTOR_LIB_BEGIN_SENTINEL = "<!-- BEGIN FACTOR-LIBRARY -->"
FACTOR_LIB_END_SENTINEL = "<!-- END FACTOR-LIBRARY -->"

_INDEX_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(?P<fm>.*?)\n---\s*\n?(?P<body>.*)", re.DOTALL
)
_NON_ACTIVE_DIRECTION_STATUSES = {"dead", "merged", "archived"}

_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(?P<fm>.*?)\n---\s*\n?(?P<body>.*)", re.DOTALL
)


def _read_direction_frontmatter_and_body(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}, text
    fm = yaml.safe_load(m.group("fm"))
    return (fm if isinstance(fm, dict) else {}), m.group("body")


def _count_active_threads(body: str) -> int:
    """Count threads marked [◉ ACTIVE] in the body."""
    return len(re.findall(r"\[◉ ACTIVE\]", body))


def collect_direction_stats(directions_dir: str | Path) -> list[dict[str, Any]]:
    """Return a list of frontmatter dicts for all direction md files."""
    rows: list[dict[str, Any]] = []
    p = Path(directions_dir)
    if not p.exists():
        return rows
    for md in sorted(p.glob("*.md")):
        fm, body = _read_direction_frontmatter_and_body(md)
        if not fm:
            continue
        rows.append(
            {
                "direction_id": fm.get("direction_id", md.stem),
                "status": fm.get("status", "exploring"),
                "priority": fm.get("priority", "medium"),
                "rounds": int(fm.get("rounds", 0)),
                "admits": int(fm.get("admits", 0)),
                "last_batch": fm.get("last_batch") or "—",
                "active_threads": _count_active_threads(body),
            }
        )
    return rows


def count_admitted_factors(factors_dir: str | Path) -> int:
    p = Path(factors_dir)
    if not p.exists():
        return 0
    return sum(1 for f in p.glob("F*.yaml"))


def _factor_id_key(path: Path) -> tuple[int, str]:
    """Sort key for F{id}.yaml — numeric id ascending, with fallback."""
    stem = path.stem
    digits = "".join(c for c in stem if c.isdigit())
    return (int(digits) if digits else 1 << 30, stem)


def _fmt_float(value: Any, digits: int = 3) -> str | None:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return None
    return f"{f:.{digits}f}"


def collect_admitted_factors(factors_dir: str | Path) -> list[dict[str, Any]]:
    """Return one row per ``F*.yaml``, sorted by numeric factor id.

    Each row pulls key fields from the YAML (canonical admission record);
    if a sibling ``F*.md`` exists its frontmatter supplies ``composite_grade``
    (LLM-authored by the factor-report subagent, may not yet exist when
    Phase 4 first refreshes).
    """
    rows: list[dict[str, Any]] = []
    p = Path(factors_dir)
    if not p.exists():
        return rows
    for yaml_path in sorted(p.glob("F*.yaml"), key=_factor_id_key):
        try:
            data = load_yaml(yaml_path)
        except Exception:
            continue
        if not isinstance(data, dict):
            continue
        if data.get("status") == "retired":
            continue
        md_path = yaml_path.with_suffix(".md")
        grade: str | None = None
        if md_path.exists():
            fm, _ = _read_direction_frontmatter_and_body(md_path)
            g = fm.get("composite_grade") if isinstance(fm, dict) else None
            if isinstance(g, str) and g.strip():
                grade = g.strip()
        metrics = data.get("validation_metrics") or {}
        if not isinstance(metrics, dict):
            metrics = {}
        rows.append(
            {
                "factor_id": str(data.get("factor_id") or yaml_path.stem),
                "name": str(data.get("name") or yaml_path.stem),
                "direction": str(data.get("direction") or "—"),
                "expression": str(data.get("expression") or ""),
                "grade": grade,
                "ic_ir": metrics.get("ic_ir"),
                "monotonicity": metrics.get("monotonicity"),
            }
        )
    return rows


def render_factor_library(rows: list[dict[str, Any]]) -> str:
    """Render the sentinel-bounded ``因子库`` bullet list."""
    lines = [FACTOR_LIB_BEGIN_SENTINEL]
    if not rows:
        lines.append("")
        lines.append("_（暂无 admitted 因子）_")
    else:
        for r in rows:
            grade_tok = f" `{r['grade']}`" if r.get("grade") else ""
            metric_bits: list[str] = []
            icir = _fmt_float(r.get("ic_ir"))
            if icir is not None:
                metric_bits.append(f"ICIR_oos={icir}")
            mono = _fmt_float(r.get("monotonicity"), digits=2)
            if mono is not None:
                metric_bits.append(f"Mono={mono}")
            metric_txt = ", ".join(metric_bits) if metric_bits else "metrics pending"
            expr = r.get("expression") or ""
            expr_tok = f" · `{expr}`" if expr else ""
            lines.append(
                f"- [[factors/{r['factor_id']}|{r['name']}]]{grade_tok}"
                f" · {r['direction']} · {metric_txt}{expr_tok}"
            )
    lines.append(FACTOR_LIB_END_SENTINEL)
    return "\n".join(lines)


def _apply_factor_library(text: str, factor_library_block: str) -> str:
    """Replace the ``FACTOR-LIBRARY`` sentinel block. No-op if sentinels absent.

    We keep the sentinels optional so INDEX files written before this feature
    (or stripped-down test fixtures) don't get an unexpected block appended.
    """
    if FACTOR_LIB_BEGIN_SENTINEL not in text or FACTOR_LIB_END_SENTINEL not in text:
        return text
    pattern = re.compile(
        re.escape(FACTOR_LIB_BEGIN_SENTINEL) + r".*?" + re.escape(FACTOR_LIB_END_SENTINEL),
        re.DOTALL,
    )
    return pattern.sub(factor_library_block, text)


def render_auto_section(
    direction_rows: list[dict[str, Any]],
    total_admitted: int,
    round_counter: int,
    last_consolidation_round: int | None,
) -> str:
    """Build the markdown between the BEGIN/END sentinels."""
    lines = [BEGIN_SENTINEL, ""]

    # Direction table
    lines.append("| Direction | Status | Priority | Rounds | Admits | Threads | Last batch |")
    lines.append("|---|---|---|---|---|---|---|")
    if not direction_rows:
        lines.append("| _no directions yet_ | — | — | 0 | 0 | 0 | — |")
    else:
        for r in direction_rows:
            lines.append(
                "| "
                + " | ".join(
                    [
                        str(r["direction_id"]),
                        str(r["status"]),
                        str(r.get("priority", "medium")),
                        str(r["rounds"]),
                        str(r["admits"]),
                        str(r.get("active_threads", 0)),
                        str(r["last_batch"]),
                    ]
                )
                + " |"
            )
    lines.append("")

    # System-level metrics
    lines.append("| Metric | Value |")
    lines.append("|---|---|")
    lines.append(f"| Total factors admitted | {total_admitted} |")
    lines.append(f"| Current round | {round_counter} |")
    lines.append(
        "| Last consolidation | "
        + (
            f"round {last_consolidation_round}"
            if last_consolidation_round is not None
            else "—"
        )
        + " |"
    )
    lines.append("")
    lines.append(END_SENTINEL)

    return "\n".join(lines)


def _count_active_directions(rows: list[dict[str, Any]]) -> int:
    return sum(
        1 for r in rows if r.get("status") not in _NON_ACTIVE_DIRECTION_STATUSES
    )


def _read_state_summary(paths: StoragePaths) -> tuple[int | None, str | None]:
    """Return ``(round, last_batch)`` from state.yaml, or ``(None, None)`` if absent."""
    try:
        data = load_yaml(paths.state_file)
    except FileNotFoundError:
        return None, None
    if not isinstance(data, dict):
        return None, None
    r = data.get("round")
    lb = data.get("last_batch")
    return (int(r) if r is not None else None, lb if isinstance(lb, str) else None)


def _render_frontmatter(
    *,
    round_counter: int,
    last_batch: str | None,
    total_active_directions: int,
    total_admitted: int,
    last_consolidation_round: int | None,
    generated_at: str,
) -> str:
    """Render the YAML frontmatter block (with trailing newline)."""
    lines = [
        "---",
        f"generated_at: {generated_at}",
        f"round: {round_counter}",
        f"total_active_directions: {total_active_directions}",
        f"total_factors_admitted: {total_admitted}",
        f"last_batch: {last_batch if last_batch else 'null'}",
        "last_consolidation_round: "
        + (str(last_consolidation_round) if last_consolidation_round is not None else "null"),
        "---",
    ]
    return "\n".join(lines) + "\n"


def _apply_frontmatter(existing: str, frontmatter_block: str) -> str:
    """Replace or prepend the YAML frontmatter block.

    Always leaves exactly one blank line between the frontmatter and the body.
    """
    m = _INDEX_FRONTMATTER_RE.match(existing)
    body = m.group("body") if m else existing
    return frontmatter_block + "\n" + body.lstrip("\n")


def refresh_index(
    paths: StoragePaths,
    round_counter: int,
    last_consolidation_round: int | None = None,
) -> Path:
    """Regenerate INDEX.md frontmatter + auto-section in place.

    Preserves the LLM-authored narrative between the frontmatter and the
    ``BEGIN_SENTINEL`` block. If the file is missing, creates a minimal
    INDEX with frontmatter + auto-section only.
    """
    rows = collect_direction_stats(paths.directions_dir)
    total_admitted = count_admitted_factors(paths.factors_dir)
    auto_text = render_auto_section(
        rows, total_admitted, round_counter, last_consolidation_round
    )
    factor_library_block = render_factor_library(
        collect_admitted_factors(paths.factors_dir)
    )
    _, last_batch = _read_state_summary(paths)
    frontmatter_block = _render_frontmatter(
        round_counter=round_counter,
        last_batch=last_batch,
        total_active_directions=_count_active_directions(rows),
        total_admitted=total_admitted,
        last_consolidation_round=last_consolidation_round,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )

    index_path = paths.vault_index_file
    if not index_path.exists():
        skeleton = (
            frontmatter_block
            + "\n# Factor Research Index\n\n"
            "_Upper half is LLM-maintained; Phase 5 consolidation rewrites it._\n\n"
            "---\n\n"
            "## Statistics (machine-generated)\n\n"
            f"{auto_text}\n"
        )
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(skeleton, encoding="utf-8")
        return index_path

    text = index_path.read_text(encoding="utf-8")
    text = _apply_frontmatter(text, frontmatter_block)
    text = _apply_factor_library(text, factor_library_block)
    if BEGIN_SENTINEL in text and END_SENTINEL in text:
        pattern = re.compile(
            re.escape(BEGIN_SENTINEL) + r".*?" + re.escape(END_SENTINEL),
            re.DOTALL,
        )
        new_text = pattern.sub(auto_text, text)
    else:
        new_text = text.rstrip() + "\n\n" + auto_text + "\n"

    index_path.write_text(new_text, encoding="utf-8")
    return index_path
