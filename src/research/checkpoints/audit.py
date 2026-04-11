"""Phase 3 audit — verify LLM-written ``judge.md`` before it's trusted.

Per refactor_plan §7, the LLM writes ``judge.md`` free-form in markdown,
but the Python audit layer enforces **six structural invariants** before
the file is accepted downstream. Any violation raises
:class:`JudgeAuditError` and the phase3 orchestrator asks the LLM to
rewrite.

Checks (mirrors the audit code in refactor_plan §7 + §7.MT):

1. **Frontmatter schema** — frontmatter parses as YAML, has required
   keys (``batch_id``, ``candidates``, ``batch_summary``), each
   candidate dict has ``candidate_id``, ``verdict``, ``hard_gate_result``.
2. **Verdict enum** — verdict is one of
   ``{admit, reserve, reject, replace}``.
3. **Hard gate not overridable** — if ``hard_gate_result != "all_pass"``,
   ``verdict`` must be ``reject``. LLM cannot promote a hard-gate failure
   to anything else.
4. **Body section coverage** — each candidate has an ``## C{id}`` H2
   section. Non-reject candidates must additionally contain ``### CP01``
   through ``### CP06`` H3 sections; reject candidates only need ``### CP01``.
5. **CP03 cites mt_bucket** (§7.MT hard rule) — for every non-reject
   candidate, the CP03 body section must contain the string ``mt_bucket``.
   This catches LLMs that see the numeric hint in the packet but forget
   to actually reference it in their reasoning.
6. **Referenced context authenticity** — every entry under a candidate's
   ``referenced_context`` list must be present in the packet's declared
   references (prevents LLM from fabricating wiki-links to files that
   weren't in the single-input packet).

The audit is defensive but not paranoid — it only catches
schema/structural problems, not semantic errors. "Did the LLM reason
correctly?" is the LLM's job; we just make sure the LLM cannot silently
skip the form.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


VALID_VERDICTS: frozenset[str] = frozenset(
    {"admit", "reserve", "reject", "replace"}
)

REQUIRED_CANDIDATE_FRONTMATTER_FIELDS: tuple[str, ...] = (
    "candidate_id",
    "verdict",
    "hard_gate_result",
)

# Non-reject candidates must have all six; rejects only need CP01.
ALL_CHECKPOINTS: tuple[str, ...] = ("CP01", "CP02", "CP03", "CP04", "CP05", "CP06")


class JudgeAuditError(ValueError):
    """Raised when ``judge.md`` violates a structural invariant."""


@dataclass
class ParsedJudgeMd:
    """Intermediate representation of a parsed judge.md."""

    frontmatter: dict[str, Any]
    body: str


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


_FRONTMATTER_PATTERN = re.compile(
    r"\A---\s*\n(?P<fm>.*?)\n---\s*\n(?P<body>.*)",
    re.DOTALL,
)


def parse_judge_md(text: str) -> ParsedJudgeMd:
    """Split YAML frontmatter from markdown body.

    Raises :class:`JudgeAuditError` if the file lacks the expected
    ``---\\n...\\n---\\n`` fence.
    """
    match = _FRONTMATTER_PATTERN.match(text)
    if not match:
        raise JudgeAuditError(
            "judge.md missing '---' frontmatter fence at start"
        )
    try:
        fm = yaml.safe_load(match.group("fm"))
    except yaml.YAMLError as exc:
        raise JudgeAuditError(f"judge.md frontmatter YAML parse error: {exc}") from exc
    if not isinstance(fm, dict):
        raise JudgeAuditError(
            f"judge.md frontmatter must be a mapping, got {type(fm).__name__}"
        )
    return ParsedJudgeMd(frontmatter=fm, body=match.group("body"))


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _check_frontmatter_schema(fm: dict[str, Any]) -> None:
    if "batch_id" not in fm:
        raise JudgeAuditError("frontmatter missing batch_id")
    if "candidates" not in fm or not isinstance(fm["candidates"], list):
        raise JudgeAuditError("frontmatter missing candidates list")
    if "batch_summary" not in fm or not isinstance(fm["batch_summary"], dict):
        raise JudgeAuditError("frontmatter missing batch_summary dict")

    for c in fm["candidates"]:
        if not isinstance(c, dict):
            raise JudgeAuditError(
                "candidate entry must be a dict, got " f"{type(c).__name__}"
            )
        for k in REQUIRED_CANDIDATE_FRONTMATTER_FIELDS:
            if k not in c:
                raise JudgeAuditError(
                    f"candidate {c.get('candidate_id', '?')!r} missing field {k!r}"
                )


def _check_verdict_enum(fm: dict[str, Any]) -> None:
    for c in fm["candidates"]:
        v = c["verdict"]
        if v not in VALID_VERDICTS:
            raise JudgeAuditError(
                f"candidate {c['candidate_id']!r} has invalid verdict {v!r} "
                f"(must be one of {sorted(VALID_VERDICTS)})"
            )


def _check_hard_gate_not_overridden(fm: dict[str, Any]) -> None:
    for c in fm["candidates"]:
        gate = c["hard_gate_result"]
        verdict = c["verdict"]
        if gate != "all_pass" and verdict != "reject":
            raise JudgeAuditError(
                f"candidate {c['candidate_id']!r}: hard_gate_result={gate!r} "
                f"but verdict={verdict!r} — hard gates cannot be overridden"
            )


def _extract_h2_section(body: str, candidate_id: str) -> str | None:
    """Return the body text under ``## C{id}`` (up to the next ``## `` or end).

    Search is tolerant to extra heading text like ``## C001 — ADMIT``.
    """
    # Match the H2 line containing the candidate id at a word boundary,
    # then capture everything up to the next H2 line or EOF.
    pattern = re.compile(
        rf"^##\s+[^\n]*\b{re.escape(candidate_id)}\b[^\n]*\n(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(body)
    return m.group(1) if m else None


def _extract_h3_section(section: str, heading: str) -> str | None:
    """Return body under ``### {heading}`` up to next H3 or H2 or EOF."""
    pattern = re.compile(
        rf"^###\s+{re.escape(heading)}\b[^\n]*\n(.*?)(?=^###\s+|^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(section)
    return m.group(1) if m else None


def _check_body_sections(fm: dict[str, Any], body: str) -> None:
    for c in fm["candidates"]:
        cid = c["candidate_id"]
        section = _extract_h2_section(body, cid)
        if section is None:
            raise JudgeAuditError(
                f"body missing '## ... {cid}' H2 section"
            )

        expected = ("CP01",) if c["verdict"] == "reject" else ALL_CHECKPOINTS
        for cp in expected:
            if _extract_h3_section(section, cp) is None:
                raise JudgeAuditError(
                    f"candidate {cid!r} body missing '### {cp}' section"
                )


def _check_cp03_cites_mt_bucket(fm: dict[str, Any], body: str) -> None:
    """§7.MT hard rule — every non-reject CP03 section must say 'mt_bucket'."""
    for c in fm["candidates"]:
        if c["verdict"] == "reject":
            continue
        cid = c["candidate_id"]
        section = _extract_h2_section(body, cid)
        if section is None:
            continue  # already caught by _check_body_sections
        cp03 = _extract_h3_section(section, "CP03")
        if cp03 is None:
            continue  # already caught
        if "mt_bucket" not in cp03:
            raise JudgeAuditError(
                f"candidate {cid!r} CP03 body must cite 'mt_bucket' "
                "(see refactor_plan §7.MT)"
            )


def _check_referenced_context(
    fm: dict[str, Any], packet_refs: set[str] | None
) -> None:
    """Every referenced_context entry must be in the packet's declared refs."""
    if packet_refs is None:
        return  # packet reference set not supplied — skip this check
    for c in fm["candidates"]:
        cid = c["candidate_id"]
        refs = c.get("referenced_context") or []
        for r in refs:
            if r not in packet_refs:
                raise JudgeAuditError(
                    f"candidate {cid!r} references {r!r} which is not in the "
                    "judge_packet — LLM cannot cite context outside the packet"
                )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def audit_judge_md(
    path: str | Path,
    packet_refs: set[str] | None = None,
) -> ParsedJudgeMd:
    """Run all six checks on the judge.md at *path*.

    Parameters
    ----------
    path
        Path to the LLM-written ``judge.md``.
    packet_refs
        Optional set of reference strings the pre-pack declared. If
        supplied, ``_check_referenced_context`` enforces that LLM
        citations are a subset; pass ``None`` to skip that specific check.

    Returns
    -------
    ParsedJudgeMd
        The parsed frontmatter + body, for the caller's convenience.

    Raises
    ------
    JudgeAuditError
        On any structural violation. The error message identifies the
        offending candidate and the failing check.
    """
    p = Path(path)
    if not p.exists():
        raise JudgeAuditError(f"judge.md not found at {p}")

    text = p.read_text(encoding="utf-8")
    parsed = parse_judge_md(text)

    _check_frontmatter_schema(parsed.frontmatter)
    _check_verdict_enum(parsed.frontmatter)
    _check_hard_gate_not_overridden(parsed.frontmatter)
    _check_body_sections(parsed.frontmatter, parsed.body)
    _check_cp03_cites_mt_bucket(parsed.frontmatter, parsed.body)
    _check_referenced_context(parsed.frontmatter, packet_refs)

    return parsed
