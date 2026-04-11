"""Phase 1 START + DESIGN orchestrator.

Produces a frozen ``batches/batch_{id}/manifest.yaml`` from a set of
proposed candidates. Five responsibilities (refactor_plan §5):

1. **DSL whitelist validation** — operator and field must be in the
   hardcoded whitelists (single source of truth, same lists the legacy
   ``execute/precheck.py`` used). Bonus checks: balanced parens,
   max expression depth, non-constant (contains at least one ``$field``),
   no forbidden fields / ops.
2. **Python candidate validation** — re-uses
   ``research.compute.python_runner`` AST whitelist + module contract
   (no duplication).
3. **Canonicalization + duplicate detection** (Q4) — normalize
   whitespace and apply commutativity for ``Add/Mul`` to catch
   ``Mul(A, B) == Mul(B, A)``, then reject any expression whose
   canonical form matches an already-admitted factor.
4. **batch_goal audit** — non-empty, ≥ 30 chars (so LLM can't submit
   "test" as the goal).
5. **Atomic manifest freeze** — write ``manifest.yaml`` via
   ``storage.yaml_io.save_yaml`` (temp-file + replace).

Order matters: candidates that fail any check are collected with
reasons and never reach the manifest. If any single candidate fails,
the entire batch fails (``Phase1FreezeError``) — fail-fast rather than
silently dropping candidates the LLM thinks are in the batch.
"""

from __future__ import annotations

import ast
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from research.compute.python_runner import (
    PythonFactorContractError,
    load_python_candidate,
)
from research.storage.yaml_io import save_yaml

# ---------------------------------------------------------------------------
# Whitelists — single source of truth, copied from legacy precheck.py
# (legacy file stays on disk until P7 cleanup; we don't import it since
# execute/ is not in the deprecation guard list but copying keeps P3
# standalone.)
# ---------------------------------------------------------------------------

DSL_OPERATOR_WHITELIST: frozenset[str] = frozenset(
    {
        # Qlib built-in math / logic
        "Add", "Sub", "Mul", "Div", "Abs", "Log", "Power", "Sign",
        "Not", "And", "Or", "Eq", "Ne", "Gt", "Ge", "Lt", "Le",
        # Rolling statistics
        "Mean", "Std", "Var", "Skew", "Kurt", "Med", "Mad", "Sum", "Prod",
        "Count", "Quantile", "Min", "Max",
        # Time-series ops
        "Ref", "Delta", "IdxMax", "IdxMin", "Correlation", "Corr", "Cov",
        "Rank", "Mask",
        "EMA", "WMA",
        # Regression helpers
        "Slope", "Rsquare", "Resi",
        # Conditionals
        "If", "IfElse", "Greater", "Less",
        # Custom registered operators
        "SignedPower", "Tanh", "Exp", "Sigmoid", "Softmax",
        "Scale", "Zscore", "Winsorize",
        "TsDecay", "TsMomentum", "TsAutoCorr", "RealizedVol", "TsEntropy",
        "TsMax", "TsMin", "TsRank", "TsSkew", "TsKurt",
        "CsRank", "CsZscore", "CsDemean",
        "AmihudIlliq", "HHI",
    }
)

DSL_FIELD_WHITELIST: frozenset[str] = frozenset(
    {
        "$open", "$high", "$low", "$close", "$volume", "$amount",
        "$pe_ratio", "$pb_ratio", "$ps_ratio",
        "$market_cap", "$circ_market_cap", "$turnover_rate",
    }
)

FORBIDDEN_FIELDS: frozenset[str] = frozenset({"$vwap"})
UNAVAILABLE_OPERATORS: frozenset[str] = frozenset({"Neg", "SMA"})

MAX_EXPRESSION_DEPTH = 10
MIN_BATCH_GOAL_LENGTH = 30
# Operators whose argument order doesn't matter for equivalence checking.
# Add/Mul are the two canonical commutative Qlib ops.
COMMUTATIVE_OPERATORS: frozenset[str] = frozenset({"Add", "Mul"})


# ---------------------------------------------------------------------------
# Errors + result types
# ---------------------------------------------------------------------------


class Phase1FreezeError(ValueError):
    """Raised when at least one candidate fails validation."""


@dataclass
class CandidateReport:
    """Per-candidate validation outcome."""

    candidate_id: str
    source_type: str
    expression: str  # for python candidates, file path
    passed: bool
    reasons: list[str] = field(default_factory=list)
    canonical: str | None = None  # only for DSL expressions


@dataclass
class FreezeReport:
    """Top-level outcome of freeze_manifest."""

    batch_id: str
    direction: str
    candidates: list[CandidateReport]
    manifest_path: Path | None

    @property
    def all_passed(self) -> bool:
        return all(c.passed for c in self.candidates)


# ---------------------------------------------------------------------------
# DSL validation
# ---------------------------------------------------------------------------

_OPERATOR_PATTERN = re.compile(r"([A-Z][a-zA-Z]*)\s*\(")
_FIELD_PATTERN = re.compile(r"\$[a-zA-Z_][a-zA-Z0-9_]*")


