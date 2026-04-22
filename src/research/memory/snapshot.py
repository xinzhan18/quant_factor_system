"""Markdown aggregation layer backing ``research memory snapshot``.

Obsidian Bases render at display time; their tables don't exist in the
markdown source, so LLMs / ``cat`` / CI can't read them. This module
scans the same frontmatter Bases does (filter predicates mirror
``storage/vault/_bases/*.base``) and emits plain markdown tables as the
LLM-side counterpart. INDEX.md keeps only the Bases embeds — data
duplication between an embedded NAV block and the CLI has been removed.

Public surface:

* ``collect_direction_rows`` / ``collect_factor_rows`` /
  ``collect_batch_rows`` — scan frontmatter.
* ``render_directions_table`` / ``render_factors_table`` /
  ``render_batches_table`` — pipe tables.
* ``render_snapshot`` — full multi-section markdown for the CLI.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

import yaml

from research.storage.paths import StoragePaths

_FM_RE = re.compile(r"\A---\s*\n(?P<fm>.*?)\n---\s*\n?", re.DOTALL)

_STATUS_ICON = {
    "productive": "🟢",
    "exploring": "🔵",
    "saturated": "🟡",
    "dead": "🔴",
    "merged": "⚫",
    "archived": "⚫",
}
_GRADE_ICON = {"A": "🥇", "B": "🥈", "C": "🥉", "D": ""}


def _read_fm(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    m = _FM_RE.match(path.read_text(encoding="utf-8"))
    if m is None:
        return {}
    data = yaml.safe_load(m.group("fm"))
    return data if isinstance(data, dict) else {}


def _fmt(value: Any, ndigits: int = 4) -> str:
    if value is None or value == "":
        return "—"
    if isinstance(value, float):
        return f"{value:.{ndigits}f}"
    return str(value)


def collect_direction_rows(paths: StoragePaths) -> list[dict[str, Any]]:
    """One row per ``directions/*.md`` with frontmatter pulled out."""
    rows: list[dict[str, Any]] = []
    if not paths.directions_dir.exists():
        return rows
    for md in sorted(paths.directions_dir.glob("*.md")):
        fm = _read_fm(md)
        if not fm:
            continue
        rows.append(
            {
                "slug": md.stem,
                "status": fm.get("status", "exploring"),
                "priority": fm.get("priority", "medium"),
                "rounds": int(fm.get("rounds", 0) or 0),
                "admits": int(fm.get("admits", 0) or 0),
                "last_batch": fm.get("last_batch") or "",
                "last_goal": (fm.get("last_goal") or "").strip(),
            }
        )
    return rows


def collect_factor_rows(paths: StoragePaths) -> list[dict[str, Any]]:
    """One row per active admitted ``factors/F*.md`` — filter mirrors
    ``factors.base`` (``decision == admit`` AND ``status == active``)."""
    rows: list[dict[str, Any]] = []
    if not paths.factors_dir.exists():
        return rows
    for md in sorted(
        paths.factors_dir.glob("F*.md"),
        key=lambda p: int("".join(c for c in p.stem if c.isdigit()) or "0"),
    ):
        fm = _read_fm(md)
        if not fm:
            continue
        if fm.get("decision") != "admit" or fm.get("status") != "active":
            continue
        rows.append(
            {
                "factor_id": fm.get("id") or md.stem,
                "name": fm.get("name") or md.stem,
                "direction": fm.get("direction") or "—",
                "grade": fm.get("composite_grade") or "",
                "score": fm.get("composite_score"),
                "ic_mean": fm.get("ic_mean_validation"),
                "ic_ir": fm.get("ic_ir_validation"),
                "mono": fm.get("monotonicity_validation"),
                "alpha_surv": fm.get("alpha_survival_ratio"),
                "max_corr": fm.get("max_lib_corr"),
                "batch": fm.get("batch") or "",
            }
        )
    return rows


def collect_batch_rows(
    paths: StoragePaths, limit: int | None = None
) -> list[dict[str, Any]]:
    """One row per ``batches/*/judge.md`` — newest first. ``limit`` caps
    the list (``None`` = all)."""
    rows: list[dict[str, Any]] = []
    if not paths.batches_dir.exists():
        return rows
    for batch_dir in sorted(
        paths.batches_dir.iterdir(),
        key=lambda p: p.name,
        reverse=True,
    ):
        if not batch_dir.is_dir():
            continue
        jp = batch_dir / "judge.md"
        fm = _read_fm(jp)
        if not fm:
            continue
        rows.append(
            {
                "batch_id": fm.get("batch_id") or batch_dir.name,
                "direction": fm.get("direction") or "—",
                "admit": int(fm.get("admit_count", 0) or 0),
                "reserve": int(fm.get("reserve_count", 0) or 0),
                "reject": int(fm.get("reject_count", 0) or 0),
                "total": int(fm.get("candidate_count", 0) or 0),
                "mt_bucket": fm.get("mt_bucket") or "",
                "judged_at": fm.get("judged_at") or "",
            }
        )
        if limit is not None and len(rows) >= limit:
            break
    return rows


def _pipe_row(cells: Iterable[Any]) -> str:
    return "| " + " | ".join(str(c) for c in cells) + " |"


def render_directions_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_（无方向）_"
    header = _pipe_row(["", "Direction", "Status", "Prio", "Rounds", "Admits", "Last"])
    sep = _pipe_row(["---"] * 7)
    lines = [header, sep]
    for r in sorted(
        rows,
        key=lambda x: (
            x["status"] != "productive",
            x["status"] != "exploring",
            -x["admits"],
            x["slug"],
        ),
    ):
        icon = _STATUS_ICON.get(r["status"], "⚪")
        last = (
            f"[[batches/{r['last_batch']}/judge|{r['last_batch']}]]"
            if r["last_batch"]
            else "—"
        )
        lines.append(
            _pipe_row(
                [
                    icon,
                    f"[[directions/{r['slug']}]]",
                    r["status"],
                    r["priority"],
                    r["rounds"],
                    r["admits"],
                    last,
                ]
            )
        )
    return "\n".join(lines)


def render_factors_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_（暂无 admitted 因子）_"
    header = _pipe_row(
        [
            "",
            "ID",
            "Name",
            "Direction",
            "Grade",
            "Score",
            "IC",
            "ICIR",
            "Mono",
            "α-Surv",
            "MaxCorr",
            "Admitted",
        ]
    )
    sep = _pipe_row(["---"] * 12)
    lines = [header, sep]
    for r in rows:
        icon = _GRADE_ICON.get(r["grade"], "")
        batch = (
            f"[[batches/{r['batch']}/judge|{r['batch']}]]" if r["batch"] else "—"
        )
        lines.append(
            _pipe_row(
                [
                    icon,
                    f"[[factors/{r['factor_id']}]]",
                    r["name"],
                    f"[[directions/{r['direction']}]]" if r["direction"] != "—" else "—",
                    r["grade"] or "—",
                    _fmt(r["score"], 0),
                    _fmt(r["ic_mean"], 4),
                    _fmt(r["ic_ir"], 3),
                    _fmt(r["mono"], 2),
                    _fmt(r["alpha_surv"], 3),
                    _fmt(r["max_corr"], 3),
                    batch,
                ]
            )
        )
    return "\n".join(lines)


def render_batches_table(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "_（暂无 batch）_"
    header = _pipe_row(
        ["", "Batch", "Direction", "✅", "⏸", "❌", "Total", "MT", "Judged"]
    )
    sep = _pipe_row(["---"] * 9)
    lines = [header, sep]
    for r in rows:
        if r["admit"] > 0:
            outcome = "✅"
        elif r["reserve"] > 0:
            outcome = "⏸"
        else:
            outcome = "❌"
        direction = (
            f"[[directions/{r['direction']}]]" if r["direction"] != "—" else "—"
        )
        lines.append(
            _pipe_row(
                [
                    outcome,
                    f"[[batches/{r['batch_id']}/judge|{r['batch_id']}]]",
                    direction,
                    r["admit"],
                    r["reserve"],
                    r["reject"],
                    r["total"],
                    r["mt_bucket"] or "—",
                    r["judged_at"] or "—",
                ]
            )
        )
    return "\n".join(lines)


def render_snapshot(
    paths: StoragePaths,
    sections: tuple[str, ...] = ("directions", "factors", "batches"),
    recent_batches: int | None = None,
) -> str:
    """Full aggregated markdown — all three sections, usable as a one-shot
    briefing for LLM / reports / CI dumps."""
    chunks: list[str] = ["# Vault Snapshot", ""]
    if "directions" in sections:
        chunks.append("## 🎯 方向总览")
        chunks.append("")
        chunks.append(render_directions_table(collect_direction_rows(paths)))
        chunks.append("")
    if "factors" in sections:
        chunks.append("## 📚 因子库 (admitted / active)")
        chunks.append("")
        chunks.append(render_factors_table(collect_factor_rows(paths)))
        chunks.append("")
    if "batches" in sections:
        title = "## 📊 Batch 流水"
        if recent_batches:
            title += f" (最近 {recent_batches})"
        chunks.append(title)
        chunks.append("")
        chunks.append(
            render_batches_table(collect_batch_rows(paths, limit=recent_batches))
        )
        chunks.append("")
    return "\n".join(chunks)
