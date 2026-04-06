"""Compute engine — data provision, factor computation, caching, and preprocessing.

Public API:
    DataProvider      — Qlib D.features wrapper with parquet caching
    FactorEngine      — DSL and Python factor execution
    FactorValueCache  — Parquet disk cache keyed by md5 hash
    UniverseManager   — Stock universe resolution (default: CSI 1000)
    Preprocessor      — Vectorized cross-sectional winsorize / zscore / neutralize
    register_custom_operators — Register custom Qlib operators
"""

from research.compute.universe import UniverseManager
from research.compute.cache import FactorValueCache
from research.compute.data_provider import DataProvider
from research.compute.factor_engine import FactorEngine
from research.compute.preprocess import Preprocessor
from research.compute.operators import register_custom_operators

__all__ = [
    "UniverseManager",
    "FactorValueCache",
    "DataProvider",
    "FactorEngine",
    "Preprocessor",
    "register_custom_operators",
]
