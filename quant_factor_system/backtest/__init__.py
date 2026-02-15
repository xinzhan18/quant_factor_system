"""
回测模块
Backtest Module

功能:
- 回测引擎 (engine.py)
- 绩效分析 (analyzer.py)

使用示例:
    from quant_factor_system.backtest import BacktestEngine, PerformanceAnalyzer
    
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
]
