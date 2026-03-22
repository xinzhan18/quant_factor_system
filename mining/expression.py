"""Expression validation for Qlib factor expressions."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Set

from .config import MiningConfig


@dataclass
class ValidationResult:
    """Result of expression validation."""
    valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


KNOWN_OPERATORS = {
    "Add", "Sub", "Mul", "Div", "Abs", "Log", "Power", "Sign", "Neg",
    "Mean", "Std", "Var", "Skew", "Kurt", "Med", "Sum", "Prod",
    "Ref", "Delta", "TsRank", "TsMax", "TsMin", "TsArgMax", "TsArgMin", "Correlation",
    "Rank", "CSRankNorm",
    "EMA", "SMA", "WMA",
    "Slope", "Rsquare", "Resi",
    "If", "Greater", "Less",
    "SignedPower", "TsDecay", "Scale", "Tanh", "Exp",
}


class ExpressionValidator:
    """Validate Qlib factor expressions before computation."""

    def __init__(self, config: MiningConfig | None = None):
        self._config = config or MiningConfig()
        self._valid_fields: Set[str] = set(
            self._config.base_fields + self._config.minute_agg_fields
        )

    def validate(self, expression: str, max_depth: int | None = None) -> ValidationResult:
        """Validate a Qlib expression. Checks: non-empty, balanced parens, known fields, depth limit."""
        if max_depth is None:
            max_depth = self._config.max_expression_depth
        errors: List[str] = []
        warnings: List[str] = []

        if not expression or not expression.strip():
            return ValidationResult(valid=False, errors=["Empty expression"])
        expr = expression.strip()

        # Parentheses balance
        depth = 0
        for ch in expr:
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
            if depth < 0:
                errors.append("Unbalanced parentheses: extra closing paren")
                break
        if depth > 0:
            errors.append("Unbalanced parentheses: missing closing paren")
        if errors:
            return ValidationResult(valid=False, errors=errors)

        # Field check
        fields_used = set(re.findall(r"\$[a-zA-Z_][a-zA-Z0-9_]*", expr))
        for f in fields_used:
            if f not in self._valid_fields:
                errors.append(f"Unknown field: {f}")

        # Depth check
        nesting = self._max_nesting_depth(expr)
        if nesting > max_depth:
            errors.append(f"Expression depth {nesting} exceeds limit {max_depth}")

        # Operator check (warning only)
        ops_used = set(re.findall(r"([A-Z][a-zA-Z]+)\s*\(", expr))
        for op in ops_used:
            if op not in KNOWN_OPERATORS:
                warnings.append(f"Unknown operator: {op}")

        return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)

    def safe_wrap(self, expression: str) -> str:
        """Wrap Div operations to handle zero division."""
        pattern = r"Div\(([^()]+(?:\([^()]*\))*[^()]*),\s*([^()]+(?:\([^()]*\))*[^()]*)\)"
        def _safe_div(match):
            a, b = match.group(1).strip(), match.group(2).strip()
            return f"If(Greater(Abs({b}), 1e-8), Div({a}, {b}), 0)"
        return re.sub(pattern, _safe_div, expression)

    def _max_nesting_depth(self, expr: str) -> int:
        max_d = 0
        current = 0
        for ch in expr:
            if ch == "(":
                current += 1
                max_d = max(max_d, current)
            elif ch == ")":
                current -= 1
        return max_d
