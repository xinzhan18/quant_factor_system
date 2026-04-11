"""CP01 Hard Gates — Python-only rejection rules.

Five hard-gate checks that run before any LLM judgment. Their defining
property (per refactor_plan §7): **LLM has no authority to override any
of them**. If a candidate fails a hard gate, the only legal verdict is
``reject``; ``checkpoints/audit.py`` enforces this invariant.

The five gates:

1. **compute_error** — Phase 2 recorded an exception on this candidate.
   No downstream reasoning possible.
2. **coverage** — too-low cross-sectional coverage indicates the factor
   is defined on a tiny fraction of the universe and any IC is unreliable.
3. **sign_flip** — train and validation IC have opposite signs (or one
   is effectively zero). Primary validation signal is not representative.
4. **forbidden_field_or_op** — expression uses a blacklisted field /
   operator (e.g. ``$vwap`` is zero in current data). Normally caught by
   Phase 1 DSL whitelist, but we re-check at Phase 3 to be defensive.
5. **sample_policy_violation** — the result was computed under a
   different sample_policy_version than the one currently in
   ``config.yaml``.

Each gate is a pure function taking the ``result.yaml`` candidate dict
plus any relevant config. :func:`evaluate_hard_gates` runs all of them
and returns a structured result for the pre-pack layer to consume.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

# Default thresholds (overridden by config.yaml.thresholds.hard_gates).
DEFAULT_MIN_COVERAGE = 0.80
DEFAULT_FORBIDDEN_FIELDS: frozenset[str] = frozenset({"$vwap"})
DEFAULT_FORBIDDEN_OPERATORS: frozenset[str] = frozenset({"Neg", "SMA"})


@dataclass(frozen=True)
class HardGateResult:
    """Structured output of ``evaluate_hard_gates`` for one candidate."""

    candidate_id: str
    passed: bool
    reasons: list[str]  # empty iff passed


def _has_compute_error(candidate: dict[str, Any]) -> str | None:
    err = candidate.get("compute_error")
    if err:
        return f"compute_error: {err}"
    return None


def _check_coverage(
    candidate: dict[str, Any], min_coverage: float
) -> str | None:
    coverage = candidate.get("coverage")
    if coverage is None:
        return f"coverage missing (min {min_coverage})"
    if coverage < min_coverage:
        return f"coverage {coverage:.3f} < min {min_coverage:.3f}"
    return None


def _check_sign_flip(candidate: dict[str, Any]) -> str | None:
    es = candidate.get("effect_strength")
    if not es:
        return "effect_strength missing"
    train_ic = es.get("train", {}).get("ic_mean")
    val_ic = es.get("validation", {}).get("ic_mean")
    if train_ic is None or val_ic is None:
        return "ic_mean missing"
    # "Effectively zero" threshold — below this we cannot reliably
    # assign a sign. Using 1e-4 matches the legacy execution gate.
    if abs(train_ic) < 1e-4:
        return f"train ic_mean ~0 ({train_ic:.6f}) — sign undefined"
    if abs(val_ic) < 1e-4:
        return f"validation ic_mean ~0 ({val_ic:.6f}) — sign undefined"
    if (train_ic > 0) != (val_ic > 0):
        return (
            f"sign_flip: train {train_ic:+.6f} vs validation {val_ic:+.6f}"
        )
    return None


def _check_forbidden(
    candidate: dict[str, Any],
    forbidden_fields: frozenset[str],
    forbidden_ops: frozenset[str],
) -> str | None:
    expr = candidate.get("expression") or ""
    # Field check: grep for exact ``$name`` tokens (``$vwap`` catches
    # only ``$vwap``, not ``$vwap_close_ratio`` since we look for word
    # boundaries — but to keep the rule conservative we use simple
    # substring containment and require fields to include the $).
    for field in forbidden_fields:
        if field in expr:
            return f"forbidden_field: {field} in expression"
    for op in forbidden_ops:
        # Operators appear as ``OpName(`` in Qlib DSL
        if f"{op}(" in expr:
            return f"forbidden_operator: {op}(...) in expression"
    return None


def _check_sample_policy(
    result: dict[str, Any], current_version: str
) -> str | None:
    seen = result.get("sample_policy_version")
    if seen is None:
        return "sample_policy_version missing from result.yaml"
    if seen != current_version:
        return (
            f"sample_policy_violation: result computed with {seen!r}, "
            f"current config {current_version!r}"
        )
    return None


def evaluate_hard_gates(
    result: dict[str, Any],
    current_sample_policy_version: str,
    min_coverage: float = DEFAULT_MIN_COVERAGE,
    forbidden_fields: frozenset[str] = DEFAULT_FORBIDDEN_FIELDS,
    forbidden_operators: frozenset[str] = DEFAULT_FORBIDDEN_OPERATORS,
) -> list[HardGateResult]:
    """Run all hard gates on every candidate in a ``result.yaml`` dict.

    Parameters
    ----------
    result
        Parsed ``result.yaml`` (top-level dict with ``candidates`` list).
    current_sample_policy_version
        The value currently in ``config.yaml.sample_policy.sample_policy_version``.
        Pass this in explicitly so the gate is a pure function.
    min_coverage
        Minimum acceptable coverage. Below → reject.
    forbidden_fields, forbidden_operators
        Blacklists to check the expression against.

    Returns
    -------
    list[HardGateResult]
        One per candidate, in the order they appear in ``result["candidates"]``.
    """
    # Sample-policy check is batch-level — same for every candidate in
    # this batch. Compute once and reuse.
    sample_policy_fail = _check_sample_policy(result, current_sample_policy_version)

    results: list[HardGateResult] = []
    for c in result.get("candidates", []):
        cid = c.get("candidate_id", "?")
        reasons: list[str] = []

        # Ordered: cheapest / most definitive checks first
        if (r := _has_compute_error(c)) is not None:
            reasons.append(r)
        # If compute_error is set, further checks may be meaningless, but we
        # still run them so the reasons list is complete for the LLM packet.
        if sample_policy_fail is not None:
            reasons.append(sample_policy_fail)
        if (r := _check_forbidden(c, forbidden_fields, forbidden_operators)) is not None:
            reasons.append(r)
        # coverage and sign_flip require effect_strength, skip if compute_error
        if c.get("compute_error") is None:
            if (r := _check_coverage(c, min_coverage)) is not None:
                reasons.append(r)
            if (r := _check_sign_flip(c)) is not None:
                reasons.append(r)

        results.append(
            HardGateResult(
                candidate_id=cid,
                passed=len(reasons) == 0,
                reasons=reasons,
            )
        )

    return results
