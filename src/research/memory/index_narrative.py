"""Regenerate the INDEX.md narrative blocks — "最近 Batch" + "活跃方向".

Historically these two sections were LLM-maintained; under the autonomous
mining loop LLM compliance decayed batch-after-batch (``最近 Batch`` list
stopped at batch_018 while the loop reached batch_029). Python owns them
now, bounded by new sentinel comment pairs so future LLM edits outside
the sentinels survive regeneration.

Data sources:

* **最近 Batch**: each ``batches/batch_*/judge.md`` ``> [!abstract]+`` block
* **活跃方向**: each ``directions/{tag}.md`` frontmatter (status, priority,
  rounds, admits, last_batch) plus the latest ``### YYYY-MM-DD [[batches/...]]``
  entry in the Narrative Log body.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from research.storage.paths import StoragePaths

RECENT_BEGIN = "<!-- BEGIN NARRATIVE-RECENT -->"
RECENT_END = "<!-- END NARRATIVE-RECENT -->"
DIRECTIONS_BEGIN = "<!-- BEGIN NARRATIVE-DIRECTIONS -->"
DIRECTIONS_END = "<!-- END NARRATIVE-DIRECTIONS -->"

_BATCH_DIR_RE = re.compile(r"^batch_\d+$")

# Match ``> [!abstract]+ batch_025 · ...`` up to the blank line that
# terminates the Obsidian callout. The callout is multi-line, each starting
# with ``> ``. The first line's tail (after ``[!abstract]+``) carries the
# batch identifier and candidate count — we want to preserve it.
_ABSTRACT_BLOCK_RE = re.compile(
    r"^>\s*\[!abstract\]\+?\s*(?P<first>[^\n]*)\n(?P<rest>(?:^>.*\n)*)",
    re.MULTILINE,
)

_FM_RE = re.compile(r"\A---\s*\n(?P<fm>.*?)\n---\s*\n?(?P<body>.*)", re.DOTALL)

# Find ``### YYYY-MM-DD [[batches/batch_N/judge|batch_N]]`` headings in the
# Narrative Log. We pick the last one and grab its first content paragraph.
_LOG_HEADING_RE = re.compile(
    r"^###\s+(?P<date>\d{4}-\d{2}-\d{2})\s+\[\[batches/(?P<batch>batch_\d+)[^\]]*\]\][^\n]*\n"
    r"(?P<body>.*?)(?=^###\s|^##\s|\Z)",
    re.MULTILINE | re.DOTALL,
)

_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}
_STATUS_ORDER = {
    "productive": 0,
    "exploring": 1,
    "saturated": 2,
    "dead": 3,
    "merged": 4,
    "archived": 5,
}


def _batch_sort_key(p: Path) -> int:
    """Sort batch dirs numerically (batch_001 < batch_010 < batch_025)."""
    m = re.search(r"(\d+)$", p.name)
    return int(m.group(1)) if m else -1


def extract_abstract_block(judge_text: str) -> str | None:
    """Return the first-line body of the ``> [!abstract]+`` callout, trimmed.

    The callout is 1-5 lines. We concatenate them (stripping the ``> `` prefix)
    with ``\\n`` joins so the result drops cleanly into a bullet.
    """
    m = _ABSTRACT_BLOCK_RE.search(judge_text)
    if not m:
        return None
    first = (m.group("first") or "").strip()
    rest = m.group("rest") or ""
    lines: list[str] = []
    if first:
        lines.append(first)
    for line in rest.splitlines():
        s = line.lstrip()
        if not s.startswith(">"):
            break
        content = s[1:].strip()
        if content:
            lines.append(content)
    return " · ".join(lines) if lines else None


def _read_frontmatter_and_body(path: Path) -> tuple[dict[str, Any], str]:
    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if not m:
        return {}, text
    import yaml
    fm = yaml.safe_load(m.group("fm")) or {}
    if not isinstance(fm, dict):
        fm = {}
    return fm, m.group("body")


def _latest_narrative_entry(body: str) -> tuple[str, str] | None:
    """Return ``(batch_id, first_content_line)`` from the most recent log entry."""
    matches = list(_LOG_HEADING_RE.finditer(body))
    if not matches:
        return None
    last = matches[-1]
    bid = last.group("batch")
    entry_body = last.group("body").strip()
    # First non-blank line of the entry body — skip leading blockquotes/empties
    first_line = ""
    for line in entry_body.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("**") or s.startswith(">"):
            # Obsidian bold line or callout — still take it, it's the gist
            first_line = s
            break
        first_line = s
        break
    return bid, first_line


def render_recent_batches(
    batches_dir: str | Path, *, max_batches: int = 15
) -> str:
    """Render the sentinel-bounded ``## 最近 Batch`` bullet list."""
    p = Path(batches_dir)
    if not p.exists():
        return f"{RECENT_BEGIN}\n\n_（no batches yet）_\n\n{RECENT_END}"
    dirs = sorted(
        (d for d in p.iterdir() if d.is_dir() and _BATCH_DIR_RE.match(d.name)),
        key=_batch_sort_key,
        reverse=True,
    )
    lines = [RECENT_BEGIN, ""]
    taken = 0
    for bdir in dirs:
        if taken >= max_batches:
            break
        jpath = bdir / "judge.md"
        if not jpath.exists():
            continue
        text = jpath.read_text(encoding="utf-8")
        abstract = extract_abstract_block(text)
        if abstract is None:
            continue
        lines.append(f"- [[batches/{bdir.name}/judge|{bdir.name}]] — {abstract}")
        taken += 1
    if taken == 0:
        lines.append("_（no parseable batch abstracts）_")
    lines += ["", RECENT_END]
    return "\n".join(lines)