def validate_dsl_expression(expression: str) -> list[str]:
    """Return a list of rejection reasons; empty list means the expression passed."""
    reasons: list[str] = []

    if not expression or not expression.strip():
        return ["empty_expression"]
    expr = expression.strip()

    # --- balanced parentheses + max depth ---
    depth = 0
    max_depth = 0
    for ch in expr:
        if ch == "(":
            depth += 1
            max_depth = max(max_depth, depth)
        elif ch == ")":
            depth -= 1
            if depth < 0:
                reasons.append("unbalanced_parentheses")
                break
    if depth > 0:
        reasons.append("unbalanced_parentheses")
    if reasons:
        # Don't run the other checks on a syntactically broken expression
        return reasons

    if max_depth > MAX_EXPRESSION_DEPTH:
        reasons.append(f"expression_too_deep:{max_depth}")

    # --- operator whitelist ---
    ops_used = set(_OPERATOR_PATTERN.findall(expr))
    for op in ops_used:
        if op in UNAVAILABLE_OPERATORS:
            reasons.append(f"unavailable_operator:{op}")
        elif op not in DSL_OPERATOR_WHITELIST:
            reasons.append(f"unknown_operator:{op}")

    # --- field whitelist ---
    fields_used = set(_FIELD_PATTERN.findall(expr))
    for f in fields_used:
        if f in FORBIDDEN_FIELDS:
            reasons.append(f"forbidden_field:{f}")
        elif f not in DSL_FIELD_WHITELIST:
            reasons.append(f"unknown_field:{f}")

    # --- constant expression (no field references) ---
    if not fields_used:
        reasons.append("constant_expression")

    return reasons


# ---------------------------------------------------------------------------
# Canonicalization — for duplicate detection under commutativity
# ---------------------------------------------------------------------------


def _tokenize(expression: str) -> list[str]:
    """Coarse tokenizer: split on the set of DSL delimiters."""
    # Normalize whitespace first
    expr = re.sub(r"\s+", "", expression)
    # Tokenize on () ,
    tokens: list[str] = []
    buf = ""
    for ch in expr:
        if ch in "(),":
            if buf:
                tokens.append(buf)
                buf = ""
            tokens.append(ch)
        else:
            buf += ch
    if buf:
        tokens.append(buf)
    return tokens


def canonicalize_expression(expression: str) -> str:
    """Return a canonical form of *expression* invariant under commutativity.

    The canonicalizer:

    1. Strips whitespace.
    2. Parses the expression tree via simple tokenizer (Qlib DSL is
       prefix-function with commas).
    3. For each call whose operator is in ``COMMUTATIVE_OPERATORS``,
       sorts its argument list lexicographically by canonical form.
    4. Re-serializes.

    This catches ``Mul(A, B) == Mul(B, A)`` but not algebraic
    equivalences like ``Add(A, Mul(B, 2)) == Add(Mul(2, B), A)``
    via distributivity — that's out of scope for a cheap check.
    """
    tokens = _tokenize(expression)

    pos = 0

    def parse() -> str:
        nonlocal pos
        if pos >= len(tokens):
            return ""
        tok = tokens[pos]
        pos += 1
        # Look ahead: is this a function call?
        if pos < len(tokens) and tokens[pos] == "(":
            pos += 1  # consume '('
            args: list[str] = []
            if pos < len(tokens) and tokens[pos] != ")":
                args.append(parse())
                while pos < len(tokens) and tokens[pos] == ",":
                    pos += 1  # consume ','
                    args.append(parse())
            if pos < len(tokens) and tokens[pos] == ")":
                pos += 1  # consume ')'
            # If operator is commutative, sort args canonically
            if tok in COMMUTATIVE_OPERATORS:
                args = sorted(args)
            return f"{tok}({','.join(args)})"
        # Bare atom (field, literal)
        return tok

    result = parse()
    return result


def check_duplicate_expression(
    canonical: str,
    existing_canonicals: Iterable[str],
) -> bool:
    """Return True iff *canonical* already exists in *existing_canonicals*."""
    return canonical in set(existing_canonicals)


# ---------------------------------------------------------------------------
# Python candidate validation
# ---------------------------------------------------------------------------


def validate_python_candidate(path: str | Path) -> list[str]:
    """Return rejection reasons for a Python candidate file; empty = passed."""
    try:
        load_python_candidate(path)
    except PythonFactorContractError as exc:
        return [f"python_contract:{exc}"]
    except Exception as exc:
        return [f"python_load_error:{type(exc).__name__}:{exc}"]
    return []


# ---------------------------------------------------------------------------
# batch_goal audit
# ---------------------------------------------------------------------------


def validate_batch_goal(goal: str | None) -> list[str]:
    """Check the batch_goal string is present and long enough."""
    if goal is None or not goal.strip():
        return ["empty_batch_goal"]
    if len(goal.strip()) < MIN_BATCH_GOAL_LENGTH:
        return [
            f"batch_goal_too_short:{len(goal.strip())}<{MIN_BATCH_GOAL_LENGTH}"
        ]
    return []


