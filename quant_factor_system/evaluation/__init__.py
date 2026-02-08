# Evaluation - 评估模块
from .factor_evaluator import (
    BacktestConfig,
    FactorResult,
    FactorPreprocessor,
    ICAnalyzer,
    GroupBacktester,
    TransactionCostCalculator,
    FactorEvaluator,
    align_factor_returns,
    create_return_series
)

# Enhanced Evaluation
from .enhanced import (
    EnhancedFactorResult,
    EnhancedICAnalyzer,
    GroupReturnsAnalyzer,
    FactorCorrelator,
    EnhancedEvaluator,
    evaluate_factor
)

# Alphalens 集成
try:
    from .alphalens_wrapper import (
        AlphalensWrapper,
        create_tearsheet_report,
        calculate_ic_stats,
        calculate_ic_decay,
        calculate_group_returns,
        plot_ic_analysis,
        plot_group_returns,
        generate_factor_report
    )
    ALPHALENS_AVAILABLE = True
except ImportError:
    ALPHALENS_AVAILABLE = False
    AlphalensWrapper = None

__all__ = [
    # 原有评估模块
    "BacktestConfig",
    "FactorResult",
    "FactorPreprocessor",
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
]
