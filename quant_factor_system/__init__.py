"""
量化多因子评价系统
Quantitative Multi-Factor Evaluation System
"""

from .base import Factor, FactorSystem
from .factors import (
    MomentumFactor, 
    ValueFactor, 
    QualityFactor, 
    VolatilityFactor,
    GrowthFactor
)
from .evaluator import FactorEvaluator

__version__ = "1.0.0"
__all__ = [
    "Factor",
    "FactorSystem",
    "MomentumFactor",
    "ValueFactor", 
    "QualityFactor",
    "VolatilityFactor",
    "GrowthFactor",
    "FactorEvaluator"
]
