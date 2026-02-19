"""
ATR动态止盈止损模块
ATR Stop Loss / Take Profit

功能:
- 基于ATR(平均真实波幅)计算动态止损位
- 波动率自适应
- 多周期ATR支持

使用示例:
    from quant_factor_system.stoploss.atr import ATRStopLoss
    
    sl = ATRStopLoss(
        atr_multiplier=2.0,  # 2倍ATR
        atr_period=14        # ATR周期
    )
    
    should_close, reason = sl.check(
        entry_price=10.0,
        current_price=9.5,
        atr_value=0.3
    )
"""

import pandas as pd
from typing import Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class ATRResult:
    """ATR计算结果"""
    tr: pd.Series          # 真实波幅
    atr: pd.Series         # ATR值
    atr_ma: pd.Series      # ATR移动平均


class ATRCalculator:
    """
    ATR (Average True Range) 计算器
    
    真实波幅 (True Range):
    TR = max(High-Low, |High-PrevClose|, |Low-PrevClose|)
    
    ATR = TR的N日简单移动平均
    """
    
    def __init__(
        self,
        period: int = 14,
        ma_type: str = 'sma'  # 'sma' 或 'ema'
    ):
        """
        初始化
        
        Args:
            period: ATR周期
            ma_type: 移动平均类型
        """
        self.period = period
        self.ma_type = ma_type
    
    def calculate(self, df: pd.DataFrame) -> ATRResult:
        """
        计算ATR
        
        Args:
            df: 包含 high, low, close 列的DataFrame
            
        Returns:
            ATRResult
        """
        # 1. 计算真实波幅 (True Range)
        high = df['high']
        low = df['low']
        close = df['close']
        
        # 前收盘价
        prev_close = close.shift(1)
        
        # 三种情况取最大
        tr1 = high - low
        tr2 = abs(high - prev_close)
        tr3 = abs(low - prev_close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
        # 2. 计算ATR (移动平均)
        if self.ma_type == 'ema':
            atr = tr.ewm(span=self.period, adjust=False).mean()
        else:
            atr = tr.rolling(window=self.period).mean()
        
        # 3. ATR移动平均 (用于平滑)
        atr_ma = atr.rolling(window=self.period * 2).mean()
        
        return ATRResult(
            tr=tr.dropna(),
            atr=atr.dropna(),
            atr_ma=atr_ma.dropna()
        )
    
    def calculate_single(self, df: pd.DataFrame) -> float:
        """
        计算最新ATR值
        
        Args:
            df: 价格数据
            
        Returns:
            最新ATR值
        """
        result = self.calculate(df)
        
        if len(result.atr) > 0:
            return result.atr.iloc[-1]
        
        return 0


class BaseATRStop(ABC):
    """ATR止损基类"""
    
    @abstractmethod
    def get_stop_price(
        self,
        entry_price: float,
        atr: float,
        **kwargs
    ) -> float:
        """
        计算止损价格
        
        Args:
            entry_price: 入场价格
            atr: ATR值
            
        Returns:
            止损价格
        """


class ATRStopLoss(BaseATRStop):
    """
    ATR动态止损
    
    止损位 = 入场价 - N * ATR
    
    特点:
    - 波动率自适应
    - 避免被正常波动止损
    """
    
    def __init__(
        self,
        atr_multiplier: float = 2.0,  # ATR倍数
        atr_period: int = 14,        # ATR周期
        ma_type: str = 'sma'          # MA类型
    ):
        """
        Args:
            atr_multiplier: ATR倍数 (如2.0表示2倍ATR)
            atr_period: ATR周期
            ma_type: 移动平均类型
        """
        self.atr_multiplier = atr_multiplier
        self.atr_period = atr_period
        self.ma_type = ma_type
        self.calculator = ATRCalculator(period=atr_period, ma_type=ma_type)
    
    def get_stop_price(
        self,
        entry_price: float,
        atr: float,
        direction: str = 'long'
    ) -> float:
        """
        计算止损价格
        
        Args:
            entry_price: 入场价格
            atr: ATR值
            direction: 方向 ('long' 或 'short')
            
        Returns:
            止损价格
        """
        stop_distance = atr * self.atr_multiplier
        
        if direction == 'long':
            return entry_price - stop_distance
        else:
            return entry_price + stop_distance
    
    def check(
        self,
        entry_price: float,
        current_price: float,
        atr: float,
        direction: str = 'long',
        **kwargs
    ) -> Tuple[bool, str, float]:
        """
        检查是否触发ATR止损
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
            atr: ATR值
            direction: 方向
            
        Returns:
            (should_close, reason, stop_price)
        """
        stop_price = self.get_stop_price(entry_price, atr, direction)
        
        if direction == 'long':
            if current_price <= stop_price:
                return (
                    True,
                    'atr_stop',
                    stop_price
                )
        else:  # short
            if current_price >= stop_price:
                return (
                    True,
                    'atr_stop',
                    stop_price
                )
        
        return (False, 'not_triggered', stop_price)


class ATRTrailingStop(BaseATRStop):
    """
    ATR移动止盈止损
    
    止损位 = 最高(低)点 - N * ATR
    
    特点:
    - 追踪价格极端点
    - 动态调整止损位
    """
    
    def __init__(
        self,
        atr_multiplier: float = 2.0,
        atr_period: int = 14,
        activation: float = 0.03  # 激活阈值
    ):
        self.atr_multiplier = atr_multiplier
        self.atr_period = atr_period
        self.activation = activation
        
        self.calculator = ATRCalculator(period=atr_period)
        
        # 追踪状态
        self.highest_price: float = 0
        self.lowest_price: float = float('inf')
        self.activated: bool = False
    
    def reset(self):
        """重置状态"""
        self.highest_price = 0
        self.lowest_price = float('inf')
        self.activated = False
    
    def get_stop_price(
        self,
        current_price: float,
        atr: float,
        direction: str = 'long',
        update_extreme: bool = True
    ) -> float:
        """
        计算移动止损价格
        
        Args:
            current_price: 当前价格
            atr: ATR值
            direction: 方向
            update_extreme: 是否更新极端点
        """
        if direction == 'long':
            if current_price > self.highest_price:
                self.highest_price = current_price
            
            return self.highest_price - atr * self.atr_multiplier
        
        else:  # short
            if current_price < self.lowest_price:
                self.lowest_price = current_price
            
            return self.lowest_price + atr * self.atr_multiplier
    
    def check(
        self,
        entry_price: float,
        current_price: float,
        atr: float,
        direction: str = 'long',
        **kwargs
    ) -> Tuple[bool, str, float]:
        """
        检查是否触发移动ATR止损
        
        Returns:
            (should_close, reason, stop_price)
        """
        # 计算当前盈利
        if entry_price > 0:
            profit_ratio = (current_price - entry_price) / entry_price
        else:
            profit_ratio = 0
        
        # 检查是否激活
        if not self.activated:
            if profit_ratio >= self.activation:
                self.activated = True
        
        if not self.activated:
            return (False, 'not_activated', 0)
        
        # 获取止损价格
        stop_price = self.get_stop_price(current_price, atr, direction)
        
        # 检查是否触发
        if direction == 'long':
            if current_price <= stop_price:
                return (True, 'atr_trailing', stop_price)
        else:
            if current_price >= stop_price:
                return (True, 'atr_trailing', stop_price)
        
        return (False, 'not_triggered', stop_price)


class VolatilityBasedPositionSizing:
    """
    基于波动率的仓位管理
    
    根据ATR调整仓位:
    仓位 = 账户风险 / (ATR * 乘数)
    """
    
    def __init__(
        self,
        risk_per_trade: float = 0.02,  # 每笔交易风险 (2%)
        atr_multiplier: float = 2.0,   # ATR乘数
        max_position: float = 0.2,     # 最大仓位 (20%)
        atr_period: int = 14
    ):
        """
        Args:
            risk_per_trade: 每笔交易承担的风险比例
            atr_multiplier: ATR乘数
            max_position: 最大仓位比例
            atr_period: ATR周期
        """
        self.risk_per_trade = risk_per_trade
        self.atr_multiplier = atr_multiplier
        self.max_position = max_position
        self.atr_period = atr_period
    
    def calculate_position_size(
        self,
        entry_price: float,
        atr: float,
        account_value: float,
        direction: str = 'long'
    ) -> float:
        """
        计算仓位大小
        
        Args:
            entry_price: 入场价格
            atr: ATR值
            account_value: 账户金额
            direction: 方向
            
        Returns:
            仓位比例 (0-1)
        """
        if atr <= 0:
            return self.max_position
        
        # 每股风险
        stop_distance = atr * self.atr_multiplier
        
        if direction == 'long':
            risk_per_share = entry_price - (entry_price - stop_distance)
        else:
            risk_per_share = (entry_price + stop_distance) - entry_price
        
        if risk_per_share <= 0:
            return self.max_position
        
        # 账户风险金额
        risk_amount = account_value * self.risk_per_trade
        
        # 仓位大小 (股数)
        position_shares = risk_amount / risk_per_share
        
        # 仓位比例
        position_value = position_shares * entry_price
        position_ratio = position_value / account_value
        
        # 限制最大仓位
        return min(position_ratio, self.max_position)


# ==================== 导出 ====================

__all__ = [
    'ATRCalculator',
    'ATRResult',
    'ATRStopLoss',
    'ATRTrailingStop',
    'VolatilityBasedPositionSizing',
]
