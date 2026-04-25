"""Pattern Scout — cross-batch pattern recognition for the LLM orchestrator.

Phase C of the subagent refactor. The Pattern Scout is run at Phase 0 of
``/factor-mine`` (after ``research memory refresh-index``). Its output is
the LLM-owned ``HOT-TOPICS-LLM`` block inside ``vault/INDEX.md`` — so the
orchestrator sees "4 batches in a row blocked by the same mechanism" from
the single startup file rather than only noticing after the 5th.

## Responsibility split (R2)

This module is **Python: I/O only**. It:

1. Scans the last *N* batches' ``judge.md`` + active directions'
   frontmatter.
2. Extracts the "方向级反思" and "跨候选对比" sections from each judge.
3. Produces a single ``_meta/pattern_scout_packet.md`` that the
   subagent reads.

It does **not** call an LLM, detect patterns, or rewrite
``INDEX.md``. Those are subagent responsibilities performed in an isolated
Claude context, restricted to the HOT-TOPICS-LLM sentinel block.

Why this split matters for iteration isolation:

* The orchestrator context sees only the subagent's ≤10-line return
  ("patterns detected: vol_20d absorption, …"), not the raw judge.md
  bodies. This keeps Phase 0 light even when the batch history grows.
* Python owns the I/O aggregation so the contract the subagent reads
  is deterministic (audit-friendly).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import yaml

from research.memory.index_refresher import HOT_TOPICS_BEGIN, HOT_TOPICS_END
from research.storage.paths import StoragePaths

_FM_RE = re.compile(r"\A---\s*\n(?P<fm>.*?)\n---\s*\n(?P<body>.*)", re.DOTALL)

# H2 section names to extract from judge.md bodies. Kept in priority order —
# earlier entries appear first in the packet (main agent skims top-down).
_JUDGE_SECTIONS = ("方向级反思", "跨候选对比", "Thread 进展")

PACKET_FILENAME = "pattern_scout_packet.md"


@dataclass
class _JudgeExcerpt:
    batch_id: str
    direction: str | None
    admit: int
    reserve: int
    reject: int
    total: int
    section_excerpts: dict[str, str]  # section_name -> body (H2-scoped)


def _parse_fm_and_body(path: Path) -> tuple[dict, str]:
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if m is None:
        return {}, text
    fm_raw = yaml.safe_load(m.group("fm")) or {}
    body = m.group("body")
    return (fm_raw if isinstance(fm_raw, dict) else {}), body


def _extract_h2_section(body: str, section_title: str) -> str:
    """Return the body of one H2 section, empty string if missing.

    Scans until the next ``## `` header or EOF. Keeps the leading ``## X``
    line so downstream consumers can tell which section they got.
    """
    # Match ``## <title>`` exactly as a heading line; title may have trailing
    # whitespace. Non-greedy to stop at the next ``## ``.
    pattern = re.compile(
        rf"^##\s+{re.escape(section_title)}\s*$.*?(?=^##\s+|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    m = pattern.search(body)
    return m.group(0).strip() if m else ""


def _collect_recent_batches(
    paths: StoragePaths, limit: int
) -> list[_JudgeExcerpt]:
    """Return up to *limit* most-recent batches, newest last (reading order).

    Batch ordering is by directory name lexicographic (``batch_001`` <
    ``batch_002`` < …), which matches chronological order since the allocator
    pads to three digits.
    """
    if not paths.batches_dir.exists():
        return []
    batch_dirs = sorted(
        (d for d in paths.batches_dir.glob("batch_*") if d.is_dir()),
        key=lambda d: d.name,
    )
    recent = batch_dirs[-limit:] if limit > 0 else batch_dirs

    out: list[_JudgeExcerpt] = []
    for d in recent:
        fm, body = _parse_fm_and_body(d / "judge.md")
        if not fm:
            continue
        summary = fm.get("batch_summary") or {}
        out.append(
            _JudgeExcerpt(
                batch_id=d.name,
                direction=fm.get("direction"),
                admit=int(fm.get("admit_count") or summary.get("admit") or 0),
                reserve=int(
                    fm.get("reserve_count") or summary.get("reserve") or 0
                ),
                reject=int(fm.get("reject_count") or summary.get("reject") or 0),
                total=int(
                    fm.get("candidate_count") or summary.get("total") or 0
                ),
                section_excerpts={
                    s: _extract_h2_section(body, s) for s in _JUDGE_SECTIONS
                },
            )
        )
    return out


def _collect_active_direction_frontmatter(
    paths: StoragePaths,
) -> list[dict]:
    """Return frontmatter for every ``directions/*.md`` that isn't archived.

    Returned dicts are keyed by direction_tag + status/priority/rounds/admits
    + last_batch fields. Callers do not need the direction body text for
    Pattern Scout purposes.
    """
    out: list[dict] = []
    if not paths.directions_dir.exists():
        return out
    for md in sorted(paths.directions_dir.glob("*.md")):
        fm, _ = _parse_fm_and_body(md)
        if not fm:
            continue
        if fm.get("status") in {"archived", "merged"}:
            continue
        out.append(
            {
                "direction_tag": fm.get("direction_tag") or md.stem,
                "status": fm.get("status"),
                "priority": fm.get("priority"),
                "rounds": fm.get("rounds"),
                "admits": fm.get("admits"),
                "last_batch": fm.get("last_batch"),
                "last_goal": fm.get("last_goal"),
            }
        )
    return out


def build_packet(paths: StoragePaths, recent: int = 10) -> str:
    """Compose the Pattern Scout packet. Pure function of on-disk state."""
    excerpts = _collect_recent_batches(paths, limit=recent)
    directions = _collect_active_direction_frontmatter(paths)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")

    lines: list[str] = []
    lines.append("# Pattern Scout Packet")
    lines.append("")
    lines.append(f"> Generated at {now} · recent={recent} batches")
    lines.append("")
    lines.append("## 任务")
    lines.append("")
    lines.append(
        "你是 Pattern Scout，扫描下方的最近 N 批 judge 摘录 + active directions "
        "frontmatter，**识别跨批的失败模式 / style 吸收律 / 重复机制**。"
        "只改写 `storage/vault/INDEX.md` 的 `HOT-TOPICS-LLM` sentinel 块。"
    )
    lines.append("")
    lines.append("## 当前 HOT-TOPICS-LLM 块")
    lines.append("")
    if paths.vault_index_file.exists():
        index_text = paths.vault_index_file.read_text(encoding="utf-8")
        start = index_text.find(HOT_TOPICS_BEGIN)
        end = index_text.find(HOT_TOPICS_END)
        if start != -1 and end != -1 and start < end:
            lines.append(index_text[start:end + len(HOT_TOPICS_END)].strip())
        else:
            lines.append("_（INDEX 尚无 HOT-TOPICS-LLM 块；先跑 research memory refresh-index）_")
    else:
        lines.append("_（INDEX.md 不存在；先跑 research memory refresh-index）_")
    lines.append("")
    lines.append("## 输出契约（INDEX.md HOT-TOPICS-LLM 块）")
    lines.append("")
    lines.append(
        "只替换 `<!-- BEGIN HOT-TOPICS-LLM -->` 到 "
        "`<!-- END HOT-TOPICS-LLM -->` 之间的内容；不要改 INDEX frontmatter、"
        "COCKPIT、Bases embed 或其它 sentinel。"
    )
    lines.append("")
    lines.append(
        "块内最多 5 条 bullet。每条包含 P{id}、confidence 图标、title、"
        "affected directions、action hint、1-2 个证据 wikilink。若无 active "
        "pattern，保留 sentinel 并写一行“当前无活跃跨批模式”。"
    )
    lines.append("")
    lines.append("## 识别启发")
    lines.append("")
    lines.append(
        "- 同一 `dominant_style`（如 `vol_20d`）在 ≥3 批、跨 ≥2 方向出现"
    )
    lines.append(
        "- 同一 rejection 形态（magnitude/ratio/power-mean）反复失败"
    )
    lines.append(
        "- 一个 direction 的 zero-admit 可以用另一 direction 已证伪的"
        "同族理由解释"
    )
    lines.append(
        "- 硬 gate `max_corr` 到同一 F{id} 反复命中（库空间饱和）"
    )
    lines.append("")
    lines.append("## Active Directions（frontmatter 摘录）")
    lines.append("")
    if not directions:
        lines.append("_（无 active direction）_")
    else:
        lines.append(
            "| direction | status | priority | rounds | admits | last_batch |"
        )
        lines.append("|---|---|---|---|---|---|")
        for d in directions:
            lines.append(
                f"| {d.get('direction_tag')} "
                f"| {d.get('status')} "
                f"| {d.get('priority')} "
                f"| {d.get('rounds')} "
                f"| {d.get('admits')} "
                f"| {d.get('last_batch')} |"
            )
    lines.append("")

    lines.append("## Recent batches（judge.md 关键段摘录）")
    lines.append("")
    if not excerpts:
        lines.append("_（无 judge 历史）_")
    else:
        for e in excerpts:
            lines.append(
                f"### {e.batch_id} · direction=`{e.direction}` · "
                f"admit={e.admit} reserve={e.reserve} reject={e.reject} "
                f"total={e.total}"
            )
            for section in _JUDGE_SECTIONS:
                excerpt = e.section_excerpts.get(section, "").strip()
                if not excerpt:
                    continue
                lines.append("")
                lines.append(excerpt)
            lines.append("")

    return "\n".join(lines)


def write_packet(paths: StoragePaths, recent: int = 10) -> Path:
    """Overwrite ``_meta/pattern_scout_packet.md`` with the latest packet."""
    paths.vault_meta_dir.mkdir(parents=True, exist_ok=True)
    packet_path = paths.vault_meta_dir / PACKET_FILENAME
    packet_path.write_text(build_packet(paths, recent=recent), encoding="utf-8")
    return packet_path


def hot_topics_target(paths: StoragePaths) -> Path:
    """Canonical file whose HOT-TOPICS-LLM block the subagent rewrites."""
    return paths.vault_index_file
