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
            "status": "exploring",
            "rounds": 0,
            "admits": 0,
            "members": [],
            "created_at": _now_iso(),
            "created_batch": batch_id,
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

    # Auto-transition: first admit in an `exploring` direction → `productive`.
    # LLMs forget to flip this in the narrative log; the mechanical rule is
    # unambiguous enough that Python owns it. Any transition out of `exploring`
    # past that point (exploring → dead / merged) remains LLM-driven — *but*
    # :func:`sync_status_from_judge` runs in phase4 too to catch the other
    # cases the LLM forgets.
    if new_admits and fm.get("status") == "exploring":
        fm["status"] = "productive"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_serialize(fm, body), encoding="utf-8")

    return fm


# ---------------------------------------------------------------------------
# Bug 5/6 — judge-declared status + thread transitions
# ---------------------------------------------------------------------------


_STATUSES = {"exploring", "productive", "saturated", "dead", "merged", "archived"}
# Accept both unquoted (`→ saturated`) and backtick-quoted (``status `productive
# → saturated` ``) forms. LLMs produce both in judge.md narrative.
_TRANSITION_PATTERN = re.compile(
    r"(?:direction[^\n]{0,40})?`?\s*([a-z_]+)\s*→\s*([a-z_]+)\s*`?", re.IGNORECASE
)
_FIRST_BATCH_DEAD_PATTERN = re.compile(
    r"direction\s+首批(?:\s*即)?\s*dead", re.IGNORECASE
)
_SATURATED_ONESIDED = re.compile(r"→\s*saturated\b")
_DEAD_ONESIDED = re.compile(r"→\s*dead\b")

# Only these direction-level transitions are mechanical-enough for Python
# to apply unilaterally. Everything else (e.g. exploring → exploring with
# a thread update) stays LLM-authored.
_ALLOWED_TRANSITIONS: set[tuple[str, str]] = {
    ("exploring", "productive"),
    ("exploring", "saturated"),
    ("exploring", "dead"),
    ("productive", "saturated"),
    ("productive", "dead"),
    ("saturated", "dead"),
}

_ACTIVE_TOKEN = "[◉ ACTIVE]"


def _parse_declared_status(judge_body: str) -> str | None:
    r"""Return the target status the judge narrative declares, or ``None``.

    Recognises three shapes:

    * ``direction status `exploring → dead``` (fully-specified)
    * ``direction 首批 dead`` / ``direction 首批即 dead`` (first-batch collapse)
    * bare ``→ saturated`` / ``→ dead`` when there is no other transition
      phrase (LLMs sometimes drop the lhs)
    """
    if _FIRST_BATCH_DEAD_PATTERN.search(judge_body):
        return "dead"

    for m in _TRANSITION_PATTERN.finditer(judge_body):
        lhs, rhs = m.group(1).lower(), m.group(2).lower()
        if lhs in _STATUSES and rhs in _STATUSES and (lhs, rhs) in _ALLOWED_TRANSITIONS:
            return rhs

    # Fallback for bare `→ saturated` / `→ dead` with no lhs
    if _DEAD_ONESIDED.search(judge_body):
        return "dead"
    if _SATURATED_ONESIDED.search(judge_body):
        return "saturated"

    return None


def _close_active_threads(body: str, batch_id: str) -> str:
    """Replace ``[◉ ACTIVE]`` with ``[✗ DISPROVEN {batch_id}]`` everywhere.

    Called when direction transitions to ``dead`` — any thread still flagged
    active is stale-by-definition. Idempotent (no-op if no ACTIVE markers).
    """
    return body.replace(_ACTIVE_TOKEN, f"[✗ DISPROVEN {batch_id}]")


def sync_status_from_judge(
    direction_path: str | Path,
    *,
    judge_body: str,
    batch_id: str,
) -> dict[str, Any]:
    """Read the judge narrative and reconcile direction frontmatter.

    This runs **after** :func:`update_direction_frontmatter` in phase4 —
    that function handles the ``exploring → productive`` auto-flip on
    admit; this one handles ``→ saturated`` / ``→ dead`` declarations
    the LLM writes in the judge narrative but forgets to propagate.

    When the target is ``dead``, the direction body's ``[◉ ACTIVE]`` thread
    markers are rewritten to ``[✗ DISPROVEN {batch_id}]`` — a dead direction
    cannot have lingering active threads (Bug 6).

    Returns the (possibly-patched) frontmatter dict. No-ops when:

    * no allowed transition is parseable from the judge body
    * the frontmatter status is already at or past the target
    """
    path = Path(direction_path)
    fm, body = _parse_or_init(path)
    if not fm:
        return fm

    target = _parse_declared_status(judge_body)
    if target is None:
        return fm

    current = fm.get("status", "exploring")
    if current == target:
        # Still close stale ACTIVE threads even if status already matches —
        # the LLM may have flipped status but forgotten the thread markers.
        if target == "dead" and _ACTIVE_TOKEN in body:
            body = _close_active_threads(body, batch_id)
            path.write_text(_serialize(fm, body), encoding="utf-8")
        return fm

    if (current, target) not in _ALLOWED_TRANSITIONS:
        return fm

    fm["status"] = target
    fm["last_activity"] = _now_iso()

    if target == "dead":
        body = _close_active_threads(body, batch_id)

    path.write_text(_serialize(fm, body), encoding="utf-8")
    return fm
