"""
Quant Factor System - 量化因子研究平台

功能:
- 数据层: TimescaleDB存储, RiceQuant数据源
- 因子层: 因子计算, 聚合, 处理
- 回测层: 回测引擎, 绩效分析, 选股, 仓位, 止损

使用:
    # 数据
    from quant_factor_system.data import QuantDataManager, RiceQuantSource
    
    # 因子
    from quant_factor_system.factors import FactorProcessor, FactorAggregator
    
    # 回测（包含选股、仓位、止损）
    from quant_factor_system.backtest import BacktestEngine, PerformanceAnalyzer
"""

__version__ = "4.1.0"

# 数据层
from .data import (
    QuantDataManager,
    RiceQuantSource,
    TimescaleDB,
    DataManager,
)

# 因子层
from .factors import (
    FactorProcessor,
    FactorProcessorConfig,
    FactorAggregator,
    FactorFactory,
    FactorRegistry,
)

# 回测层
from .backtest import (
    BacktestEngine,
    PerformanceAnalyzer,
    # 选股
    SingleFactorSelector,
    MultiFactorCombiner,
    IntersectionFilter,
    # 仓位
    EqualWeightManager,
    FixedWeightManager,
    FactorWeightedManager,
    KellyManager,
    # 止损
    FixedStopLoss,
    ATRStopLoss,
)

__all__ = [
    # 版本
    '__version__',
    
    # 数据层
    'QuantDataManager',
    'RiceQuantSource',
    'TimescaleDB',
    'DataManager',
    
    # 因子层
    'FactorProcessor',
    'FactorProcessorConfig',
    'FactorAggregator',
    'FactorFactory',
    'FactorRegistry',
    
    # 回测层
    'BacktestEngine',
    'PerformanceAnalyzer',
    
    # 选股
    'SingleFactorSelector',
    'MultiFactorCombiner',
    'IntersectionFilter',
    
    # 仓位
    'EqualWeightManager',
    'FixedWeightManager',
    'FactorWeightedManager',
    'KellyManager',
    
    # 止损
    'FixedStopLoss',
    'ATRStopLoss',
]
