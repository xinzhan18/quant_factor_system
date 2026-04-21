"""Tests for checkpoints.audit — 16 structural checks on batch judge artifacts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
import yaml

from research.checkpoints.audit import (
    ALL_CHECKPOINTS,
    JudgeAuditError,
    audit_batch_judge,
)


# ---------------------------------------------------------------------------
# Fixtures — build a fully-passing batch, then mutate one thing at a time.
# ---------------------------------------------------------------------------


def _rubric_tier(cp: str) -> str:
    return {
        "CP02": "aligned",
        "CP03": "strong",
        "CP04": "acceptable",
        "CP05": "low",
        "CP06": "stable",
    }[cp]


def _good_candidate_md(
    cid: str = "C001",
    batch_id: str = "batch_042",
    direction: str = "fp_divergence",
    verdict: str = "admit",
) -> str:
    fm: dict[str, Any] = {
        "candidate_id": cid,
        "batch_id": batch_id,
        "direction": direction,
        "expression": "Std($close, 20)",
        "verdict": verdict,
        "thread_id": "T001",
    }
    # factor_id intentionally NOT required — Phase 4 allocates.
    if verdict != "reject":
        fm["key_metrics_short"] = "ICIR=0.338 ls_t=3.89"
    else:
        fm["reject_reason_short"] = "coverage 0.65 < 0.80"
    fm_text = yaml.dump(fm, sort_keys=False, allow_unicode=True)

    if verdict == "reject":
        body = "\n".join([
            "## CP01",
            "coverage 0.65 < 0.80 → reject.",
        ])
    else:
        body_lines: list[str] = []
        for cp in ALL_CHECKPOINTS:
            body_lines.append(f"## {cp}")
            if cp == "CP01":
                body_lines.append("all gates passed.")
            elif cp == "CP02":
                body_lines.append(
                    f"Mechanism: volatility signal. "
                    f"[[directions/{direction}#Hypothesis]] — aligned."
                )
            elif cp == "CP03":
                body_lines.append(
                    "ICIR=0.338 mt_bucket=medium search_adjusted=0.41 → strong."
                )
            else:
                body_lines.append(f"{cp} reasoning here — {_rubric_tier(cp)}.")
            body_lines.append("")
        body = "\n".join(body_lines)

    return f"---\n{fm_text.strip()}\n---\n\n{body}\n"


def _good_judge_md(
    batch_id: str = "batch_042",
    direction: str = "fp_divergence",
    candidate_ids: list[str] | None = None,
    verdicts: dict[str, str] | None = None,
) -> str:
    ids = candidate_ids or ["C001"]
    verdicts = verdicts or {cid: "admit" for cid in ids}

    def _entry(cid: str) -> dict[str, Any]:
        v = verdicts.get(cid, "admit")
        e: dict[str, Any] = {"candidate_id": cid, "verdict": v}
        if v == "admit":
            # Audit c1 now requires factor_name for admit entries.
            e["factor_name"] = f"test_factor_{cid.lower()}"
        return e

    fm: dict[str, Any] = {
        "batch_id": batch_id,
        "direction": direction,
        "candidates": [_entry(cid) for cid in ids],
        "batch_summary": {
            "total": len(ids),
            "admit": sum(1 for v in verdicts.values() if v == "admit"),
            "reserve": sum(1 for v in verdicts.values() if v == "reserve"),
            "reject": sum(1 for v in verdicts.values() if v == "reject"),
        },
    }
    fm_text = yaml.dump(fm, sort_keys=False, allow_unicode=True)
    body_lines = [
        f"# {batch_id} Judge Summary",
        "",
        "## 候选一览",
        "",
        "| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |",
        "|---|---|---|---|---|---|",
    ]
    for cid in ids:
        v = verdicts.get(cid, "admit")
        body_lines.append(
            f"| {cid} | {v} | 🟢·🟢·🟢·🟢·🟢 | ICIR=0.34 | fixture row | "
            f"[[batches/{batch_id}/candidates/{cid}]] |"
        )
    # Cross-candidate required when >1 candidate; include unconditionally
    # so single-candidate batches remain template-complete.
    body_lines += [
        "",
        "## 跨候选对比",
        "",
        "- fixture cross-candidate synthesis.",
        "",
        "## Thread 进展",
        "",
        "- T001: fixture thread progress.",
        "",
        "## 方向级反思",
        "",
        "fixture direction-level reflection.",
    ]
    return f"---\n{fm_text.strip()}\n---\n\n" + "\n".join(body_lines) + "\n"


def _good_direction_md(
    direction: str = "fp_divergence",
    batch_id: str = "batch_042",
    candidates: dict[str, str] | None = None,
    expressions: dict[str, str] | None = None,
    reject_reasons: dict[str, str] | None = None,
) -> str:
    """Build a direction.md that satisfies c14 + c16 for the given candidates.

    ``candidates``: ``{candidate_id: verdict}`` (both hard-gate reject and LLM
    reject go into Known Failures; everything else into Threads evidence trail).
    """
    if candidates is None:
        candidates = {"C001": "admit"}
    if expressions is None:
        expressions = {cid: "Std($close, 20)" for cid in candidates}
    if reject_reasons is None:
        reject_reasons = {
            cid: "coverage 0.65 < 0.80"
            for cid, v in candidates.items()
            if v == "reject"
        }

    fm: dict[str, Any] = {
        "direction_tag": direction,
        "status": "exploring",
        "priority": "medium",
        "rounds": 1,
        "admits": 0,
        "members": [],
    }
    fm_text = yaml.dump(fm, sort_keys=False, allow_unicode=True)

    evidence_lines = [
        f"- [[batches/{batch_id}/candidates/{cid}|{batch_id} {cid}]]: {v}"
        for cid, v in candidates.items()
        if v != "reject"
    ]
    known_failures_lines = [
        f"- {cid} `{expressions[cid]}` — {reject_reasons.get(cid, 'gate fail')}"
        for cid, v in candidates.items()
        if v == "reject"
    ]

    body = f"""# {direction}

