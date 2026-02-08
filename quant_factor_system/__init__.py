"""
量化多因子评价系统
Quantitative Multi-Factor Evaluation System

工程化目录结构:
├── core/           # 核心类
├── factors/        # 因子模块
│   ├── basic/     # 基础因子
│   └── barra/     # Barra因子
├── data/          # 数据模块
│   ├── source/    # 数据源
│   └── processor/  # 数据处理
├── evaluation/     # 评估模块
├── trading/        # 交易模块
├── automation/     # 自动化模块
├── visualization/  # 可视化模块
└── storage/        # 存储模块

版本: 3.0.0
"""

from .core import Factor, FactorSystem
from .factors import *
from .data import *
from .evaluation import *
from .trading import *
from .automation import *
from .visualization import *
from .storage import *

__version__ = "3.0.0"
__author__ = "OpenClaw"

__all__ = [
    # Core
    "Factor",
    "FactorSystem",
    
    # Factors
    "MomentumFactor",
    "ValueFactor",
    "QualityFactor",
    "VolatilityFactor",
    "GrowthFactor",
    "SizeFactor",
    "LiquidityFactor",
    "BarraSizeFactor",
    "BetaFactor",
    "BarraMomentumFactor",
    "BarraValueFactor",
    "BarraVolatilityFactor",
    "BarraLiquidityFactor",
    "EarningsYieldFactor",
    "BarraGrowthFactor",
    "LeverageFactor",
    "IndustryFactor",
    
    # Data
    "DataProcessor",
    "FactorNeutralizer",
    "FactorPreprocessor",
    "get_real_stock_data",
    "get_market_index_data",
    "DataRepository",
    
    # Evaluation
    "BacktestConfig",
    "FactorResult",
    "ICAnalyzer",
    "GroupBacktester",
    "TransactionCostCalculator",
    "FactorEvaluator",
    "align_factor_returns",
    "create_return_series",
    
    # Enhanced Evaluation
    "EnhancedFactorResult",
    "EnhancedICAnalyzer",
    "GroupReturnsAnalyzer",
    "FactorCorrelator",
    "EnhancedEvaluator",
    "evaluate_factor",
    
    # Automation
    "TaskScheduler",
    "TaskStatus",
    "TaskResult",
    "FactorAnalysisPipeline",
    
    # Visualization
    "FactorDashboard",
    "ReportGenerator",
    
    # Storage
    "FactorDatabase",
    "CSVStorage",
    "Cache",
    "get_database",
    "get_csv_storage",
    "get_cache",
]
