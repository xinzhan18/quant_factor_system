"""Surgical frontmatter update for ``vault/directions/{name}.md``.

Direction files are LLM-maintained markdown with a YAML frontmatter
block. Python writes exactly five mechanical fields after each archive:

* ``rounds`` — how many times this direction has been mined (increment)
* ``admits`` — cumulative admitted count (increment by N)
* ``last_batch`` — batch_id of the most recent run
* ``last_admits`` — F{id} list from the most recent admission
* ``last_activity`` — ISO-8601 timestamp

Everything else — narrative log, thread list, hypothesis text — is
untouched. We parse the ``---\\n...\\n---`` frontmatter block, patch
the dict, and rewrite with the same body. This is a **surgical update**
rather than a full markdown rewrite because the LLM-written body
must not drift.

When the file doesn't exist, we create it with a minimal skeleton.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

_FRONTMATTER_RE = re.compile(
    r"\A---\s*\n(?P<fm>.*?)\n---\s*\n?(?P<body>.*)",
    re.DOTALL,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _parse_or_init(path: Path) -> tuple[dict[str, Any], str]:
    """Read frontmatter + body, returning (fm_dict, body_text).

    If the file doesn't exist, return an empty dict and an empty body —
    caller will fill it in.
    """
    if not path.exists():
        return {}, ""
    text = path.read_text(encoding="utf-8")
    m = _FRONTMATTER_RE.match(text)
    if not m:
        # No frontmatter block — treat whole file as body
        return {}, text
    fm = yaml.safe_load(m.group("fm")) or {}
    if not isinstance(fm, dict):
        fm = {}
    return fm, m.group("body")


def _serialize(fm: dict[str, Any], body: str) -> str:
    fm_text = yaml.dump(
        fm,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )
    return f"---\n{fm_text.rstrip()}\n---\n{body}"


def update_direction_frontmatter(
    direction_path: str | Path,
    *,
    batch_id: str,
    new_admits: list[str],
    goal: str | None = None,
) -> dict[str, Any]:
    """Apply a post-archive frontmatter patch.

    Parameters
    ----------
    direction_path
        Path to ``vault/directions/{name}.md``.
    batch_id
        Most recent batch that just archived.
    new_admits
        List of F{id} strings admitted in this batch (may be empty).
    goal
        Optional short goal string for the most recent run — appended
        to frontmatter as ``last_goal`` for human reference.

    Returns
    -------
    dict[str, Any]
        The updated frontmatter dict (useful for the caller to inspect).
    """
    path = Path(direction_path)
    fm, body = _parse_or_init(path)

    # Create skeleton on first update
    if not fm:
        fm = {
            "direction_id": path.stem,
            "rounds": 0,
            "admits": 0,
            "members": [],
            "status": "active",
            "created_at": _now_iso(),
        }
    if not body:
        body = f"\n# {path.stem}\n\n_(Body will be filled by Phase 5 consolidation.)_\n"

    # Increment counters
    fm["rounds"] = int(fm.get("rounds", 0)) + 1
    fm["admits"] = int(fm.get("admits", 0)) + len(new_admits)

    # Deduplicate + append members
    members = list(fm.get("members") or [])
    for fid in new_admits:
        if fid not in members:
            members.append(fid)
    fm["members"] = members

    fm["last_batch"] = batch_id
    fm["last_admits"] = new_admits
    fm["last_activity"] = _now_iso()
    if goal is not None:
        fm["last_goal"] = goal

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_serialize(fm, body), encoding="utf-8")

    return fm