## Hypothesis

Test hypothesis.

## Threads

### T001: Example thread [◉ ACTIVE]
**Question**: test
**Evidence trail**:
{chr(10).join(evidence_lines) if evidence_lines else '(none)'}

## Known Failures

{chr(10).join(known_failures_lines) if known_failures_lines else '(none)'}

## Narrative Log

### 2026-04-18 [[batches/{batch_id}/judge|{batch_id}]]
Round summary.
"""
    return f"---\n{fm_text.strip()}\n---\n\n{body}"


def _good_index_md(
    direction: str = "fp_divergence",
    batch_id: str = "batch_042",
) -> str:
    return f"""---
generated_at: '2026-04-18T00:00:00Z'
round: 42
---

# INDEX

## 活跃方向

### [[directions/{direction}|Example Direction]] `exploring` `medium`
Last run: {batch_id}. Keep probing.

<!-- BEGIN AUTO-SECTION -->

(auto)

<!-- END AUTO-SECTION -->
"""


def _write_batch(
    tmp_path: Path,
    batch_id: str = "batch_042",
    direction: str = "fp_divergence",
    candidate_ids: list[str] | None = None,
    candidate_mds: dict[str, str] | None = None,
    judge_md: str | None = None,
) -> Path:
    ids = candidate_ids or ["C001"]
    bdir = tmp_path / batch_id
    bdir.mkdir()
    cdir = bdir / "candidates"
    cdir.mkdir()

    for cid in ids:
        md = (candidate_mds or {}).get(cid) or _good_candidate_md(
            cid=cid, batch_id=batch_id, direction=direction
        )
        (cdir / f"{cid}.md").write_text(md, encoding="utf-8")

    if judge_md is None:
        judge_md = _good_judge_md(batch_id, direction, ids)
    (bdir / "judge.md").write_text(judge_md, encoding="utf-8")
    return bdir


def _write_vault_files(
    tmp_path: Path,
    direction: str = "fp_divergence",
    batch_id: str = "batch_042",
    direction_md: str | None = None,
    index_md: str | None = None,
    candidate_verdicts: dict[str, str] | None = None,
) -> tuple[Path, Path]:
    """Create direction.md + INDEX.md siblings at tmp_path for c14/c15."""
    dpath = tmp_path / f"{direction}.md"
    ipath = tmp_path / "INDEX.md"
    dpath.write_text(
        direction_md
        or _good_direction_md(
            direction=direction,
            batch_id=batch_id,
            candidates=candidate_verdicts or {"C001": "admit"},
        ),
        encoding="utf-8",
    )
    ipath.write_text(
        index_md or _good_index_md(direction=direction, batch_id=batch_id),
        encoding="utf-8",
    )
    return dpath, ipath


def _result_for(ids: list[str]) -> dict[str, Any]:
    return {"candidates": [{"candidate_id": cid} for cid in ids]}


def _hints_for(
    ids: list[str],
    failed: set[str] | None = None,
    direction: str = "fp_divergence",
    batch_id: str = "batch_042",
) -> dict[str, Any]:
    failed = failed or set()
    per: dict[str, Any] = {}
    for cid in ids:
        if cid in failed:
            per[cid] = {"hard_gate": {"passed": False, "reasons": ["coverage x"]}}
        else:
            per[cid] = {
                "hard_gate": {"passed": True, "reasons": []},
                "mt_budget": {
                    "score": 0.4,
                    "bucket": "medium",
                    "terms": {"family": 0.4, "direction": 0.4, "exposure": 0.4},
                    "search_adjusted": {
                        "raw": 0.5,
                        "adjusted": 0.4,
                        "bucket": "medium",
                    },
                },
            }
    return {"batch_id": batch_id, "direction": direction, "per_candidate": per}


def _run_audit(
    tmp_path: Path,
    bdir: Path,
    ids: list[str],
    hints: dict[str, Any] | None = None,
    direction: str = "fp_divergence",
    batch_id: str = "batch_042",
    candidate_verdicts: dict[str, str] | None = None,
    direction_md: str | None = None,
    index_md: str | None = None,
):
    """Wire up all four inputs and invoke audit_batch_judge."""
    hints = hints if hints is not None else _hints_for(ids, direction=direction, batch_id=batch_id)
    dpath, ipath = _write_vault_files(
        tmp_path,
        direction=direction,
        batch_id=batch_id,
        direction_md=direction_md,
        index_md=index_md,
        candidate_verdicts=candidate_verdicts,
    )
    return audit_batch_judge(
        bdir,
        _result_for(ids),
        hints,
        direction_path=dpath,
        index_path=ipath,
    )


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


class TestHappyPath:
    def test_clean_batch_passes(self, tmp_path: Path) -> None:
        bdir = _write_batch(tmp_path, candidate_ids=["C001"])
        parsed = _run_audit(tmp_path, bdir, ["C001"])
        assert parsed.violations == []
        assert "C001" in parsed.candidates

    def test_multiple_candidates_pass(self, tmp_path: Path) -> None:
        ids = ["C001", "C002", "C003"]
        bdir = _write_batch(tmp_path, candidate_ids=ids)
        parsed = _run_audit(
            tmp_path,
            bdir,
            ids,
            candidate_verdicts={cid: "admit" for cid in ids},
        )
        assert parsed.violations == []

    def test_mixed_verdicts_pass(self, tmp_path: Path) -> None:
        ids = ["C001", "C002"]
        verdicts = {"C001": "admit", "C002": "reject"}
        mds = {
            "C001": _good_candidate_md(cid="C001", verdict="admit"),
            "C002": _good_candidate_md(cid="C002", verdict="reject"),
        }
        judge_md = _good_judge_md(candidate_ids=ids, verdicts=verdicts)
        bdir = _write_batch(
            tmp_path,
            candidate_ids=ids,
            candidate_mds=mds,
            judge_md=judge_md,
        )
        hints = _hints_for(["C001"])
        hints["per_candidate"]["C002"] = {
            "hard_gate": {"passed": False, "reasons": ["coverage 0.65 < 0.80"]}
        }
        parsed = _run_audit(
            tmp_path,
            bdir,
            ids,
            hints=hints,
            candidate_verdicts=verdicts,
        )
        assert parsed.violations == []


# ---------------------------------------------------------------------------
# Check 1 — judge.md frontmatter schema
# ---------------------------------------------------------------------------


class TestCheck1JudgeFrontmatter:
    def test_missing_batch_id_fails(self, tmp_path: Path) -> None:
        broken = _good_judge_md().replace("batch_id: batch_042\n", "", 1)
        bdir = _write_batch(tmp_path, judge_md=broken)
        with pytest.raises(JudgeAuditError, match="batch_id"):
            _run_audit(tmp_path, bdir, ["C001"])

    def test_missing_candidates_list_fails(self, tmp_path: Path) -> None:
        fm = {
            "batch_id": "batch_042",
            "batch_summary": {"total": 0, "admit": 0, "reserve": 0, "reject": 0},
        }
        body = "# no candidates"
        bad = "---\n" + yaml.dump(fm, sort_keys=False).strip() + "\n---\n\n" + body
        bdir = _write_batch(tmp_path, judge_md=bad)
        with pytest.raises(JudgeAuditError, match="candidates list"):
            _run_audit(tmp_path, bdir, ["C001"])

    def test_missing_batch_summary_fails(self, tmp_path: Path) -> None:
        fm = {
            "batch_id": "batch_042",
            "candidates": [{"candidate_id": "C001", "verdict": "admit"}],
        }
        bad = (
            "---\n"
            + yaml.dump(fm, sort_keys=False).strip()
            + "\n---\n\n"
            + "- [[batches/batch_042/candidates/C001|C001]]: admit\n"
        )
        bdir = _write_batch(tmp_path, judge_md=bad)
        with pytest.raises(JudgeAuditError, match="batch_summary"):
            _run_audit(tmp_path, bdir, ["C001"])


# ---------------------------------------------------------------------------
# Check 2 — verdict enum
# ---------------------------------------------------------------------------


class TestCheck2VerdictEnum:
    def test_invalid_judge_verdict_fails(self, tmp_path: Path) -> None:
        bad_judge = _good_judge_md().replace("verdict: admit", "verdict: maybe")
        bdir = _write_batch(tmp_path, judge_md=bad_judge)
        with pytest.raises(JudgeAuditError, match="invalid verdict"):
            _run_audit(tmp_path, bdir, ["C001"])


# ---------------------------------------------------------------------------
# Check 3 — hard gate immutable
# ---------------------------------------------------------------------------


class TestCheck3HardGateImmutable:
    def test_hard_gate_fail_with_admit_verdict_in_judge_fails(
        self, tmp_path: Path
    ) -> None:
        bdir = _write_batch(tmp_path, candidate_ids=["C001"])
        hints = _hints_for(["C001"], failed={"C001"})
        with pytest.raises(JudgeAuditError, match="hard-gate fail"):
            _run_audit(tmp_path, bdir, ["C001"], hints=hints)


# ---------------------------------------------------------------------------
# Check 4 — candidate md completeness
# ---------------------------------------------------------------------------


class TestCheck4Completeness:
    def test_missing_candidate_md_fails(self, tmp_path: Path) -> None:
        bdir = _write_batch(tmp_path, candidate_ids=["C001"])
        with pytest.raises(JudgeAuditError, match="C002.md missing"):
            _run_audit(tmp_path, bdir, ["C001", "C002"])

    def test_extra_candidate_md_fails(self, tmp_path: Path) -> None:
        bdir = _write_batch(tmp_path, candidate_ids=["C001", "C002"])
        with pytest.raises(JudgeAuditError, match="no such candidate"):
            _run_audit(tmp_path, bdir, ["C001"])


# ---------------------------------------------------------------------------
# Check 5 — candidate md frontmatter
# ---------------------------------------------------------------------------


class TestCheck5CandidateFrontmatter:
    def test_admit_without_factor_id_passes(self, tmp_path: Path) -> None:
        """factor_id is now optional — Phase 4 allocates it, so LLM's
        admit without factor_id must pass c5."""
        bdir = _write_batch(tmp_path, candidate_ids=["C001"])
        parsed = _run_audit(tmp_path, bdir, ["C001"])
        assert parsed.violations == []

    def test_missing_required_field_fails(self, tmp_path: Path) -> None:
        bad = _good_candidate_md().replace("thread_id: T001\n", "")
        bdir = _write_batch(
            tmp_path,
            candidate_ids=["C001"],
            candidate_mds={"C001": bad},
        )
        with pytest.raises(JudgeAuditError, match="thread_id"):
            _run_audit(tmp_path, bdir, ["C001"])

    def test_filename_mismatch_fails(self, tmp_path: Path) -> None:
        bad = _good_candidate_md(cid="C999")  # frontmatter says C999
        bdir = _write_batch(
            tmp_path,
            candidate_ids=["C001"],
            candidate_mds={"C001": bad},  # but filename is C001.md
        )
        with pytest.raises(JudgeAuditError, match="mismatches filename"):
            _run_audit(tmp_path, bdir, ["C001"])


# ---------------------------------------------------------------------------
# Check 6 — body sections
# ---------------------------------------------------------------------------


class TestCheck6BodySections:
    def test_missing_cp03_fails(self, tmp_path: Path) -> None:
        bad = _good_candidate_md()
        bad = bad.replace("## CP03\n", "## CPXX\n")
        bdir = _write_batch(tmp_path, candidate_ids=["C001"], candidate_mds={"C001": bad})
        with pytest.raises(JudgeAuditError, match="CP03"):
            _run_audit(tmp_path, bdir, ["C001"])


# ---------------------------------------------------------------------------
# Check 7 & 8 — CP03 citations
# ---------------------------------------------------------------------------


class TestCheck7And8CP03Citations:
    def test_missing_mt_bucket_fails(self, tmp_path: Path) -> None:
        bad = _good_candidate_md().replace("mt_bucket", "xxxxxxxxx")
        bdir = _write_batch(tmp_path, candidate_ids=["C001"], candidate_mds={"C001": bad})
        with pytest.raises(JudgeAuditError, match="mt_bucket"):
            _run_audit(tmp_path, bdir, ["C001"])

    def test_missing_search_adjusted_fails(self, tmp_path: Path) -> None:
        bad = _good_candidate_md().replace("search_adjusted", "yyyy")
        bdir = _write_batch(tmp_path, candidate_ids=["C001"], candidate_mds={"C001": bad})
        with pytest.raises(JudgeAuditError, match="search_adjusted"):
            _run_audit(tmp_path, bdir, ["C001"])


# ---------------------------------------------------------------------------
# Check 9 — CP02 hypothesis link
# ---------------------------------------------------------------------------


class TestCheck9Cp02HypothesisLink:
    def test_missing_hypothesis_wikilink_fails(self, tmp_path: Path) -> None:
        bad = _good_candidate_md().replace(
            "[[directions/fp_divergence#Hypothesis]]",
            "fp_divergence hypothesis",
        )
        bdir = _write_batch(tmp_path, candidate_ids=["C001"], candidate_mds={"C001": bad})
        with pytest.raises(JudgeAuditError, match="directions/fp_divergence"):
            _run_audit(tmp_path, bdir, ["C001"])


# ---------------------------------------------------------------------------
# Check 10 — rubric tier mention
# ---------------------------------------------------------------------------


class TestCheck10RubricTier:
    def test_cp06_missing_tier_word_fails(self, tmp_path: Path) -> None:
        base = _good_candidate_md()
        bad = base.replace(
            "CP06 reasoning here — stable.",
            "CP06 reasoning here — fine.",
        )
        bdir = _write_batch(tmp_path, candidate_ids=["C001"], candidate_mds={"C001": bad})
        with pytest.raises(JudgeAuditError, match="CP06"):
            _run_audit(tmp_path, bdir, ["C001"])


# ---------------------------------------------------------------------------
# Check 11 — wikilink shape
# ---------------------------------------------------------------------------


class TestCheck11WikilinkShape:
    def test_relative_wikilink_fails(self, tmp_path: Path) -> None:
        bad = _good_candidate_md().replace(
            "[[directions/fp_divergence#Hypothesis]]",
            "[[../directions/fp_divergence#Hypothesis]]",
        )
        bdir = _write_batch(tmp_path, candidate_ids=["C001"], candidate_mds={"C001": bad})
        with pytest.raises(JudgeAuditError, match="relative path"):
            _run_audit(tmp_path, bdir, ["C001"])


# ---------------------------------------------------------------------------
# Check 12 — judge candidate union
# ---------------------------------------------------------------------------


class TestCheck12JudgeCandidateUnion:
    def test_judge_lists_candidate_without_md_fails(self, tmp_path: Path) -> None:
        # judge.md lists C001 and C002, but only C001.md exists on disk
        bdir = _write_batch(tmp_path, candidate_ids=["C001"])
        judge_md = _good_judge_md(candidate_ids=["C001", "C002"])
        (bdir / "judge.md").write_text(judge_md, encoding="utf-8")
        with pytest.raises(JudgeAuditError, match="C002.md missing"):
            _run_audit(tmp_path, bdir, ["C001", "C002"])


# ---------------------------------------------------------------------------
# Check 13 — judge body wikilinks
# ---------------------------------------------------------------------------


class TestCheck13JudgeBodyLinks:
    def test_missing_wikilink_in_body_fails(self, tmp_path: Path) -> None:
        fm = {
            "batch_id": "batch_042",
            "direction": "fp_divergence",
            "candidates": [{"candidate_id": "C001", "verdict": "admit"}],
            "batch_summary": {"total": 1, "admit": 1, "reserve": 0, "reject": 0},
        }
        judge_md = (
            "---\n"
            + yaml.dump(fm, sort_keys=False).strip()
            + "\n---\n\n# Judge\n\n(no links here)\n"
        )
        bdir = _write_batch(tmp_path, judge_md=judge_md)
        with pytest.raises(JudgeAuditError, match="missing wikilink"):
            _run_audit(tmp_path, bdir, ["C001"])


# ---------------------------------------------------------------------------
# Check 14 — direction.md body updated
# ---------------------------------------------------------------------------


class TestCheck14DirectionMdUpdated:
    def test_missing_evidence_trail_fails(self, tmp_path: Path) -> None:
        bdir = _write_batch(tmp_path, candidate_ids=["C001"])
        # direction.md has no evidence trail for C001
        dmd = _good_direction_md(candidates={})  # empty candidates → no trail
        with pytest.raises(JudgeAuditError, match="evidence-trail"):
            _run_audit(tmp_path, bdir, ["C001"], direction_md=dmd)

    def test_missing_known_failure_for_reject_fails(self, tmp_path: Path) -> None:
        ids = ["C001"]
        md = _good_candidate_md(cid="C001", verdict="reject")
        judge_md = _good_judge_md(candidate_ids=ids, verdicts={"C001": "reject"})
        bdir = _write_batch(
            tmp_path,
            candidate_ids=ids,
            candidate_mds={"C001": md},
            judge_md=judge_md,
        )
        hints = _hints_for(ids, failed={"C001"})
        # direction.md has no Known Failures entry for C001
        dmd = _good_direction_md(candidates={})
        with pytest.raises(JudgeAuditError, match="Known Failures"):
            _run_audit(
                tmp_path,
                bdir,
                ids,
                hints=hints,
                direction_md=dmd,
                candidate_verdicts={"C001": "reject"},
            )

    def test_missing_narrative_log_reference_fails(self, tmp_path: Path) -> None:
        bdir = _write_batch(tmp_path, candidate_ids=["C001"])
        # direction.md narrative log mentions a different batch only
        bad = _good_direction_md(batch_id="batch_999")
        # Fix evidence trail wikilink to still point to batch_042 so c14 evidence
        # passes and only narrative check fails
        bad = bad.replace("batch_999/candidates", "batch_042/candidates")
        bad = bad.replace("|batch_999 C001", "|batch_042 C001")
        with pytest.raises(JudgeAuditError, match="Narrative Log"):
            _run_audit(tmp_path, bdir, ["C001"], direction_md=bad)

    def test_relative_wikilink_in_direction_fails(self, tmp_path: Path) -> None:
        bdir = _write_batch(tmp_path, candidate_ids=["C001"])
        bad = _good_direction_md().replace(
            "[[batches/batch_042/candidates/C001|",
            "[[../batches/batch_042/candidates/C001|",
        )
        with pytest.raises(JudgeAuditError, match="relative path"):
            _run_audit(tmp_path, bdir, ["C001"], direction_md=bad)


# ---------------------------------------------------------------------------
# Check 15 — INDEX.md direction section mentions batch
# ---------------------------------------------------------------------------


class TestCheck15IndexMdUpdated:
    def test_missing_direction_heading_fails(self, tmp_path: Path) -> None:
        bdir = _write_batch(tmp_path, candidate_ids=["C001"])
        # INDEX.md has no direction heading at all
        bad_index = """---
