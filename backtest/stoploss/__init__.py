"""
止盈止损模块
Stop Loss Module

功能:
- 固定止盈止损
- 移动止盈止损
- ATR动态止损
"""

from .fixed import FixedStopLoss, TrailingStopLoss, TimeStopLoss, CombinedStopLoss, StopCheckResult, StopReason
from .atr import ATRCalculator, ATRResult, ATRStopLoss, ATRTrailingStop

__all__ = [
    'FixedStopLoss',
    'TrailingStopLoss',
    'TimeStopLoss',
    'CombinedStopLoss',
    'StopCheckResult',
    'StopReason',
    'ATRCalculator',
    'ATRResult',
    'ATRStopLoss',
    'ATRTrailingStop',
]
