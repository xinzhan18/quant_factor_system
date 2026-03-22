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
    "If", "IfElse", "Greater", "Less",
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
        """Wrap Div operations to handle zero division.

        Uses iterative parsing to handle arbitrarily nested expressions.
        """
        result = self._wrap_div_recursive(expression)
        return result

    def _wrap_div_recursive(self, expr: str) -> str:
        """Find and wrap Div(...) calls, handling nested parentheses."""
        output = []
        i = 0
        while i < len(expr):
            # Look for "Div("
            if expr[i:i+4] == "Div(" and (i == 0 or not expr[i-1].isalpha()):
                # Find the matching closing paren
                start = i + 4
                args = self._split_top_level_args(expr, start)
                if args is not None:
                    a_raw, b_raw, end_pos = args
                    a = self._wrap_div_recursive(a_raw.strip())
                    b = self._wrap_div_recursive(b_raw.strip())
                    output.append(f"If(Greater(Abs({b}), 1e-8), Div({a}, {b}), 0)")
                    i = end_pos
                    continue
            output.append(expr[i])
            i += 1
        return "".join(output)

    @staticmethod
    def _split_top_level_args(expr: str, start: int):
        """Split two comma-separated arguments respecting nested parens.

        Returns (arg1, arg2, end_position) or None if parsing fails.
        ``start`` should point to the first character after the opening '('.
        """
        depth = 1
        comma_pos = None
        i = start
        while i < len(expr) and depth > 0:
            ch = expr[i]
            if ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    break
            elif ch == "," and depth == 1 and comma_pos is None:
                comma_pos = i
            i += 1
        if depth != 0 or comma_pos is None:
            return None
        return expr[start:comma_pos], expr[comma_pos+1:i], i + 1

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