generated_at: '2026-04-18T00:00:00Z'
---

# INDEX

(no direction headings)

<!-- BEGIN AUTO-SECTION -->
(auto)
<!-- END AUTO-SECTION -->
"""
        with pytest.raises(JudgeAuditError, match="missing '### \\[\\[directions"):
            _run_audit(tmp_path, bdir, ["C001"], index_md=bad_index)

    def test_direction_section_missing_batch_id_fails(self, tmp_path: Path) -> None:
        bdir = _write_batch(tmp_path, candidate_ids=["C001"])
        bad_index = _good_index_md().replace(
            "Last run: batch_042.", "Last run: batch_xxx."
        )
        with pytest.raises(JudgeAuditError, match="does not mention 'batch_042'"):
            _run_audit(tmp_path, bdir, ["C001"], index_md=bad_index)

    def test_batch_reference_only_in_auto_section_fails(self, tmp_path: Path) -> None:
        """Batch mention in the Python auto section doesn't count for c15."""
        bdir = _write_batch(tmp_path, candidate_ids=["C001"])
        bad_index = """---
generated_at: '2026-04-18T00:00:00Z'
---

# INDEX

### [[directions/fp_divergence|Example]] `exploring` `medium`
No recent updates.

<!-- BEGIN AUTO-SECTION -->
Last batch: batch_042
<!-- END AUTO-SECTION -->
"""
        with pytest.raises(JudgeAuditError, match="does not mention 'batch_042'"):
            _run_audit(tmp_path, bdir, ["C001"], index_md=bad_index)


