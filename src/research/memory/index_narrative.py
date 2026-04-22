"""Regenerate the INDEX ``💡 最近洞察`` callout from consolidation log.

The rest of INDEX is pure tables-via-Bases (see
:mod:`research.memory.index_refresher`). The only LLM-sourced prose is a
Phase-5 consolidation summary, which lives in
``_meta/consolidation_log.md`` and is quoted into INDEX between the
``<!-- BEGIN INSIGHT -->`` / ``<!-- END INSIGHT -->`` sentinels.

If no consolidation has run yet, a placeholder is emitted instead.
"""

from __future__ import annotations

import re
from pathlib import Path

from research.storage.paths import StoragePaths

INSIGHT_BEGIN = "<!-- BEGIN INSIGHT -->"
INSIGHT_END = "<!-- END INSIGHT -->"

# Legacy exports (still imported by older tests); kept as no-op aliases.
RECENT_BEGIN = INSIGHT_BEGIN
RECENT_END = INSIGHT_END
DIRECTIONS_BEGIN = INSIGHT_BEGIN
DIRECTIONS_END = INSIGHT_END

_CONSOLIDATION_HEADING_RE = re.compile(
    r"^##\s+(?P<title>[^\n]+)\n(?P<body>.*?)(?=^##\s|\Z)",
    re.MULTILINE | re.DOTALL,
)


def extract_latest_summary(log_text: str) -> tuple[str, str] | None:
    """Return ``(title, body)`` for the last ``## ...`` section in the log.

    ``title`` retains the heading content (e.g. ``"batch_020 · Phase 5"``);
    ``body`` is the content until the next H2 or EOF, trimmed.
    """
    matches = list(_CONSOLIDATION_HEADING_RE.finditer(log_text))
    if not matches:
        return None
    last = matches[-1]
    title = last.group("title").strip()
    body = last.group("body").strip()
    return title, body


def render_insight_block(log_path: Path) -> str:
    """Build the sentinel-bounded insight callout."""
    if not log_path.exists():
        inner = (
            "> [!tip] 💡 最近洞察\n"
            "> _（暂无 consolidation 总结 — 运行 Phase 5 后自动填充）_"
        )
        return f"{INSIGHT_BEGIN}\n{inner}\n{INSIGHT_END}"

    text = log_path.read_text(encoding="utf-8")
    parsed = extract_latest_summary(text)
    if parsed is None:
        inner = (
            "> [!tip] 💡 最近洞察\n"
            "> _（consolidation_log.md 尚无 ## 标题分段）_"
        )
        return f"{INSIGHT_BEGIN}\n{inner}\n{INSIGHT_END}"

    title, body = parsed
    # Cap each quoted line at ~200 chars to keep INDEX scannable. Body is
    # verbatim; we only prefix ``> `` so Obsidian renders it as a callout.
    body_lines = [f"> {line}" if line else ">" for line in body.splitlines()]
    quoted = "\n".join(body_lines).rstrip()
    inner = f"> [!tip] 💡 最近洞察 · {title}\n{quoted}\n> — [[_meta/consolidation_log|完整总结]]"
    return f"{INSIGHT_BEGIN}\n{inner}\n{INSIGHT_END}"


def refresh_narrative(paths: StoragePaths) -> Path:
    """Replace the insight sentinel block in INDEX.md with the latest summary."""
    index_path = paths.vault_index_file
    if not index_path.exists():
        return index_path

    log_path = paths.consolidation_log_file
    insight_block = render_insight_block(log_path)

    text = index_path.read_text(encoding="utf-8")
    if INSIGHT_BEGIN in text and INSIGHT_END in text:
        pattern = re.compile(
            re.escape(INSIGHT_BEGIN) + r".*?" + re.escape(INSIGHT_END),
            re.DOTALL,
        )
        new_text = pattern.sub(insight_block, text)
    else:
        # No sentinel present — unexpected for the new INDEX layout, but
        # degrade gracefully by appending before the first H2.
        idx = text.find("## ")
        if idx < 0:
            new_text = text.rstrip() + "\n\n" + insight_block + "\n"
        else:
            new_text = text[:idx] + insight_block + "\n\n" + text[idx:]

    index_path.write_text(new_text, encoding="utf-8")
    return index_path
