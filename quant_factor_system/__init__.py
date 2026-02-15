"""
Quant Factor System - 量化因子研究平台

功能:
- 数据层: TimescaleDB存储, RiceQuant数据源
- 因子层: 因子计算, 聚合
- 选股层: 单因子/多因子选股
- 回测层: 回测引擎, 绩效分析

使用:
    # 数据
    from quant_factor_system.data import QuantDataManager, RiceQuantSource
    
    # 因子
    from quant_factor_system.factors import FactorAggregator, FactorFactory
    
    # 选股
    from quant_factor_system.selector import SingleFactorSelector, MultiFactorSelector
    
    # 回测
    from quant_factor_system.backtest import BacktestEngine, PerformanceAnalyzer
"""

__version__ = "4.0.0"

# 数据层
from .data import (
    QuantDataManager,
    RiceQuantSource,
    TimescaleDBStorage,
    CSVStorage,
)

# 因子层
from .factors import (
    FactorAggregator,
    FactorFactory,
    FactorRegistry,
)

# 选股层
from .selector import (
    SingleFactorSelector,
    MultiFactorSelector,
    FactorFilter,
)

# 回测层
from .backtest import (
    BacktestEngine,
    PerformanceAnalyzer,
)

__all__ = [
    # 版本
    '__version__',
    
    # 数据层
    'QuantDataManager',
    'RiceQuantSource',
    'TimescaleDBStorage',
    'CSVStorage',
    
    # 因子层
    'FactorAggregator',
    'FactorFactory',
    'FactorRegistry',
    
    # 选股层
    'SingleFactorSelector',
    'MultiFactorSelector',
    'FactorFilter',
    
    # 回测层
    'BacktestEngine',
    'PerformanceAnalyzer',
]