# ---------------------------------------------------------------------------
# Check 16 — thread_id resolves in direction.md
# ---------------------------------------------------------------------------


class TestCheck16ThreadIdResolves:
    def test_unknown_thread_id_fails(self, tmp_path: Path) -> None:
        bad_md = _good_candidate_md().replace("thread_id: T001", "thread_id: T999")
        bdir = _write_batch(
            tmp_path,
            candidate_ids=["C001"],
            candidate_mds={"C001": bad_md},
        )
        with pytest.raises(JudgeAuditError, match="thread_id='T999'"):
            _run_audit(tmp_path, bdir, ["C001"])

    def test_existing_thread_id_passes(self, tmp_path: Path) -> None:
        bdir = _write_batch(tmp_path, candidate_ids=["C001"])
        parsed = _run_audit(tmp_path, bdir, ["C001"])
        assert parsed.violations == []


# ---------------------------------------------------------------------------
# Multi-violation accumulation
# ---------------------------------------------------------------------------


class TestMultiViolation:
    def test_multiple_violations_reported_together(self, tmp_path: Path) -> None:
        # Break two things at once: missing search_adjusted AND bad wikilink
        bad = _good_candidate_md().replace(
            "search_adjusted", "yyy"
        ).replace(
            "[[directions/fp_divergence#Hypothesis]]",
            "[[../directions/fp_divergence#Hypothesis]]",
        )
        bdir = _write_batch(tmp_path, candidate_ids=["C001"], candidate_mds={"C001": bad})
        with pytest.raises(JudgeAuditError) as exc_info:
            _run_audit(tmp_path, bdir, ["C001"])
        violations = exc_info.value.args[1]
        assert len(violations) >= 2


