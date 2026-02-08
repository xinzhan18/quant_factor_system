"""
量化多因子评价系统
Quantitative Multi-Factor Evaluation System

一个简单但功能完整的 Python 量化多因子评价框架。
基于 Barra 模型和行业最佳实践。

主要特性:
- 模块化设计，易于扩展
- 支持多种数据源
- 完整的因子评估体系
- 简单的回测框架
- 自动数据更新
- 可视化报告

版本: 2.0.0
"""

from .base import Factor, FactorSystem
from .factors import (
    MomentumFactor, 
    ValueFactor, 
    QualityFactor, 
    VolatilityFactor,
    GrowthFactor,
    SizeFactor,
    LiquidityFactor
)
from .extended_factors import (
    BarraStyleFactor,
    SizeFactor as BarraSizeFactor,
    BetaFactor,
    MomentumFactor as BarraMomentumFactor,
    SizeNonlinearFactor,
    ValueFactor as BarraValueFactor,
    VolatilityFactor as BarraVolatilityFactor,
    LiquidityFactor as BarraLiquidityFactor,
    EarningsYieldFactor,
    GrowthFactor as BarraGrowthFactor,
    LeverageFactor,
    IndustryFactor,
    DEFAULT_BARRA_FACTORS
)
from .evaluator import FactorEvaluator, BacktestEngine
from .data_source import (
    DataSource,
    AkshareDataSource,
    YFinanceDataSource,
    MultiSourceDataManager,
    DataCache,
    get_a_stock_data
)
from .data_processor import (
    DataProcessor,
    FactorNeutralizer,
    FactorPreprocessor,
    get_real_stock_data,
    get_market_index_data
)
from .data_storage import (
    SQLiteDB,
    DataRepository,
    AutoDataUpdater
)
from .automation import (
    TaskScheduler,
    TaskStatus,
    TaskResult,
    FactorAnalysisPipeline,
    create_default_pipeline
)
from .visualization import (
    FactorDashboard,
    ReportGenerator
)

__version__ = "2.1.0"
__author__ = "OpenClaw"

__all__ = [
    # 核心类
    "Factor",
    "FactorSystem",
    
    # 基础因子
    "MomentumFactor",
    "ValueFactor", 
    "QualityFactor",
    "VolatilityFactor",
    "GrowthFactor",
    "SizeFactor",
    "LiquidityFactor",
    
    # Barra 风格因子
    "BarraStyleFactor",
    "BarraSizeFactor",
    "BetaFactor",
    "BarraMomentumFactor",
    "SizeNonlinearFactor",
    "BarraValueFactor",
    "BarraVolatilityFactor",
    "BarraLiquidityFactor",
    "EarningsYieldFactor",
    "BarraGrowthFactor",
    "LeverageFactor",
    "IndustryFactor",
    "DEFAULT_BARRA_FACTORS",
    
    # 评估器
    "FactorEvaluator",
    "BacktestEngine",
    
    # 数据源
    "DataSource",
    "AkshareDataSource",
    "YFinanceDataSource",
    "MultiSourceDataManager",
    "DataCache",
    "get_a_stock_data",
    
    # 数据持久化
    "SQLiteDB",
    "DataRepository",
    "AutoDataUpdater",
    
    # 自动化
    "TaskScheduler",
    "TaskStatus",
    "TaskResult",
    "FactorAnalysisPipeline",
    "create_default_pipeline",
    
    # 可视化
    "FactorDashboard",
    "ReportGenerator",
    
    # 数据处理（专业版）
    "DataProcessor",
    "FactorNeutralizer",
    "FactorPreprocessor",
    "get_real_stock_data",
    "get_market_index_data",
]
