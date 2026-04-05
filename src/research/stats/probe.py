"""Lightweight garbage filter: pass / reserve / fail.

Pure vectorized functions. No I/O, no Qlib.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from core.factor_stats import daily_cross_sectional_ic


def run_probe(
    factor_values: pd.DataFrame,
    forward_returns: pd.DataFrame,
    train_splits: List[Tuple[str, str]],
    forbidden_patterns: Optional[List[str]] = None,
    expression: Optional[str] = None,
    min_obs: int = 30,
    valid_ratio_threshold: float = 0.30,
    max_complexity: int = 10,
) -> Dict[str, Any]:
    """Run a lightweight probe to classify a candidate as pass / reserve / fail.

    Checks (in order):
      1. computable   -- factor_values is non-empty
      2. valid_ratio  -- fraction of non-NaN values > threshold
      3. variance_ok  -- not near-constant
      4. forbidden_hit -- expression matches a forbidden pattern
      5. complexity_ok -- expression depth within limit
      6. signal_strength_hint -- IC magnitude bucket
      7. split_consistency_hint -- same-sign IC across train splits
      8. duplicate_risk_hint -- placeholder (always ``unknown``)

    Args:
        factor_values: Flat DataFrame [time, symbol, value].
        forward_returns: Flat DataFrame [time, symbol, value].
        train_splits: List of (start, end) date-string tuples for IC checks.
        forbidden_patterns: Optional regex patterns to reject.
        expression: Optional DSL expression string for pattern / complexity.
        min_obs: Minimum cross-sectional observations per day.
        valid_ratio_threshold: Minimum non-NaN ratio.
        max_complexity: Maximum allowed nesting depth.

    Returns:
        Dict with per-check results and overall ``verdict``
        (pass / reserve / fail).
    """
    reasons: List[str] = []

    # 1. Computable
    computable = not factor_values.empty and len(factor_values) > 0
    if not computable:
        return _build_result(verdict="fail", reasons=["not_computable"])

    # 2. Valid ratio
    total = len(factor_values)
    valid_count = factor_values["value"].notna().sum()
    valid_ratio = float(valid_count / total) if total > 0 else 0.0
    if valid_ratio < valid_ratio_threshold:
        reasons.append("valid_ratio_too_low")

    # 3. Variance
    vals = factor_values["value"].dropna().values
    if len(vals) < 10:
        variance_ok = False
        reasons.append("insufficient_data")
    else:
        variance_ok = bool(np.std(vals) > 1e-10)
        if not variance_ok:
            reasons.append("near_constant")

    # 4. Forbidden pattern
    forbidden_hit = False
    if expression and forbidden_patterns:
        for pat in forbidden_patterns:
            if re.search(pat, expression):
                forbidden_hit = True
                reasons.append(f"forbidden_pattern:{pat}")
                break

    # 5. Complexity
    complexity_ok = True
    if expression:
        depth = _nesting_depth(expression)
        if depth > max_complexity:
            complexity_ok = False
            reasons.append("expression_too_complex")

    # Early fail: hard checks
    if not computable or valid_ratio < valid_ratio_threshold or not variance_ok or forbidden_hit:
        return _build_result(
            computable=computable, valid_ratio=valid_ratio,
            variance_ok=variance_ok, forbidden_hit=forbidden_hit,
            complexity_ok=complexity_ok, verdict="fail", reasons=reasons,
        )

    # 6. Signal strength hint (IC across all train data combined)
    all_ic_values: List[float] = []
    split_signs: List[float] = []
    for start, end in train_splits:
        fv = factor_values.loc[
            (factor_values["time"] >= pd.Timestamp(start))
            & (factor_values["time"] <= pd.Timestamp(end))
        ]
        fr = forward_returns.loc[
            (forward_returns["time"] >= pd.Timestamp(start))
            & (forward_returns["time"] <= pd.Timestamp(end))
        ]
        ic = daily_cross_sectional_ic(fv, fr, min_obs=min_obs)
        if not ic.empty:
            split_mean = float(ic.mean())
            all_ic_values.extend(ic.values.tolist())
            split_signs.append(np.sign(split_mean))

    if not all_ic_values:
        return _build_result(
            computable=True, valid_ratio=valid_ratio,
            variance_ok=variance_ok, forbidden_hit=forbidden_hit,
            complexity_ok=complexity_ok, verdict="fail",
            reasons=reasons + ["no_ic_computed"],
        )

    overall_ic = float(np.mean(all_ic_values))
    abs_ic = abs(overall_ic)
    if abs_ic >= 0.02:
        strength = "strong"
    elif abs_ic >= 0.01:
        strength = "medium"
    elif abs_ic >= 0.005:
        strength = "weak"
    else:
        strength = "none"

    # 7. Split consistency hint
    if len(split_signs) < 2:
        consistency = "weak"
    else:
        dominant = np.sign(overall_ic)
        frac_same = float(np.mean(np.array(split_signs) == dominant))
        if frac_same >= 0.75:
            consistency = "good"
        elif frac_same >= 0.50:
            consistency = "acceptable"
        elif frac_same > 0.0:
            consistency = "weak"
        else:
            consistency = "broken"

    # Verdict
    if strength == "none":
        verdict = "fail"
    elif strength == "weak" or consistency in ("broken", "weak"):
        verdict = "reserve"
    else:
        verdict = "pass"

    if not complexity_ok:
        verdict = "reserve" if verdict == "pass" else verdict

    return _build_result(
        computable=True, valid_ratio=valid_ratio,
        variance_ok=variance_ok, forbidden_hit=forbidden_hit,
        complexity_ok=complexity_ok,
        signal_strength_hint=strength, split_consistency_hint=consistency,
        verdict=verdict, reasons=reasons, overall_ic=round(overall_ic, 6),
    )


def _build_result(
    *,
    computable: bool = False,
    valid_ratio: float = 0.0,
    variance_ok: bool = False,
    forbidden_hit: bool = False,
    complexity_ok: bool = True,
    signal_strength_hint: str = "none",
    split_consistency_hint: str = "broken",
    verdict: str = "fail",
    reasons: Optional[List[str]] = None,
    overall_ic: Optional[float] = None,
) -> Dict[str, Any]:
    """Build a probe result dict with consistent keys."""
    result: Dict[str, Any] = {
        "computable": computable,
        "valid_ratio": round(valid_ratio, 4),
        "variance_ok": variance_ok,
        "forbidden_hit": forbidden_hit,
        "complexity_ok": complexity_ok,
        "signal_strength_hint": signal_strength_hint,
        "split_consistency_hint": split_consistency_hint,
        "duplicate_risk_hint": "unknown",
        "verdict": verdict,
        "reasons": reasons or [],
    }
    if overall_ic is not None:
        result["overall_ic"] = overall_ic
    return result


def _nesting_depth(expression: str) -> int:
    """Count maximum parenthesis nesting depth in an expression."""
    depth = 0
    max_depth = 0
    for ch in expression:
        if ch == "(":
            depth += 1
            max_depth = max(max_depth, depth)
        elif ch == ")":
            depth -= 1
    return max_depth