# ---------------------------------------------------------------------------
# c17-c19 — judge template discipline (Bug 7)
# ---------------------------------------------------------------------------


class TestCheck17ThreadProgressSection:
    def test_missing_thread_progress_fails_multi_candidate(
        self, tmp_path: Path
    ) -> None:
        bad_judge = _good_judge_md(candidate_ids=["C001", "C002"]).replace(
            "## Thread 进展\n", "## Skipped\n"
        )
        bdir = _write_batch(
            tmp_path, candidate_ids=["C001", "C002"], judge_md=bad_judge
        )
        with pytest.raises(JudgeAuditError, match="Thread 进展"):
            _run_audit(tmp_path, bdir, ["C001", "C002"])

    def test_single_candidate_exempt(self, tmp_path: Path) -> None:
        # Build a judge with no Thread 进展 section AND only 1 candidate
        judge = _good_judge_md(candidate_ids=["C001"]).replace(
            "## Thread 进展\n\n- T001: fixture thread progress.\n", ""
        )
        bdir = _write_batch(tmp_path, candidate_ids=["C001"], judge_md=judge)
        # This must still fail c18 (no 跨候选 allowed here since 1 candidate,
        # but c19 still applies for table columns). It should NOT fail c17.
        try:
            _run_audit(tmp_path, bdir, ["C001"])
        except JudgeAuditError as exc:
            errs = exc.args[1]
            assert not any("Thread 进展" in v for v in errs)


