"""
选股模块
Selectors Module

功能:
- 单因子选股
- 多因子组合
- 交集过滤
"""

from .single import SingleFactorSelector, SelectionResult, SortOrder
from .multi import MultiFactorCombiner, CombinedFactor, CombinationMethod
from .filter import IntersectionFilter, UnionFilter, DifferenceFilter, FilterResult

__all__ = [
    'SingleFactorSelector',
    'SelectionResult',
    'SortOrder',
    'MultiFactorCombiner',
    'CombinedFactor',
    'CombinationMethod',
    'IntersectionFilter',
    'UnionFilter',
    'DifferenceFilter',
    'FilterResult',
]
