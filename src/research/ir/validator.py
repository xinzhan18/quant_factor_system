"""Validation for Factor IR v1."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from research.ir.schema import FactorIR

SUPPORTED_BACKENDS: frozenset[str] = frozenset(
    {"qlib", "python", "daily_python"}
)
SUPPORTED_DAILY_TEMPLATES: frozenset[str] = frozenset(
    {"quantile_split_spread", "conditional_rolling_mean"}
)


class FactorIRValidationError(ValueError):
    """Raised when one or more candidates fail IR validation."""


@dataclass(frozen=True)
class FactorIRValidationResult:
    """Per-candidate validation outcome."""

    candidate_id: str
    errors: list[str]

    @property
    def passed(self) -> bool:
        return not self.errors


def validate_factor_ir(ir: FactorIR) -> list[str]:
    """Return validation errors for a single candidate IR."""
    errors: list[str] = []
    if not ir.candidate_id:
        errors.append("missing_candidate_id")

    backend = ir.factor_logic.backend
    if backend not in SUPPORTED_BACKENDS:
        errors.append(f"unknown_backend:{backend}")
        return errors

    if backend == "qlib":
        if not ir.factor_logic.expression:
            errors.append("qlib_missing_expression")
    elif backend == "python":
        if not ir.factor_logic.path:
            errors.append("python_missing_path")
    elif backend == "daily_python":
        template = ir.factor_logic.template
        if not template:
            errors.append("daily_python_missing_template")
        elif template not in SUPPORTED_DAILY_TEMPLATES:
            errors.append(f"unknown_daily_template:{template}")

    return errors


def validate_many(irs: Iterable[FactorIR], *, raise_on_error: bool = True) -> list[FactorIRValidationResult]:
    """Validate a collection of IRs, optionally raising on any failure."""
    results = [
        FactorIRValidationResult(ir.candidate_id, validate_factor_ir(ir))
        for ir in irs
    ]
    failed = [r for r in results if not r.passed]
    if raise_on_error and failed:
        msg = "; ".join(
            f"{r.candidate_id or '?'}={r.errors}" for r in failed
        )
        raise FactorIRValidationError(msg)
    return results