# ---------------------------------------------------------------------------
# Manifest freeze entry point
# ---------------------------------------------------------------------------


def freeze_manifest(
    batch_id: str,
    direction: str,
    batch_goal: str,
    candidates: list[dict[str, Any]],
    existing_canonicals: Iterable[str],
    manifest_path: str | Path,
    *,
    sample_policy_version: str = "v3",
    strict: bool = True,
) -> FreezeReport:
    """Validate every candidate and atomically write ``manifest.yaml``.

    Parameters
    ----------
    batch_id
        Frozen batch identifier (e.g. ``batch_104``).
    direction
        Target direction slug — must match a direction md on disk, but
        the filesystem check happens at a higher layer (mine orchestrator).
    batch_goal
        Human-readable goal string for the batch. ≥ 30 chars.
    candidates
        List of candidate dicts. Each must have ``candidate_id``,
        ``source_type`` (``dsl`` | ``python``), and one of:

        * ``expression`` (for DSL)
        * ``path`` (for Python, a filesystem path to a ``.py`` module)
    existing_canonicals
        Iterable of canonical-form strings of already-admitted factors.
        Used for dedup against the library.
    manifest_path
        Where to write the frozen manifest.
    sample_policy_version
        Embedded in the manifest so Phase 2 can cross-check.
    strict
        If True (default), any candidate failure or batch_goal failure
        aborts the freeze via :class:`Phase1FreezeError`. If False,
        returns a report with ``passed=False`` entries but still writes
        the manifest with only the passing candidates (useful for
        testing / preview modes).

    Returns
    -------
    FreezeReport
        Detailed outcome per candidate, plus the written manifest path
        (``None`` if strict and batch_goal failed before any candidate
        was checked).

    Raises
    ------
    Phase1FreezeError
        In strict mode, if any validation failed. The report is
        attached to ``exc.args[1]`` for inspection.
    """
    reports: list[CandidateReport] = []

    # 1. batch_goal
    goal_reasons = validate_batch_goal(batch_goal)

    # 2. per-candidate validation + canonicalization + dedup
    seen_in_batch: set[str] = set()
    existing_set = set(existing_canonicals)

    for c in candidates:
        cid = c.get("candidate_id", "?")
        source_type = c.get("source_type", "dsl")
        expr_for_display = c.get("expression") or c.get("path") or ""
        reasons: list[str] = []
        canonical: str | None = None

        if source_type == "dsl":
            expr = c.get("expression") or ""
            reasons.extend(validate_dsl_expression(expr))
            if not reasons:
                canonical = canonicalize_expression(expr)
                if canonical in existing_set:
                    reasons.append("duplicate_of_existing_factor")
                elif canonical in seen_in_batch:
                    reasons.append("duplicate_within_batch")
                else:
                    seen_in_batch.add(canonical)
        elif source_type == "python":
            path = c.get("path")
            if not path:
                reasons.append("missing_python_path")
            else:
                reasons.extend(validate_python_candidate(path))
        else:
            reasons.append(f"unknown_source_type:{source_type}")

        reports.append(
            CandidateReport(
                candidate_id=cid,
                source_type=source_type,
                expression=expr_for_display,
                passed=len(reasons) == 0,
                reasons=reasons,
                canonical=canonical,
            )
        )

    any_failed = bool(goal_reasons) or any(not r.passed for r in reports)

    if strict and any_failed:
        report = FreezeReport(
            batch_id=batch_id,
            direction=direction,
            candidates=reports,
            manifest_path=None,
        )
        msg_parts = []
        if goal_reasons:
            msg_parts.append(f"batch_goal: {goal_reasons}")
        failed = [r for r in reports if not r.passed]
        if failed:
            msg_parts.append(
                f"{len(failed)}/{len(reports)} candidates failed: "
                + ", ".join(
                    f"{r.candidate_id}={r.reasons}" for r in failed[:5]
                )
            )
        raise Phase1FreezeError(" | ".join(msg_parts), report)

    # 3. Build the manifest dict from passing candidates
    manifest_candidates = []
    for r, c in zip(reports, candidates):
        if not r.passed:
            continue
        entry = {
            "candidate_id": r.candidate_id,
            "source_type": r.source_type,
        }
        if r.source_type == "dsl":
            entry["expression"] = c.get("expression")
            entry["canonical"] = r.canonical
        else:
            entry["path"] = c.get("path")
        manifest_candidates.append(entry)

    manifest = {
        "batch_id": batch_id,
        "direction": direction,
        "batch_goal": batch_goal.strip() if batch_goal else "",
        "sample_policy_version": sample_policy_version,
        "candidates": manifest_candidates,
    }

    path = Path(manifest_path)
    save_yaml(path, manifest)

    return FreezeReport(
        batch_id=batch_id,
        direction=direction,
        candidates=reports,
        manifest_path=path,
    )
