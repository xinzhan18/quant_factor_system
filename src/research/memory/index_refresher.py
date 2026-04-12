"""Regenerate the lower-half statistics table of ``vault/INDEX.md``.

INDEX.md has two halves:

* **Upper half** — LLM-maintained narrative listing active directions
  and recent highlights. Phase 5 CONSOLIDATION rewrites it.
* **Lower half** — machine-generated statistics table bounded by the
  HTML comments ``<!-- BEGIN AUTO-SECTION -->`` and
  ``<!-- END AUTO-SECTION -->``. Python regenerates it after every
  archive based on scanning ``directions/`` and ``factors/``.

This module only touches the lower half. It:

1. Reads every ``directions/{name}.md`` frontmatter and collects
   ``direction_id``, ``status``, ``rounds``, ``admits``, ``last_batch``.
2. Reads every ``factors/F*.yaml`` to count totals.
3. Reads ``state.yaml`` for ``round`` + ``last_consolidation`` (optional).
4. Writes a fresh markdown table between the sentinels, preserving the
   upper half byte-for-byte.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml

BEGIN_SENTINEL = "<!-- BEGIN AUTO-SECTION -->"
END_SENTINEL = "<!-- END AUTO-SECTION -->"

_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(?P<fm>.*?)\n---\s*\n?(?P<body>.*)", re.DOTALL
)


def _read_direction_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        return {}
    fm = yaml.safe_load(m.group("fm"))
    return fm if isinstance(fm, dict) else {}


def collect_direction_stats(directions_dir: str | Path) -> list[dict[str, Any]]:
    """Return a list of frontmatter dicts for all direction md files."""
    rows: list[dict[str, Any]] = []
    p = Path(directions_dir)
    if not p.exists():
        return rows
    for md in sorted(p.glob("*.md")):
        fm = _read_direction_frontmatter(md)
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
            }
        )
    return rows


def count_admitted_factors(factors_dir: str | Path) -> int:
    p = Path(factors_dir)
    if not p.exists():
        return 0
    return sum(1 for f in p.glob("F*.yaml"))


def render_auto_section(
    direction_rows: list[dict[str, Any]],
    total_admitted: int,
    round_counter: int,
    last_consolidation_round: int | None,
) -> str:
    """Build the markdown between the BEGIN/END sentinels."""
    lines = [BEGIN_SENTINEL, ""]

    # Direction table
    lines.append("| Direction | Status | Priority | Rounds | Admits | Last batch |")
    lines.append("|---|---|---|---|---|---|")
    if not direction_rows:
        lines.append("| _no directions yet_ | — | — | 0 | 0 | — |")
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


def refresh_index(
    paths: StoragePaths,
    round_counter: int,
    last_consolidation_round: int | None = None,
) -> Path:
    """Regenerate the auto-section of INDEX.md in place.

    Preserves everything outside the ``BEGIN_SENTINEL`` / ``END_SENTINEL``
    block. If the file is missing, creates a minimal INDEX with only
    the auto-section.
    """
    rows = collect_direction_stats(paths.directions_dir)
    total_admitted = count_admitted_factors(paths.factors_dir)
    auto_text = render_auto_section(
        rows, total_admitted, round_counter, last_consolidation_round
    )

    index_path = paths.vault_index_file
    if not index_path.exists():
        # Create a minimal skeleton with the auto-section only
        skeleton = (
            "# Factor Research Index\n\n"
            "_Upper half is LLM-maintained; Phase 5 consolidation rewrites it._\n\n"
            "---\n\n"
            "## Statistics (machine-generated)\n\n"
            f"{auto_text}\n"
        )
        index_path.parent.mkdir(parents=True, exist_ok=True)
        index_path.write_text(skeleton, encoding="utf-8")
        return index_path

    text = index_path.read_text(encoding="utf-8")
    if BEGIN_SENTINEL in text and END_SENTINEL in text:
        # Replace the auto-section in place
        pattern = re.compile(
            re.escape(BEGIN_SENTINEL) + r".*?" + re.escape(END_SENTINEL),
            re.DOTALL,
        )
        new_text = pattern.sub(auto_text, text)
    else:
        # Sentinels missing — append at the end
        new_text = text.rstrip() + "\n\n" + auto_text + "\n"

    index_path.write_text(new_text, encoding="utf-8")
    return index_path
