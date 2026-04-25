"""Regenerate ``vault/INDEX.md`` — a minimal Map of Content (MOC).

The file is 100% Python-owned now. Everything LLM wants to say about a
direction/factor/batch lives in its own source file (``directions/*.md``,
``factors/F*.md``, ``batches/*/judge.md``); INDEX simply embeds three
``.base`` files that Obsidian Bases re-queries live on every open. The
narrative bits in INDEX are the Cockpit (Python-derived state) and the
HOT-TOPICS-LLM block (`/pattern-scout` 维护的跨批模式).

Layout produced:

* YAML frontmatter with summary counters
* ``# 🗺️ Factor Research Index`` title
* ``> [!info]`` MOC callout (static)
* Sentinel-bounded insight block (regenerated from consolidation log)
* Three base embeds: directions / factors / recent batches
* ``> [!abstract]-`` collapsible system status footer

Side effect: every refresh also syncs lifecycle fields (``status``,
``duplicate_of``) from ``factors/F*.yaml`` into ``factors/F*.md``
frontmatter so the ``factors.base`` view never shows a retired factor.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from research.memory.cockpit import assess as assess_cockpit
from research.memory.cockpit import render_cockpit_block
from research.memory.factor_md_sync import sync_all_factor_md
from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml

_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(?P<fm>.*?)\n---\s*\n?(?P<body>.*)", re.DOTALL
)
_INDEX_FRONTMATTER_RE = _FRONTMATTER_RE

_NON_ACTIVE_DIRECTION_STATUSES = {"dead", "merged", "archived"}

# Seed content for ``_bases/*.base`` — idempotently planted if the file is
# missing. Keeps tests, fresh bootstraps, and drift-recovery hands-off:
# deleting a base file then calling refresh_index restores it. Hand-edits
# to existing base files are preserved (we only write when the file is
# absent). Kept minimal — the production vault's tuned versions live at
# ``storage/vault/_bases/*.base`` and can diverge freely.
_BASE_BLUEPRINTS: dict[str, str] = {
    "directions.base": (
        'filters:\n'
        '  and:\n'
        '    - file.inFolder("directions")\n'
        '    - file.ext == "md"\n'
        'views:\n'
        '  - type: table\n'
        '    name: "活跃方向"\n'
        '    filters:\n'
        '      not:\n'
        '        - status == "dead"\n'
        '    order: [file.name, status, priority, rounds, admits, last_batch]\n'
    ),
    "factors.base": (
        'filters:\n'
        '  and:\n'
        '    - file.inFolder("factors")\n'
        '    - file.ext == "md"\n'
        '    - decision == "admit"\n'
        '    - status == "active"\n'
        'views:\n'
        '  - type: table\n'
        '    name: "因子库"\n'
        '    order: [file.name, direction, composite_grade, ic_mean_validation, ic_ir_validation]\n'
    ),
    "recent_batches.base": (
        'filters:\n'
        '  and:\n'
        '    - file.inFolder("batches")\n'
        '    - file.name == "judge"\n'
        'views:\n'
        '  - type: table\n'
        '    name: "最近 batch"\n'
        '    limit: 10\n'
        '    order: [batch_id, direction, admit_count, reject_count, judged_at]\n'
    ),
}


def _ensure_base_files(paths: StoragePaths) -> None:
    """Idempotently plant the three ``_bases/*.base`` files if missing."""
    bases_dir = paths.vault_dir / "_bases"
    bases_dir.mkdir(parents=True, exist_ok=True)
    for fname, content in _BASE_BLUEPRINTS.items():
        fp = bases_dir / fname
        if not fp.exists():
            fp.write_text(content, encoding="utf-8")

HOT_TOPICS_BEGIN = "<!-- BEGIN HOT-TOPICS-LLM -->"
HOT_TOPICS_END = "<!-- END HOT-TOPICS-LLM -->"
# Deprecated sentinels — kept exported so older call sites / tests
# import cleanly, but the new INDEX layout does not emit them.
BEGIN_SENTINEL = "<!-- BEGIN AUTO-SECTION -->"
END_SENTINEL = "<!-- END AUTO-SECTION -->"
FACTOR_LIB_BEGIN_SENTINEL = "<!-- BEGIN FACTOR-LIBRARY -->"
FACTOR_LIB_END_SENTINEL = "<!-- END FACTOR-LIBRARY -->"


def _read_frontmatter_and_body(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if m is None:
        return {}, text
    fm = yaml.safe_load(m.group("fm"))
    return (fm if isinstance(fm, dict) else {}), m.group("body")


def _extract_sentinel_block(text: str, begin: str, end: str) -> str | None:
    """Return an existing sentinel-bounded block, preserving LLM-owned prose."""
    pattern = re.compile(
        re.escape(begin) + r"\n.*?\n" + re.escape(end),
        re.DOTALL,
    )
    matches = pattern.findall(text)
    if len(matches) != 1:
        return None
    return matches[0]


def _render_default_hot_topics_block() -> str:
    return "\n".join(
        [
            HOT_TOPICS_BEGIN,
            "> [!warning]- 🔥 Hot Topics（LLM 维护）",
            "> 当前无活跃跨批模式。`/pattern-scout` 只允许改写本块。",
            HOT_TOPICS_END,
        ]
    )


def _migrate_legacy_hot_topics_block(paths: StoragePaths) -> str | None:
    """Render old ``_meta/hot_topics.md`` frontmatter into the new INDEX block.

    This is a one-way compatibility bridge. New writes should target the
    INDEX ``HOT-TOPICS-LLM`` block directly.
    """
    legacy = paths.vault_meta_dir / "hot_topics.md"
    if not legacy.exists():
        return None
    fm, _ = _read_frontmatter_and_body(legacy)
    patterns = fm.get("patterns") or []
    if not isinstance(patterns, list):
        return None

    lines = [HOT_TOPICS_BEGIN, "> [!warning]+ 🔥 Hot Topics（LLM 维护）"]
    if not patterns:
        lines.append("> 当前无活跃跨批模式。")
    else:
        icon_by_conf = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        for p in patterns[:5]:
            if not isinstance(p, dict):
                continue
            conf = str(p.get("confidence") or "medium").lower()
            icon = icon_by_conf.get(conf, "⚪")
            pid = str(p.get("id") or "").strip()
            title = str(p.get("title") or "(untitled)").strip()
            affected = ", ".join(p.get("affected_directions") or []) or "—"
            hint = str(p.get("action_hint") or "").strip()
            suffix = f" → {hint}" if hint else ""
            header = f"{pid} " if pid else ""
            lines.append(f"> - {icon} **{header}{title}** · dirs: {affected}{suffix}")
    lines.append(HOT_TOPICS_END)
    return "\n".join(lines)


def _load_hot_topics_block(paths: StoragePaths) -> str:
    """Load the LLM-owned INDEX hot-topics block, repairing if absent."""
    if paths.vault_index_file.exists():
        text = paths.vault_index_file.read_text(encoding="utf-8")
        existing = _extract_sentinel_block(text, HOT_TOPICS_BEGIN, HOT_TOPICS_END)
        if existing is not None:
            return existing
    return _migrate_legacy_hot_topics_block(paths) or _render_default_hot_topics_block()


def _read_direction_frontmatter_and_body(
    path: Path,
) -> tuple[dict[str, Any], str]:
    """Backwards-compat alias — keep import stable for older tests."""
    return _read_frontmatter_and_body(path)


def _count_active_threads(body: str) -> int:
    return len(re.findall(r"\[◉ ACTIVE\]", body))


def collect_direction_stats(directions_dir: str | Path) -> list[dict[str, Any]]:
    """Return one row per ``directions/*.md`` (used by frontmatter counters
    and by external consumers). Bases does the display work; this is purely
    for summary counts.
    """
    rows: list[dict[str, Any]] = []
    p = Path(directions_dir)
    if not p.exists():
        return rows
    for md in sorted(p.glob("*.md")):
        fm, body = _read_frontmatter_and_body(md)
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
    total = 0
    for f in p.glob("F*.yaml"):
        try:
            data = load_yaml(f)
        except Exception:
            continue
        if isinstance(data, dict) and data.get("status") == "retired":
            continue
        total += 1
    return total


def _factor_id_key(path: Path) -> tuple[int, str]:
    stem = path.stem
    digits = "".join(c for c in stem if c.isdigit())
    return (int(digits) if digits else 1 << 30, stem)


def collect_admitted_factors(factors_dir: str | Path) -> list[dict[str, Any]]:
    """Return one row per non-retired ``F*.yaml``. Kept for compat — the
    INDEX itself no longer renders a factor list, but callers (tests,
    periodic audits) still use this.
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
            fm, _ = _read_frontmatter_and_body(md_path)
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


def _count_active_directions(rows: list[dict[str, Any]]) -> int:
    return sum(
        1 for r in rows if r.get("status") not in _NON_ACTIVE_DIRECTION_STATUSES
    )


def _read_state_summary(paths: StoragePaths) -> tuple[int | None, str | None]:
    try:
        data = load_yaml(paths.state_file)
    except FileNotFoundError:
        return None, None
    if not isinstance(data, dict):
        return None, None
    r = data.get("round")
    lb = data.get("last_batch")
    return (
        int(r) if r is not None else None,
        lb if isinstance(lb, str) else None,
    )


def _render_frontmatter(
    *,
    round_counter: int,
    last_batch: str | None,
    total_active_directions: int,
    total_admitted: int,
    last_consolidation_round: int | None,
    generated_at: str,
) -> str:
    lines = [
        "---",
        f"generated_at: {generated_at}",
        f"round: {round_counter}",
        f"total_active_directions: {total_active_directions}",
        f"total_factors_admitted: {total_admitted}",
        f"last_batch: {last_batch if last_batch else 'null'}",
        "last_consolidation_round: "
        + (
            str(last_consolidation_round)
            if last_consolidation_round is not None
            else "null"
        ),
        "---",
    ]
    return "\n".join(lines) + "\n"


def _render_moc_body(
    *,
    round_counter: int,
    last_batch: str | None,
    total_admitted: int,
    total_active_directions: int,
    last_consolidation_round: int | None,
    cockpit_block: str,
    hot_topics_block: str,
) -> str:
    """Render the body below the frontmatter. Stable, minimal layout.

    INDEX carries no row data — both humans (via Bases) and LLMs (via
    ``research memory snapshot``) pull from the same frontmatter source.
    The cockpit block up top gives the LLM derived state + next-action
    directives.
    """
    consolidation_cell = (
        f"round {last_consolidation_round}"
        if last_consolidation_round is not None
        else "—"
    )
    return "\n".join(
        [
            "# 🗺️ Factor Research Index",
            "",
            "> [!info] MOC · Map of Content",
            "> 路口页。人看下方 Bases 三表；**LLM 启动读此文件顶部 Cockpit 块**"
            "（派生状态 + 下一步指令）；拿数据用 "
            "`PYTHONPATH=src python3 -m research memory snapshot`。",
            "",
            cockpit_block,
            "",
            hot_topics_block,
            "",
            "## 🎯 方向总览 (Bases)",
            "",
            "![[_bases/directions.base]]",
            "",
            "## 📚 因子库 (Bases)",
            "",
            "![[_bases/factors.base]]",
            "",
            "## 📊 最近 Batch (Bases)",
            "",
            "![[_bases/recent_batches.base]]",
            "",
            "---",
            "",
            "> [!abstract]- 系统状态",
            f"> - Round: **{round_counter}** · Admitted: **{total_admitted}** · Active directions: **{total_active_directions}**",
            f"> - Last batch: **{last_batch or '—'}**",
            f"> - Last consolidation: **{consolidation_cell}**",
            "> - 格式 audit：运行 `research audit index` 检查漂移",
            "",
        ]
    )


def refresh_index(
    paths: StoragePaths,
    round_counter: int,
    last_consolidation_round: int | None = None,
) -> Path:
    """Rewrite INDEX.md to a minimal MOC layout.

    The file is fully deterministic given ``(directions/, factors/,
    batches/, state.yaml, _meta/consolidation_log.md)``. Re-running with
    no source changes produces byte-identical output except for
    ``generated_at``.
    """
    # Seed _bases/*.base if this is a fresh vault — no-op otherwise.
    _ensure_base_files(paths)

    # Keep F*.md frontmatter in sync with F*.yaml lifecycle before anyone
    # (Bases, audits, counters) reads it.
    sync_all_factor_md(paths)

    rows = collect_direction_stats(paths.directions_dir)
    total_admitted = count_admitted_factors(paths.factors_dir)
    total_active_directions = _count_active_directions(rows)

    _, last_batch = _read_state_summary(paths)

    frontmatter_block = _render_frontmatter(
        round_counter=round_counter,
        last_batch=last_batch,
        total_active_directions=total_active_directions,
        total_admitted=total_admitted,
        last_consolidation_round=last_consolidation_round,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    )
    cockpit_block = render_cockpit_block(assess_cockpit(paths))
    hot_topics_block = _load_hot_topics_block(paths)

    body = _render_moc_body(
        round_counter=round_counter,
        last_batch=last_batch,
        total_admitted=total_admitted,
        total_active_directions=total_active_directions,
        last_consolidation_round=last_consolidation_round,
        cockpit_block=cockpit_block,
        hot_topics_block=hot_topics_block,
    )

    index_path = paths.vault_index_file
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(frontmatter_block + "\n" + body, encoding="utf-8")
    return index_path
