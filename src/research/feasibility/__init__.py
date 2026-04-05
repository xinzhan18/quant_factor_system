"""Feasibility proxy engine — research-level implementability checks.

All computations are pure vectorized operations on MultiIndex
(datetime, instrument) DataFrames.  No database or Qlib dependency.
"""

from research.feasibility.engine import FeasibilityEngine

__all__ = ["FeasibilityEngine"]
