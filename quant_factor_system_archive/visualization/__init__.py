# Visualization - 可视化模块
from .visualization import FactorDashboard, ReportGenerator
from . import tearsheet
from . import pandas_ext

# 导出 Tearsheet
TearsheetBuilder = tearsheet.TearsheetBuilder
GridFigure = tearsheet.GridFigure
MonteCarloSimulator = tearsheet.MonteCarloSimulator
create_factor_tearsheet = tearsheet.create_factor_tearsheet

# 导出 Pandas 扩展 (从模块直接导入)
extend_pandas = pandas_ext.extend_pandas

__all__ = [
    # 原有
    "FactorDashboard",
    "ReportGenerator",
    
    # Tearsheet
    "TearsheetBuilder",
    "GridFigure",
    "MonteCarloSimulator",
    "create_factor_tearsheet",
    
    # Pandas 扩展
    "extend_pandas",
]
