"""Factor IR schema and adapters."""

from research.ir.adapter import normalize_candidate, normalize_manifest
from research.ir.schema import DataLogic, FactorIR, FactorLogic, LabelSpec
from research.ir.validator import FactorIRValidationError, validate_factor_ir

__all__ = [
    "DataLogic",
    "FactorIR",
    "FactorLogic",
    "LabelSpec",
    "FactorIRValidationError",
    "normalize_candidate",
    "normalize_manifest",
    "validate_factor_ir",
]
