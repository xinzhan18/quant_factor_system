"""
信号模块
Signal Module

提供交易信号生成和管理功能

主要组件:
- SignalGenerator: 信号生成器

使用方式:
    from quant_factor_system.backtest.signal import SignalGenerator, SignalType
    
    # 创建信号生成器
    generator = SignalGenerator()
    
    # 生成因子信号
    signals = generator.generate_factor_signals(factor_df, price_df, top_n=50)
    
    # 过滤信号
    filtered = generator.filter_signals(signals, min_strength=0.5)
"""

from .generator import (
    SignalGenerator,
    SignalType,
    SignalSource,
    TradeSignal,
    SignalBatch,
    create_signal_generator,
)

__all__ = [
    'SignalGenerator',
    'SignalType',
    'SignalSource',
    'TradeSignal',
    'SignalBatch',
    'create_signal_generator',
]