def _direction_sort_key(row: dict[str, Any]) -> tuple[int, int, str]:
    return (
        _STATUS_ORDER.get(row.get("status", "exploring"), 99),
        _PRIORITY_ORDER.get(row.get("priority", "medium"), 99),
        row.get("direction_id", ""),
    )


def render_active_directions(directions_dir: str | Path) -> str:
    """Render the sentinel-bounded ``## 活跃方向`` narrative section.

    Each direction gets a H3 heading plus a 1-line summary cobbled from
    frontmatter + latest narrative-log entry. Dead / merged / archived
    directions are excluded (those belong in a separate ledger, not the
    active section).
    """
    p = Path(directions_dir)
    if not p.exists():
        return f"{DIRECTIONS_BEGIN}\n\n_（no directions yet）_\n\n{DIRECTIONS_END}"
    rows: list[dict[str, Any]] = []
    for md in sorted(p.glob("*.md")):
        fm, body = _read_frontmatter_and_body(md)
        if not fm:
            continue
        status = fm.get("status", "exploring")
        if status in {"dead", "merged", "archived"}:
            continue
        latest = _latest_narrative_entry(body)
        rows.append(
            {
                "direction_id": fm.get("direction_id", md.stem),
                "status": status,
                "priority": fm.get("priority", "medium"),
                "rounds": int(fm.get("rounds", 0)),
                "admits": int(fm.get("admits", 0)),
                "last_batch": fm.get("last_batch") or "—",
                "last_goal": fm.get("last_goal") or "",
                "latest_batch": latest[0] if latest else None,
                "latest_line": latest[1] if latest else "",
            }
        )
    rows.sort(key=_direction_sort_key)
    lines = [DIRECTIONS_BEGIN, ""]
    if not rows:
        lines.append("_（no active directions）_")
    else:
        for r in rows:
            tag = r["direction_id"]
            header = (
                f"### [[directions/{tag}|{tag}]] "
                f"`{r['status']}` `{r['priority']}`"
            )
            lines.append(header)
            stats = (
                f"累计 {r['rounds']} rounds · **{r['admits']} admits** · "
                f"last {r['last_batch']}"
            )
            lines.append(stats + ".")
            if r["latest_line"]:
                snippet = r["latest_line"]
                if len(snippet) > 240:
                    snippet = snippet[:237] + "…"
                lines.append(snippet)
            elif r["last_goal"]:
                snippet = r["last_goal"]
                if len(snippet) > 240:
                    snippet = snippet[:237] + "…"
                lines.append(f"Goal: {snippet}")
            lines.append("")
    lines.append(DIRECTIONS_END)
    return "\n".join(lines)


def _replace_sentinel_block(
    text: str, begin: str, end: str, replacement: str
) -> str:
    """Replace content between ``begin`` and ``end`` sentinels (inclusive).

    If the sentinels are absent, returns ``text`` unchanged — caller decides
    whether to insert them.
    """
    if begin not in text or end not in text:
        return text
    pattern = re.compile(
        re.escape(begin) + r".*?" + re.escape(end), re.DOTALL
    )
    return pattern.sub(replacement, text)


def _ensure_sentinel_block(
    text: str,
    begin: str,
    end: str,
    replacement: str,
    *,
    heading: str,
) -> str:
    """Place a sentinel-bounded block into INDEX.md, absorbing any prior
    LLM-written section with the same heading.

    Decision tree:

    1. Sentinels already present → replace body between them in place.
    2. ``## {heading}`` already exists → overwrite that whole section
       (heading + body up to the next ``## `` or EOF) with a fresh
       ``## {heading}\\n\\n{replacement}\\n``. This absorbs the stale
       LLM narrative under the same heading so we don't end up with
       duplicate sections (``## 活跃方向`` from the old INDEX +
       ``## 活跃方向`` from the new sentinel block).
    3. Neither → insert a new ``## {heading}`` block before ``## 因子库``,
       or append to the file if that anchor is absent.
    """
    if begin in text and end in text:
        return _replace_sentinel_block(text, begin, end, replacement)

    new_section = f"## {heading}\n\n{replacement}\n"

    # Case 2: heading already exists — replace the whole section
    heading_pat = re.compile(
        rf"^## +{re.escape(heading)}\b[^\n]*\n(?:.*?)(?=^##\s|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = heading_pat.search(text)
    if m:
        # Preserve trailing blank line if the replaced block had one
        tail = "\n" if not new_section.endswith("\n\n") else ""
        return text[: m.start()] + new_section + tail + text[m.end():]

    # Case 3: append before 因子库, else end of file
    idx = text.find("## 因子库")
    if idx >= 0:
        return text[:idx] + new_section + "\n" + text[idx:]
    return text.rstrip() + "\n\n" + new_section


def refresh_narrative(paths: StoragePaths) -> Path:
    """Regenerate the two narrative sentinel blocks in INDEX.md."""
    index_path = paths.vault_index_file
    if not index_path.exists():
        return index_path

    text = index_path.read_text(encoding="utf-8")

    recent_block = render_recent_batches(paths.batches_dir)
    directions_block = render_active_directions(paths.directions_dir)

    text = _ensure_sentinel_block(
        text,
        RECENT_BEGIN,
        RECENT_END,
        recent_block,
        heading="最近 Batch",
    )
    text = _ensure_sentinel_block(
        text,
        DIRECTIONS_BEGIN,
        DIRECTIONS_END,
        directions_block,
        heading="活跃方向",
    )

    index_path.write_text(text, encoding="utf-8")
    return index_path
