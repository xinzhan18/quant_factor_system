"""Phase 3 audit — verify LLM-written judge artifacts before Phase 4.

New schema (post-graph-refactor):

* ``batches/batch_N/judge.md`` — batch-level summary (verdict table + observations)
* ``batches/batch_N/candidates/C{id}.md`` — per-candidate 6-CP deep analysis
* ``directions/{direction}.md`` — per-direction hypothesis + threads + narrative
* ``INDEX.md`` — MOC; LLM-maintained upper half must reference the batch

The audit is batch-scoped: runs once after all candidate MDs + judge.md +
direction.md update + INDEX.md update are written. It targets **structure**,
not semantics — "did the LLM reason correctly?" is out of scope.
"Did the LLM follow the protocol?" is in scope.

16 checks:

1. judge.md frontmatter has ``batch_id``, ``candidates`` list, ``batch_summary``
2. every judge frontmatter candidate has verdict ∈ VALID_VERDICTS
3. hard gate immutable — if ``_hints.yaml.per_candidate.{id}.hard_gate.passed`` is
   false, verdict must be ``reject`` in BOTH judge.md and C{id}.md
4. every candidate_id in result.yaml has a ``candidates/C{id}.md`` file
5. each C{id}.md frontmatter has required fields (candidate_id, batch_id,
   direction, expression, verdict, thread_id;
   +key_metrics_short for non-reject; +reject_reason_short for reject).
   ``factor_id`` is NOT required — Phase 4 allocates F{id} monotonically.
6. each C{id}.md body has all required ``## CP{N}`` sections (non-reject: CP01–06;
   reject: CP01 only)
7. non-reject C{id}.md CP03 body contains literal ``mt_bucket``
8. non-reject C{id}.md CP03 body contains literal ``search_adjusted``
9. non-reject C{id}.md CP02 body contains ``[[directions/{direction}`` wikilink
10. each CP{2..6} body cites at least one rubric tier word from that CP's grading
11. all wikilinks in C{id}.md are vault-root relative (no ``../`` prefix)
12. judge.md frontmatter candidate set == union of C{id}.md candidate_ids
13. judge.md body has ``[[batches/{batch_id}/candidates/C{id}]]`` wikilink per candidate
14. direction.md body updated: evidence trail per non-hard-gate-reject candidate,
    Known Failures per reject candidate, Narrative Log entry mentions this batch,
    and all wikilinks are vault-root
15. INDEX.md upper half (above ``<!-- BEGIN AUTO-SECTION -->``) for this direction
    mentions the current batch_id
16. each C{id}.md ``thread_id`` resolves to ``### T{n}`` H3 header in direction.md
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


VALID_VERDICTS: frozenset[str] = frozenset(
    {"admit", "reserve", "reject", "replace"}
)

ALL_CHECKPOINTS: tuple[str, ...] = ("CP01", "CP02", "CP03", "CP04", "CP05", "CP06")

# Rubric tier words (must appear in the corresponding CP body).
RUBRIC_TIER_WORDS: dict[str, tuple[str, ...]] = {
    "CP02": ("aligned", "mixed", "misaligned"),
    "CP03": ("strong", "borderline", "weak"),
    "CP04": ("good", "acceptable", "borderline", "poor"),
    "CP05": ("low", "medium", "high"),
    "CP06": ("stable", "mixed", "unstable"),
}

REQUIRED_JUDGE_CANDIDATE_FIELDS: tuple[str, ...] = (
    "candidate_id",
    "verdict",
)

# factor_name shape: snake_case, 3-40 chars, [a-z0-9_] only. Audited only
# for admit entries — reserve/reject don't allocate F{id} so no name needed.
_FACTOR_NAME_PATTERN: re.Pattern[str] = re.compile(r"^[a-z][a-z0-9_]{2,39}$")

REQUIRED_CANDIDATE_MD_FIELDS: tuple[str, ...] = (
    "candidate_id",
    "batch_id",
    "direction",
    "expression",
    "verdict",
    "thread_id",
)

# INDEX.md is split into an LLM-maintained upper half and a Python auto-generated
# lower half. c15 only inspects the upper half.
AUTO_SECTION_BEGIN: str = "<!-- BEGIN AUTO-SECTION -->"

# direction.md thread headers are H3 with format ``### T001: ...`` or ``### T001 ...``.
_THREAD_HEADER_PATTERN: re.Pattern[str] = re.compile(
    r"^###\s+(T\d+)\b", re.MULTILINE
)


class JudgeAuditError(ValueError):
    """Raised when judge artifacts violate a structural invariant."""


@dataclass
class ParsedDoc:
    frontmatter: dict[str, Any]
    body: str


@dataclass
class ParsedBatch:
    judge: ParsedDoc
    candidates: dict[str, ParsedDoc]  # candidate_id → parsed C{id}.md
    violations: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------


_FRONTMATTER_PATTERN = re.compile(
    r"\A---\s*\n(?P<fm>.*?)\n---\s*\n(?P<body>.*)",
    re.DOTALL,
)

_WIKILINK_PATTERN = re.compile(r"\[\[([^\]|]+?)(?:\|[^\]]*)?\]\]")


def _parse_doc(text: str, what: str) -> ParsedDoc:
    m = _FRONTMATTER_PATTERN.match(text)
    if not m:
        raise JudgeAuditError(f"{what} missing '---' frontmatter fence at start")
    try:
        fm = yaml.safe_load(m.group("fm"))
    except yaml.YAMLError as exc:
        raise JudgeAuditError(f"{what} frontmatter YAML parse error: {exc}") from exc
    if not isinstance(fm, dict):
        raise JudgeAuditError(
            f"{what} frontmatter must be a mapping, got {type(fm).__name__}"
        )
    return ParsedDoc(frontmatter=fm, body=m.group("body"))


def _extract_h2_section(body: str, heading_contains: str) -> str | None:
    """Return the body under ``## ... {heading_contains} ...`` up to next ## or EOF."""
    pattern = re.compile(
        rf"^##\s+[^\n]*\b{re.escape(heading_contains)}\b[^\n]*\n(.*?)(?=^##\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(body)
    return m.group(1) if m else None


# ---------------------------------------------------------------------------
# Individual checks
# ---------------------------------------------------------------------------


def _c1_judge_frontmatter_schema(judge: ParsedDoc) -> list[str]:
    fm = judge.frontmatter
    errs: list[str] = []
    if "batch_id" not in fm:
        errs.append("judge.md frontmatter missing batch_id")
    if not isinstance(fm.get("candidates"), list):
        errs.append("judge.md frontmatter missing candidates list")
    if not isinstance(fm.get("batch_summary"), dict):
        errs.append("judge.md frontmatter missing batch_summary dict")
    for c in fm.get("candidates") or []:
        if not isinstance(c, dict):
            errs.append(f"judge.md candidate entry must be dict, got {type(c).__name__}")
            continue
        for k in REQUIRED_JUDGE_CANDIDATE_FIELDS:
            if k not in c:
                errs.append(
                    f"judge.md candidate {c.get('candidate_id', '?')!r} missing field {k!r}"
                )
        # Admit entries must carry factor_name — Phase 4 writes it into
        # factor.yaml.name + python_factors/F{id}_{name}.py filename.
        if c.get("verdict") == "admit":
            fn = c.get("factor_name")
            cid = c.get("candidate_id", "?")
            if not fn:
                errs.append(
                    f"judge.md candidate {cid!r} has verdict=admit but missing factor_name"
                )
            elif not isinstance(fn, str) or not _FACTOR_NAME_PATTERN.match(fn):
                errs.append(
                    f"judge.md candidate {cid!r} factor_name {fn!r} must be snake_case "
                    f"(3-40 chars, [a-z0-9_], leading letter)"
                )
    return errs


def _c2_verdict_enum(judge: ParsedDoc, candidates: dict[str, ParsedDoc]) -> list[str]:
    errs: list[str] = []
    for c in judge.frontmatter.get("candidates") or []:
        v = c.get("verdict")
        if v not in VALID_VERDICTS:
            errs.append(
                f"judge.md candidate {c.get('candidate_id')!r} invalid verdict {v!r} "
                f"(must be in {sorted(VALID_VERDICTS)})"
            )
    for cid, doc in candidates.items():
        v = doc.frontmatter.get("verdict")
        if v not in VALID_VERDICTS:
            errs.append(
                f"C{cid[1:] if cid.startswith('C') else cid}.md invalid verdict {v!r}"
            )
    return errs


def _c3_hard_gate_not_overridden(
    hints: dict[str, Any],
    judge: ParsedDoc,
    candidates: dict[str, ParsedDoc],
) -> list[str]:
    errs: list[str] = []
    per = hints.get("per_candidate") or {}
    # Index judge frontmatter by candidate_id
    judge_verdicts: dict[str, Any] = {}
    for c in judge.frontmatter.get("candidates") or []:
        cid = c.get("candidate_id")
        if cid:
            judge_verdicts[cid] = c.get("verdict")

    for cid, entry in per.items():
        passed = bool(((entry or {}).get("hard_gate") or {}).get("passed"))
        if passed:
            continue
        # Hard gate failed — verdict must be reject everywhere
        jv = judge_verdicts.get(cid)
        if jv != "reject":
            errs.append(
                f"hard-gate fail on {cid!r} but judge.md verdict={jv!r} (must be 'reject')"
            )
        doc = candidates.get(cid)
        if doc is not None:
            cv = doc.frontmatter.get("verdict")
            if cv != "reject":
                errs.append(
                    f"hard-gate fail on {cid!r} but candidates/{cid}.md verdict={cv!r}"
                )
    return errs


def _c4_candidate_md_completeness(
    result: dict[str, Any],
    candidates: dict[str, ParsedDoc],
) -> list[str]:
    expected = {c.get("candidate_id") for c in result.get("candidates") or [] if c.get("candidate_id")}
    actual = set(candidates.keys())
    missing = expected - actual
    errs = [f"candidates/{cid}.md missing (expected from result.yaml)" for cid in sorted(missing)]
    extra = actual - expected
    errs.extend(
        f"candidates/{cid}.md exists but no such candidate in result.yaml"
        for cid in sorted(extra)
    )
    return errs


def _c5_candidate_md_frontmatter(candidates: dict[str, ParsedDoc]) -> list[str]:
    errs: list[str] = []
    for cid, doc in candidates.items():
        fm = doc.frontmatter
        for k in REQUIRED_CANDIDATE_MD_FIELDS:
            if k not in fm:
                errs.append(f"{cid}.md frontmatter missing {k!r}")
        verdict = fm.get("verdict")
        # ``factor_id`` is intentionally NOT required — Phase 4 allocates F{id}.
        if verdict != "reject" and "key_metrics_short" not in fm:
            errs.append(f"{cid}.md (non-reject) frontmatter missing key_metrics_short")
        if verdict == "reject" and "reject_reason_short" not in fm:
            errs.append(f"{cid}.md (reject) frontmatter missing reject_reason_short")
        # candidate_id field must match filename
        fm_cid = fm.get("candidate_id")
        if fm_cid is not None and fm_cid != cid:
            errs.append(
                f"{cid}.md frontmatter candidate_id={fm_cid!r} mismatches filename"
            )
    return errs


def _c6_candidate_body_sections(candidates: dict[str, ParsedDoc]) -> list[str]:
    errs: list[str] = []
    for cid, doc in candidates.items():
        verdict = doc.frontmatter.get("verdict")
        expected = ("CP01",) if verdict == "reject" else ALL_CHECKPOINTS
        for cp in expected:
            if _extract_h2_section(doc.body, cp) is None:
                errs.append(f"{cid}.md body missing '## {cp}' section")
    return errs


def _c7_cp03_cites_mt_bucket(candidates: dict[str, ParsedDoc]) -> list[str]:
    errs: list[str] = []
    for cid, doc in candidates.items():
        if doc.frontmatter.get("verdict") == "reject":
            continue
        cp03 = _extract_h2_section(doc.body, "CP03")
        if cp03 is None:
            continue  # caught by c6
        if "mt_bucket" not in cp03:
            errs.append(f"{cid}.md CP03 body must cite 'mt_bucket'")
    return errs


def _c8_cp03_cites_search_adjusted(candidates: dict[str, ParsedDoc]) -> list[str]:
    errs: list[str] = []
    for cid, doc in candidates.items():
        if doc.frontmatter.get("verdict") == "reject":
            continue
        cp03 = _extract_h2_section(doc.body, "CP03")
        if cp03 is None:
            continue
        if "search_adjusted" not in cp03:
            errs.append(f"{cid}.md CP03 body must cite 'search_adjusted'")
    return errs


def _c9_cp02_hypothesis_link(candidates: dict[str, ParsedDoc]) -> list[str]:
    errs: list[str] = []
    for cid, doc in candidates.items():
        if doc.frontmatter.get("verdict") == "reject":
            continue
        direction = doc.frontmatter.get("direction")
        if not direction:
            continue  # caught by c5
        cp02 = _extract_h2_section(doc.body, "CP02")
        if cp02 is None:
            continue
        expected = f"[[directions/{direction}"
        if expected not in cp02:
            errs.append(
                f"{cid}.md CP02 body must contain wikilink starting with "
                f"{expected!r}"
            )
    return errs


def _c10_rubric_tier_mention(candidates: dict[str, ParsedDoc]) -> list[str]:
    errs: list[str] = []
    for cid, doc in candidates.items():
        if doc.frontmatter.get("verdict") == "reject":
            continue
        for cp, tiers in RUBRIC_TIER_WORDS.items():
            section = _extract_h2_section(doc.body, cp)
            if section is None:
                continue  # caught by c6
            lowered = section.lower()
            if not any(t in lowered for t in tiers):
                errs.append(
                    f"{cid}.md {cp} body must cite a rubric tier "
                    f"(one of {list(tiers)})"
                )
    return errs


def _c11_wikilink_shape(candidates: dict[str, ParsedDoc]) -> list[str]:
    errs: list[str] = []
    for cid, doc in candidates.items():
        for m in _WIKILINK_PATTERN.finditer(doc.body):
            target = m.group(1).strip()
            if target.startswith("../") or target.startswith("./"):
                errs.append(
                    f"{cid}.md wikilink {target!r} uses relative path; "
                    "use vault-root form (e.g. [[factors/F012]])"
                )
    return errs


def _c12_judge_candidate_union(
    judge: ParsedDoc,
    candidates: dict[str, ParsedDoc],
) -> list[str]:
    judge_ids = {
        c.get("candidate_id")
        for c in judge.frontmatter.get("candidates") or []
        if c.get("candidate_id")
    }
    md_ids = set(candidates.keys())
    errs: list[str] = []
    for cid in sorted(judge_ids - md_ids):
        errs.append(
            f"judge.md frontmatter references {cid!r} but candidates/{cid}.md missing"
        )
    for cid in sorted(md_ids - judge_ids):
        errs.append(
            f"candidates/{cid}.md exists but {cid!r} missing from judge.md frontmatter"
        )
    return errs


def _c13_judge_body_links_candidates(
    judge: ParsedDoc,
    batch_id: str,
) -> list[str]:
    errs: list[str] = []
    for c in judge.frontmatter.get("candidates") or []:
        cid = c.get("candidate_id")
        if not cid:
            continue
        expected = f"[[batches/{batch_id}/candidates/{cid}"
        if expected not in judge.body:
            errs.append(
                f"judge.md body missing wikilink {expected!r} (or |label] variant)"
            )
    return errs


def _c14_direction_md_updated(
    direction_doc: ParsedDoc | None,
    hints: dict[str, Any],
    candidates: dict[str, ParsedDoc],
    batch_id: str,
) -> list[str]:
    """Verify LLM updated ``directions/{direction}.md`` for this batch.

    Enforces:
    * every non-hard-gate-reject candidate has an evidence-trail line
      ``[[batches/{batch_id}/candidates/{cid}`` in the body
    * every reject candidate (hard or LLM) has a ``## Known Failures``
      line that mentions its ``C{id}``
    * body has a ``## Narrative Log`` section that mentions this batch
    * every wikilink in the direction.md body is vault-root (no ``../``)
    """
    errs: list[str] = []
    if direction_doc is None:
        errs.append("direction.md missing or unreadable (c14)")
        return errs

    body = direction_doc.body
    per = hints.get("per_candidate") or {}
    known_failures = _extract_h2_section(body, "Known Failures") or ""
    narrative = _extract_h2_section(body, "Narrative Log") or ""

    for cid, doc in candidates.items():
        verdict = doc.frontmatter.get("verdict")
        hard_passed = bool(((per.get(cid) or {}).get("hard_gate") or {}).get("passed"))

        if verdict == "reject":
            if cid not in known_failures:
                errs.append(
                    f"direction.md '## Known Failures' missing entry for {cid} "
                    f"(reject candidate must be logged)"
                )
            continue

        # Non-reject: evidence trail must reference the candidate
        expected = f"[[batches/{batch_id}/candidates/{cid}"
        if expected not in body:
            errs.append(
                f"direction.md body missing evidence-trail wikilink {expected!r} "
                f"for {cid} (verdict={verdict!r})"
            )
        # Defensive: hard-gate-passed flag sanity (c3 already enforces verdict)
        _ = hard_passed

    if not narrative:
        errs.append("direction.md body missing '## Narrative Log' section")
    elif (
        f"[[batches/{batch_id}/judge" not in narrative
        and batch_id not in narrative
    ):
        errs.append(
            f"direction.md '## Narrative Log' missing reference to {batch_id!r}"
        )

    # Wikilink shape — reuse the same rule as c11 for C{id}.md
    for m in _WIKILINK_PATTERN.finditer(body):
        target = m.group(1).strip()
        if target.startswith("../") or target.startswith("./"):
            errs.append(
                f"direction.md wikilink {target!r} uses relative path; "
                "use vault-root form"
            )

    return errs


def _c15_index_md_references_batch(
    index_doc: ParsedDoc | None,
    direction: str,
    batch_id: str,
) -> list[str]:
    """Verify INDEX.md LLM upper half mentions the current batch for this direction.

    Looks at everything above ``<!-- BEGIN AUTO-SECTION -->`` (or the full
    body if the sentinel is absent). Requires:
    * the direction's ``### [[directions/{direction}`` heading exists
    * the batch_id appears somewhere in that section (the direction's H3
      block — bounded by the next ``###`` or EOF)
    """
    errs: list[str] = []
    if index_doc is None:
        errs.append("INDEX.md missing or unreadable (c15)")
        return errs

    body = index_doc.body
    upper, _, _ = body.partition(AUTO_SECTION_BEGIN)

    direction_marker = f"[[directions/{direction}"
    pattern = re.compile(
        rf"^###\s+[^\n]*{re.escape(direction_marker)}[^\n]*\n(.*?)(?=^###\s+|\Z)",
        re.MULTILINE | re.DOTALL,
    )
    m = pattern.search(upper)
    if not m:
        errs.append(
            f"INDEX.md LLM upper half missing '### {direction_marker}...' heading "
            f"(direction={direction!r})"
        )
        return errs

    section = m.group(1)
    if batch_id not in section:
        errs.append(
            f"INDEX.md direction section for {direction!r} does not mention "
            f"{batch_id!r} in its 1-3 line narrative"
        )
    return errs


def _c16_thread_id_resolves(
    direction_doc: ParsedDoc | None,
    candidates: dict[str, ParsedDoc],
) -> list[str]:
    """Every C{id}.md ``thread_id`` must exist as a ``### T{n}`` in direction.md."""
    errs: list[str] = []
    if direction_doc is None:
        return errs  # c14 already surfaces this

    known_threads = set(_THREAD_HEADER_PATTERN.findall(direction_doc.body))

    for cid, doc in candidates.items():
        tid = doc.frontmatter.get("thread_id")
        if not tid:
            continue  # c5 surfaces missing field
        if tid not in known_threads:
            errs.append(
                f"{cid}.md thread_id={tid!r} has no matching '### {tid}' "
                "header in direction.md"
            )
    return errs


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def audit_batch_judge(
    batch_dir: str | Path,
    result: dict[str, Any],
    hints: dict[str, Any],
    direction_path: str | Path,
    index_path: str | Path,
) -> ParsedBatch:
    """Audit a batch's judge artifacts against all 16 structural rules.

    Collects every violation (does not short-circuit) so the LLM sees the full
    picture on rewrite. Raises :class:`JudgeAuditError` iff any violation found;
    the exception's ``args[0]`` is a newline-joined summary and ``args[1]`` is
    the raw list.

    Parameters
    ----------
    batch_dir
        ``storage/vault/batches/batch_N/`` (or equivalent). Must contain
        ``judge.md`` and ``candidates/`` subdirectory.
    result
        Parsed ``result.yaml`` (list of candidate dicts with ``candidate_id``).
    hints
        Parsed ``_hints.yaml`` (with ``per_candidate.{id}.hard_gate``).
    direction_path
        ``storage/vault/directions/{direction}.md`` for c14 + c16.
    index_path
        ``storage/vault/INDEX.md`` for c15.

    Returns
    -------
    ParsedBatch
        Parsed judge + candidates, for the caller's convenience.
    """
    bdir = Path(batch_dir)
    judge_path = bdir / "judge.md"
    cand_dir = bdir / "candidates"
    batch_id = hints.get("batch_id") or result.get("batch_id") or bdir.name
    direction = hints.get("direction") or ""

    if not judge_path.exists():
        raise JudgeAuditError(f"judge.md not found at {judge_path}")

    judge = _parse_doc(judge_path.read_text(encoding="utf-8"), "judge.md")

    # Parse every candidate md present
    candidates: dict[str, ParsedDoc] = {}
    if cand_dir.is_dir():
        for p in sorted(cand_dir.glob("*.md")):
            cid = p.stem
            candidates[cid] = _parse_doc(
                p.read_text(encoding="utf-8"), f"{cid}.md"
            )

    # Parse direction.md and INDEX.md (graceful on missing)
    dpath = Path(direction_path)
    ipath = Path(index_path)
    direction_doc = (
        _parse_doc(dpath.read_text(encoding="utf-8"), f"directions/{dpath.name}")
        if dpath.exists()
        else None
    )
    index_doc = (
        _parse_doc(ipath.read_text(encoding="utf-8"), "INDEX.md")
        if ipath.exists()
        else None
    )

    violations: list[str] = []
    violations += _c1_judge_frontmatter_schema(judge)
    violations += _c2_verdict_enum(judge, candidates)
    violations += _c3_hard_gate_not_overridden(hints, judge, candidates)
    violations += _c4_candidate_md_completeness(result, candidates)
    violations += _c5_candidate_md_frontmatter(candidates)
    violations += _c6_candidate_body_sections(candidates)
    violations += _c7_cp03_cites_mt_bucket(candidates)
    violations += _c8_cp03_cites_search_adjusted(candidates)
    violations += _c9_cp02_hypothesis_link(candidates)
    violations += _c10_rubric_tier_mention(candidates)
    violations += _c11_wikilink_shape(candidates)
    violations += _c12_judge_candidate_union(judge, candidates)
    violations += _c13_judge_body_links_candidates(judge, batch_id)
    violations += _c14_direction_md_updated(direction_doc, hints, candidates, batch_id)
    violations += _c15_index_md_references_batch(index_doc, direction, batch_id)
    violations += _c16_thread_id_resolves(direction_doc, candidates)

    parsed = ParsedBatch(judge=judge, candidates=candidates, violations=violations)
    if violations:
        summary = f"{len(violations)} audit violation(s):\n" + "\n".join(
            f"  - {v}" for v in violations
        )
        raise JudgeAuditError(summary, violations)
    return parsed
