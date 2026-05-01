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
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from research.compute.python_runner import (
    PythonFactorContractError,
    load_python_candidate,
)
from research.storage.paths import StoragePaths
from research.storage.state import StateFile
from research.storage.yaml_io import load_yaml, save_yaml

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
        # Price / volume
        "$open", "$high", "$low", "$close", "$volume", "$amount",
        # Microstructure
        "$turnover_rate", "$num_trades",
        # Valuation (point-in-time)
        "$pe_ratio", "$pb_ratio", "$ps_ratio", "$pcf_ratio",
        "$market_cap", "$circ_market_cap",
        # Profitability (TTM)
        "$return_on_equity_ttm", "$return_on_asset_ttm",
        "$return_on_invested_capital_ttm",
        "$gross_profit_margin_ttm", "$operating_profit_margin_ttm",
        # Solvency (TTM)
        "$debt_to_asset_ratio_ttm", "$debt_to_equity_ratio_ttm",
        "$current_ratio_ttm",
        # Efficiency (TTM)
        "$total_asset_turnover_ttm", "$inventory_turnover_ttm",
        "$account_receivable_turnover_rate_ttm",
        # Growth (TTM)
        "$operating_revenue_growth_ratio_ttm", "$net_profit_growth_ratio_ttm",
        "$net_asset_growth_ratio_ttm",
        # Per-share / Yield (TTM)
        "$eps_ttm", "$book_value_per_share_ttm",
        "$operating_cash_flow_per_share_ttm", "$dividend_yield_ttm",
        # Valuation (TTM)
        "$pcf_ratio_total_ttm", "$peg_ratio_ttm",
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
    round_counter: int = 0,
    sample_policy: dict[str, Any] | None = None,
    direction_md_ref: str | None = None,
    active_threads_referenced: list[str] | None = None,
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
        # Pass-through fields from LLM
        for key in ("rationale", "parent_batch", "parent_candidate_id", "transformation"):
            if c.get(key):
                entry[key] = c[key]
        manifest_candidates.append(entry)

    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    manifest = {
        "batch_id": batch_id,
        "round": int(round_counter),
        "direction": direction,
        "direction_md_ref": direction_md_ref
            or f"vault/directions/{direction}.md",
        "batch_goal": batch_goal.strip() if batch_goal else "",
        "active_threads_referenced": list(active_threads_referenced or []),
        "sample_policy": dict(sample_policy) if sample_policy else {},
        "created_at": now_iso,
        "frozen_at": now_iso,
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


# ---------------------------------------------------------------------------
# High-level Phase 1 orchestrator — the "one helper to rule them all"
# ---------------------------------------------------------------------------


def collect_existing_canonicals(paths: StoragePaths) -> list[str]:
    """Scan ``vault/factors/F*.yaml`` for ``canonical`` fields (dedup source)."""
    canonicals: list[str] = []
    fdir = paths.factors_dir
    if not fdir.exists():
        return canonicals
    for yml in sorted(fdir.glob("F*.yaml")):
        data = load_yaml(yml) or {}
        canon = data.get("canonical")
        if canon:
            canonicals.append(str(canon))
    return canonicals


def _config_sample_policy(paths: StoragePaths) -> dict[str, Any]:
    """Pull the ``sample_policy`` block out of config.yaml (safe defaults)."""
    cfg = load_yaml(paths.config_file) or {}
    sp = cfg.get("sample_policy") or {}
    # Normalize to the manifest-friendly key names.
    tr = sp.get("train_range") or [None, None]
    vl = sp.get("validation_range") or [None, None]
    return {
        "train_start": str(tr[0]) if tr[0] else None,
        "train_end": str(tr[1]) if tr[1] else None,
        "test_start": str(vl[0]) if vl[0] else None,
        "test_end": str(vl[1]) if vl[1] else None,
    }


def start_phase1(
    direction: str,
    batch_goal: str,
    candidates: list[dict[str, Any]],
    *,
    paths: StoragePaths | None = None,
    active_threads_referenced: list[str] | None = None,
    strict: bool = True,
) -> FreezeReport:
    """Phase 1 one-shot orchestrator: **begin batch → freeze manifest → refresh INDEX**.

    Callers (including the LLM in ``/factor-idea``) only supply content
    (direction / goal / candidates / thread refs). Everything else —
    allocating the next batch_id, writing the full schema, transitioning
    state, regenerating INDEX.md's lower half — is handled here.

    Parameters
    ----------
    direction
        Direction slug. Must match ``vault/directions/{slug}.md``.
    batch_goal
        ≥ 30 char goal string.
    candidates
        Same dict shape accepted by :func:`freeze_manifest`.
    paths
        Optional explicit :class:`StoragePaths`; defaults to ``StoragePaths()``.
    active_threads_referenced
        Optional list like ``["T001", "T002"]`` for the manifest.
    strict
        Forwarded to :func:`freeze_manifest`.

    Returns
    -------
    FreezeReport
        The underlying freeze report. Extra work (state + INDEX) completed
        only when the report's ``all_passed`` is True.

    Raises
    ------
    Phase1FreezeError
        From :func:`freeze_manifest` when any candidate fails validation.
    research.storage.state.InvalidPhaseTransition
        When the state is not idle — caller must first ``finish_batch`` or
        ``state reset``.
    """
    paths = paths or StoragePaths()
    # Ensure the vault / batches tree exists so first-time users don't trip.
    paths.batches_dir.mkdir(parents=True, exist_ok=True)
    paths.directions_dir.mkdir(parents=True, exist_ok=True)
    paths.factors_dir.mkdir(parents=True, exist_ok=True)

    direction_md = paths.direction_file(direction)
    if not direction_md.exists():
        raise FileNotFoundError(
            f"direction file missing: {direction_md} — create it before "
            "calling start_phase1"
        )

    state = StateFile(paths.state_file)
    batch_id = state.next_batch_id()

    # Transition idle → designed. Raises InvalidPhaseTransition if not idle.
    state.begin_batch(batch_id)

    batch_dir = paths.batch_dir(batch_id)
    batch_dir.mkdir(parents=True, exist_ok=True)

    try:
        report = freeze_manifest(
            batch_id=batch_id,
            direction=direction,
            batch_goal=batch_goal,
            candidates=candidates,
            existing_canonicals=collect_existing_canonicals(paths),
            manifest_path=paths.batch_manifest_file(batch_id),
            round_counter=state.read().round,
            sample_policy=_config_sample_policy(paths),
            direction_md_ref=f"vault/directions/{direction}.md",
            active_threads_referenced=active_threads_referenced or [],
            strict=strict,
        )
    except Exception:
        # Roll back the state transition so the caller can retry cleanly.
        state.update(current_batch=None, current_batch_phase=None)
        raise

    # Refresh INDEX lower half (best-effort — don't fail Phase 1 on it)
    try:
        from research.memory.index_refresher import refresh_index
        refresh_index(paths, round_counter=state.read().round)
    except Exception as exc:  # pragma: no cover
        import sys
        print(f"[start_phase1] INDEX refresh failed: {exc}", file=sys.stderr)

    return report
