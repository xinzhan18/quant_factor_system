"""Filter Phase-5 distillation findings by direction / lessons scope.

Phase E orchestrator reads ``_consolidation/findings/*.md`` produced by the
4 distillation specialists, peeks at each finding's YAML frontmatter, and
decides which writer subagents actually need to run.

Design choice: findings are **Markdown + YAML frontmatter**, not pure YAML
(project rule R1 — markdown for LLM consumers, YAML for Python-only data).
This module only parses frontmatter (the narrow machine-readable slice);
writers and humans read the body as-is.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_FM_RE = re.compile(r"\A---\s*\n(?P<fm>.*?)\n---\s*\n?", re.DOTALL)


@dataclass(frozen=True)
class FindingMeta:
    """Machine-readable slice of ``_consolidation/findings/F00N.md``.

    Body lives in ``path``; callers that need it read from disk. The
    frontmatter schema is:

    ```yaml
    finding_id: F001                            # required
    specialist: pattern_analyst                 # required, one of 4 names
    severity: high | medium | low               # required
    affected_directions: [stochastic_position, ...] | []
    touches_lessons: true | false
    batches_referenced: [batch_041, ...]
    ```
    """

    path: Path
    finding_id: str
    specialist: str
    severity: str
    affected_directions: list[str]
    touches_lessons: bool
    batches_referenced: list[str]


def _parse_frontmatter(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    text = path.read_text(encoding="utf-8")
    m = _FM_RE.match(text)
    if m is None:
        return {}
    data = yaml.safe_load(m.group("fm"))
    return data if isinstance(data, dict) else {}


def load_findings(findings_dir: Path) -> list[FindingMeta]:
    """Load every finding md under *findings_dir* into ``FindingMeta``.

    Scans recursively to support both layouts:
      - legacy flat: ``findings/F001.md``
      - new per-specialist: ``findings/{specialist}/001.md``

    Returns empty list when the directory doesn't exist or is empty. Files
    with invalid frontmatter are skipped silently — the specialist subagent
    bears responsibility for producing valid files; a malformed one is
    treated as absent rather than blocking the orchestrator.
    """
    if not findings_dir.exists():
        return []
    out: list[FindingMeta] = []
    for md in sorted(findings_dir.rglob("*.md")):
        fm = _parse_frontmatter(md)
        finding_id = str(fm.get("finding_id") or "")
        specialist = str(fm.get("specialist") or "")
        if not finding_id or not specialist:
            continue
        out.append(
            FindingMeta(
                path=md,
                finding_id=finding_id,
                specialist=specialist,
                severity=str(fm.get("severity") or "medium").lower(),
                affected_directions=list(fm.get("affected_directions") or []),
                touches_lessons=bool(fm.get("touches_lessons")),
                batches_referenced=list(fm.get("batches_referenced") or []),
            )
        )
    return out


def findings_for_direction(
    direction: str, findings: list[FindingMeta]
) -> list[FindingMeta]:
    """Return findings that name *direction* in ``affected_directions``."""
    return [f for f in findings if direction in f.affected_directions]


def findings_for_lessons(findings: list[FindingMeta]) -> list[FindingMeta]:
    """Return findings with ``touches_lessons=true``."""
    return [f for f in findings if f.touches_lessons]


def touched_directions(findings: list[FindingMeta]) -> list[str]:
    """Union of all ``affected_directions`` across findings — the writer
    dispatch set. Sorted for deterministic ordering."""
    seen: set[str] = set()
    for f in findings:
        seen.update(f.affected_directions)
    return sorted(seen)
