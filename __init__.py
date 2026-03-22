"""
Quant Factor System - 量化因子研究平台

核心工作流: 自动化因子挖掘 (mining)
- 数据层: TimescaleDB存储, RiceQuant数据源, Qlib同步
- 挖掘层: 表达式引擎, 多阶段评估, 因子库, 经验记忆
- 可视化: IC分析, 分组收益, 报告生成

使用:
    from quant_factor_system.data import TimescaleDB
    from quant_factor_system.mining import FactorMiningEvaluator, FactorLibrary
    from quant_factor_system.visualization import ICAnalyzer
"""

__version__ = "4.1.0"

# 数据层
from .data import (
    QuantDataManager,
    RiceQuantSource,
    TimescaleDB,
    DataManager,
)

__all__ = [
    '__version__',
    'QuantDataManager',
    'RiceQuantSource',
    'TimescaleDB',
    'DataManager',
]
