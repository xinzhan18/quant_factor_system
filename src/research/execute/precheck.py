"""Pre-execution checks for DSL and Python factor candidates.

The precheck layer is the first gate in the research execute pipeline.
It rejects candidates that cannot possibly produce valid signals before
any expensive computation runs.

Design reference: ``docs/refacor_logic/research_execute.md`` section 6 Step 1.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Operator / field whitelists (source of truth for DSL validation)
# ---------------------------------------------------------------------------
DSL_OPERATOR_WHITELIST: Set[str] = {
    # Qlib built-in
    "Add", "Sub", "Mul", "Div", "Abs", "Log", "Power", "Sign",
    "Not", "And", "Or", "Eq", "Ne", "Gt", "Ge", "Lt", "Le",
    "Mean", "Std", "Var", "Skew", "Kurt", "Med", "Mad", "Sum", "Prod",
    "Count", "Quantile", "Min", "Max",
    "Ref", "Delta", "IdxMax", "IdxMin", "Correlation", "Corr", "Cov",
    "Rank", "Mask",
    "EMA", "WMA",
    "Slope", "Rsquare", "Resi",
    "If", "IfElse", "Greater", "Less",
    # Custom operators
    "SignedPower", "Tanh", "Exp", "Sigmoid", "Softmax",
    "Scale", "Zscore", "Winsorize",
    "TsDecay", "TsMomentum", "TsAutoCorr", "RealizedVol", "TsEntropy",
    "TsMax", "TsMin", "TsRank", "TsSkew", "TsKurt",
    "CsRank", "CsZscore", "CsDemean",
    "AmihudIlliq", "HHI",
}

DSL_FIELD_WHITELIST: Set[str] = {
    "$open", "$high", "$low", "$close", "$volume", "$amount",
    "$pe_ratio", "$pb_ratio", "$ps_ratio",
    "$market_cap", "$circ_market_cap", "$turnover_rate",
}

# $vwap is known to be zero -- forbid its use
FORBIDDEN_FIELDS: Set[str] = {"$vwap"}

# Operators known to be unregistered at runtime
UNAVAILABLE_OPERATORS: Set[str] = {"Neg", "SMA"}

# Patterns that are empirically known to produce bad factors
FORBIDDEN_PATTERNS: List[re.Pattern] = [
    re.compile(r"\$vwap", re.IGNORECASE),
]

MAX_EXPRESSION_DEPTH = 10



# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------
@dataclass
class PrecheckResult:
    """Outcome of a precheck step."""

    status: str  # "passed" | "failed"
    reason_codes: List[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.status == "passed"

    def to_dict(self) -> Dict[str, Any]:
        return {"status": self.status, "reason_codes": list(self.reason_codes)}


# ---------------------------------------------------------------------------
# DSL precheck
# ---------------------------------------------------------------------------
class DSLPrecheck:
    """Validate a Qlib DSL expression before execution."""

    def __init__(
        self,
        operator_whitelist: Optional[Set[str]] = None,
        field_whitelist: Optional[Set[str]] = None,
        max_depth: int = MAX_EXPRESSION_DEPTH,
        forbidden_patterns: Optional[List[re.Pattern]] = None,
    ):
        self._operators = operator_whitelist or DSL_OPERATOR_WHITELIST
        self._fields = field_whitelist or DSL_FIELD_WHITELIST
        self._max_depth = max_depth
        self._forbidden = forbidden_patterns if forbidden_patterns is not None else FORBIDDEN_PATTERNS

    def check(self, expression: str) -> PrecheckResult:
        """Run all DSL precheck rules and return a combined result."""
        reason_codes: List[str] = []

        # --- parser_check: non-empty and balanced parens ---
        if not expression or not expression.strip():
            return PrecheckResult(status="failed", reason_codes=["empty_expression"])
        expr = expression.strip()

        depth = 0
        max_seen = 0
        for ch in expr:
            if ch == "(":
                depth += 1
                max_seen = max(max_seen, depth)
            elif ch == ")":
                depth -= 1
            if depth < 0:
                reason_codes.append("unbalanced_parentheses")
                break
        if depth > 0:
            reason_codes.append("unbalanced_parentheses")
        if reason_codes:
            return PrecheckResult(status="failed", reason_codes=reason_codes)

        # --- operator_whitelist_check ---
        operators_used = set(re.findall(r"([A-Z][a-zA-Z]*)\s*\(", expr))
        for op in operators_used:
            if op in UNAVAILABLE_OPERATORS:
                reason_codes.append(f"unavailable_operator:{op}")
            elif op not in self._operators:
                reason_codes.append(f"unknown_operator:{op}")

        # --- field_whitelist_check ---
        fields_used = set(re.findall(r"\$[a-zA-Z_][a-zA-Z0-9_]*", expr))
        for f in fields_used:
            if f in FORBIDDEN_FIELDS:
                reason_codes.append(f"forbidden_field:{f}")
            elif f not in self._fields:
                reason_codes.append(f"unknown_field:{f}")

        # --- expression_depth_check ---
        if max_seen > self._max_depth:
            reason_codes.append(f"expression_too_deep:{max_seen}")

        # --- constant_factor_check (heuristic: no field references) ---
        if not fields_used:
            reason_codes.append("constant_expression")

        # --- forbidden_pattern_check ---
        for pat in self._forbidden:
            if pat.search(expr):
                reason_codes.append(f"forbidden_pattern:{pat.pattern}")

        status = "failed" if reason_codes else "passed"
        return PrecheckResult(status=status, reason_codes=reason_codes)


# ---------------------------------------------------------------------------
# Python precheck (file-based)
# ---------------------------------------------------------------------------
class PythonPrecheck:
    """Validate a Python factor .py file before execution."""

    def check(self, module_path: str) -> PrecheckResult:
        """Check that the module file exists and is readable."""
        import os
        if not module_path or not module_path.strip():
            return PrecheckResult(status="failed", reason_codes=["empty_module_path"])
        if not os.path.isfile(module_path):
            return PrecheckResult(status="failed", reason_codes=[f"module_not_found:{module_path}"])
        return PrecheckResult(status="passed")


# ---------------------------------------------------------------------------
# Convenience dispatcher
# ---------------------------------------------------------------------------
def run_precheck(candidate: Dict[str, Any]) -> PrecheckResult:
    """Dispatch to the appropriate precheck based on ``source_type``."""
    source_type = candidate.get("source_type", "dsl")

    if source_type == "dsl":
        expr = candidate.get("expression", "")
        return DSLPrecheck().check(expr)
    elif source_type == "python":
        module_path = candidate.get("module_path", "")
        return PythonPrecheck().check(module_path)
    else:
        return PrecheckResult(
            status="failed",
            reason_codes=[f"unknown_source_type:{source_type}"],
        )
