"""
Visualization module - Factor analysis charts and reports.

Extracted from factors/visualization/ as a standalone module.
All functions accept pure DataFrames as input.

Usage:
    from quant_factor_system.visualization import ICAnalyzer, GroupReturnsAnalyzer
"""

from .ic_analyzer import ICAnalyzer, create_ic_analyzer
from .group_returns import GroupReturnsAnalyzer, create_group_analyzer
from .report import FactorReportGenerator, create_report_generator

__all__ = [
    'ICAnalyzer',
    'create_ic_analyzer',
    'GroupReturnsAnalyzer',
    'create_group_analyzer',
    'FactorReportGenerator',
    'create_report_generator',
]
