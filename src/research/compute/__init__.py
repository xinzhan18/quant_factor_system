"""Compute engine — caching and preprocessing (P1 public API).

Only the new P1 modules are exported. Legacy modules (``factor_engine``,
``data_provider``, ``universe``, ``operators``, old ``preprocess.Preprocessor``
class) remain on disk until P7 but are not re-exported — callers that still
need them must import the submodule directly.
"""

from research.compute.cache import FactorValueCache
from research.compute.preprocess import (
    PreprocessConfig,
    preprocess_factor,
    winsorize_mad,
    zscore_cross_section,
)

__all__ = [
    "FactorValueCache",
    "PreprocessConfig",
    "preprocess_factor",
    "winsorize_mad",
    "zscore_cross_section",
]