class TestCheck18CrossCandidateSection:
    def test_missing_cross_candidate_fails_when_multi(self, tmp_path: Path) -> None:
        bad = _good_judge_md(candidate_ids=["C001", "C002"]).replace(
            "## 跨候选对比\n", "## Skipped\n"
        )
        bdir = _write_batch(
            tmp_path, candidate_ids=["C001", "C002"], judge_md=bad
        )
        with pytest.raises(JudgeAuditError, match="跨候选对比"):
            _run_audit(tmp_path, bdir, ["C001", "C002"])

    def test_single_candidate_exempt(self, tmp_path: Path) -> None:
        # Fixture already omits cross-candidate section if we strip it
        judge = _good_judge_md(candidate_ids=["C001"]).replace(
            "## 跨候选对比\n\n- fixture cross-candidate synthesis.\n", ""
        )
        bdir = _write_batch(tmp_path, candidate_ids=["C001"], judge_md=judge)
        try:
            _run_audit(tmp_path, bdir, ["C001"])
        except JudgeAuditError as exc:
            errs = exc.args[1]
            assert not any("跨候选对比" in v for v in errs)


class TestCheck19CandidateTableColumns:
    def test_missing_dangwei_column_fails(self, tmp_path: Path) -> None:
        judge = _good_judge_md(candidate_ids=["C001"]).replace(
            "| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |",
            "| ID | Verdict | Key | Detail |",
        )
        bdir = _write_batch(tmp_path, candidate_ids=["C001"], judge_md=judge)
        with pytest.raises(JudgeAuditError, match="档位"):
            _run_audit(tmp_path, bdir, ["C001"])

    def test_missing_fansi_column_fails(self, tmp_path: Path) -> None:
        judge = _good_judge_md(candidate_ids=["C001"]).replace(
            "| ID | Verdict | 档位 (CP2·3·4·5·6) | Key Metric | 反思 | Detail |",
            "| ID | Verdict | 档位 | Key | Detail |",
        )
        bdir = _write_batch(tmp_path, candidate_ids=["C001"], judge_md=judge)
        with pytest.raises(JudgeAuditError, match="反思"):
            _run_audit(tmp_path, bdir, ["C001"])

    def test_missing_candidate_table_section_fails(self, tmp_path: Path) -> None:
        judge = _good_judge_md(candidate_ids=["C001"]).replace(
            "## 候选一览", "## Skipped"
        )
        bdir = _write_batch(tmp_path, candidate_ids=["C001"], judge_md=judge)
        with pytest.raises(JudgeAuditError, match="候选一览"):
            _run_audit(tmp_path, bdir, ["C001"])
