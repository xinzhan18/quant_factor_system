"""
回测模块
Backtest Module

功能:
- 回测引擎 (engine.py)
- 绩效分析 (analyzer.py)
- 选股模块 (selection/)
- 信号生成 (signal/)

使用示例:
    from quant_factor_system.backtest import (
        BacktestEngine,
        PerformanceAnalyzer,
        FactorSelector,
        StockFilter,
        StockRanker
    )
    
    # 回测
    engine = BacktestEngine()
    result = engine.run(
        strategy=selection,
        price_data=price_data,
        start_date='20240101',
        end_date='20240131'
    )
    
    # 绩效分析
    analyzer = PerformanceAnalyzer()
    metrics = analyzer.analyze(
        equity=result.equity_curve,
        trades=result.trades
    )
    
    print(metrics.summary())
"""

from .engine import (
    BacktestEngine,
    BacktestResult,
    Trade,
    Position,
    Order,
    DailyResult,
    OrderSide,
    OrderType,
)

from .analyzer import (
    PerformanceAnalyzer,
    PerformanceMetrics,
)

from .selection import (
    FactorSelector,
    FactorScore,
    create_factor_selector,
    StockFilter,
    FilterType,
    FilterCondition,
    industry_filter,
    market_cap_filter,
    liquidity_filter,
    listing_date_filter,
    limit_up_down_filter,
    create_composite_filter,
    StockRanker,
    RankResult,
    create_ranker,
    SingleFactorSelector,
    SelectionResult,
    SortOrder,
    MultiFactorCombiner,
    CombinedFactor,
    CombinationMethod,
    IntersectionFilter,
    UnionFilter,
    DifferenceFilter,
    FilterResult,
)

from .signal import (
    SignalGenerator,
    SignalType,
    SignalSource,
    TradeSignal,
    SignalBatch,
    create_signal_generator,
)

from .position import (
    EqualWeightManager,
    FixedWeightManager,
    Position,
    PositionResult,
    FactorWeightedManager,
    FactorPositionResult,
    WeightingMethod,
    KellyManager,
    KellyResult,
    KellyVariant,
)

from .stoploss import (
    FixedStopLoss,
    ATRStopLoss,
)

from .risk_metrics import (
    RiskAnalyzer,
    RiskMetrics,
)

__all__ = [
    # 引擎
    'BacktestEngine',
    'BacktestResult',
    'Trade',
    'Position',
    'Order',
    'DailyResult',
    'OrderSide',
    'OrderType',
    
    # 分析
    'PerformanceAnalyzer',
    'PerformanceMetrics',
    
    # 选股
    'FactorSelector',
    'FactorScore',
    'create_factor_selector',
    'StockFilter',
    'FilterType',
    'FilterCondition',
    'industry_filter',
    'market_cap_filter',
    'liquidity_filter',
    'listing_date_filter',
    'limit_up_down_filter',
    'create_composite_filter',
    'StockRanker',
    'RankResult',
    'create_ranker',
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
    
    # 信号
    'SignalGenerator',
    'SignalType',
    'SignalSource',
    'TradeSignal',
    'SignalBatch',
    'create_signal_generator',
    
    # 仓位
    'EqualWeightPosition',
    'FactorWeightedPosition',
    'KellyPosition',
    
    # 止损
    'FixedStopLoss',
    'ATRStopLoss',
    
    # 风险指标
    'RiskAnalyzer',
    'RiskMetrics',
]
