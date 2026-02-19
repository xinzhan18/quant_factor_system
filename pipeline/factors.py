# Pipeline Factors - 因子别名

import pandas as pd
import numpy as np

from quant_factor_system.factors.basic import (
    MomentumFactor,
    ValueFactor,
    QualityFactor,
    VolatilityFactor,
    SizeFactor,
    LiquidityFactor,
    GrowthFactor,
)


class MovingAverage:
    """移动平均"""
    def __init__(self, window: int = 20):
        self.window = window
        
    def __call__(self, data: pd.DataFrame) -> pd.Series:
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        if isinstance(close.index, pd.MultiIndex):
            ma = close.groupby(level='symbol').rolling(window=self.window).mean()
            ma = ma.reset_index(level='symbol', drop=True)
        else:
            ma = close.rolling(window=self.window).mean()
        
        return ma


class RSI:
    """RSI 相对强弱指数"""
    def __init__(self, window: int = 14):
        self.window = window
        
    def __call__(self, data: pd.DataFrame) -> pd.Series:
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        delta = close.diff()
        gain = delta.where(delta > 0, 0)
        loss = (-delta).where(delta < 0, 0)
        
        if isinstance(close.index, pd.MultiIndex):
            avg_gain = gain.groupby(level='symbol').transform(lambda x: x.rolling(window=self.window).mean())
            avg_loss = loss.groupby(level='symbol').transform(lambda x: x.rolling(window=self.window).mean())
        else:
            avg_gain = gain.rolling(window=self.window).mean()
            avg_loss = loss.rolling(window=self.window).mean()
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        rsi = rsi.replace([np.inf, -np.inf], np.nan)
        
        return rsi


__all__ = [
    'MomentumFactor',
    'ValueFactor',
    'QualityFactor',
    'VolatilityFactor',
    'SizeFactor',
    'LiquidityFactor',
    'GrowthFactor',
    'MovingAverage',
    'RSI',
]

__all__ = [
    'MomentumFactor',
    'ValueFactor',
    'QualityFactor',
    'VolatilityFactor',
    'SizeFactor',
    'LiquidityFactor',
    'GrowthFactor',
]
