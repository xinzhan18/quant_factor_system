"""
固定止盈止损模块
Fixed Stop Loss / Take Profit

功能:
- 固定比例止盈
- 固定比例止损
- 时间止损

使用示例:
    from quant_factor_system.stoploss.fixed import FixedStopLoss, TimeStopLoss
    
    # 固定止盈止损
    sl = FixedStopLoss(
        stop_profit=0.10,  # 10%止盈
        stop_loss=0.05    # 5%止损
    )
    
    should_close, reason = sl.check(entry_price=10.0, current_price=10.8)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from datetime import datetime, date, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class StopReason(Enum):
    """止损原因"""
    STOP_PROFIT = 'stop_profit'      # 止盈
    STOP_LOSS = 'stop_loss'          # 止损
    TIME_STOP = 'time_stop'         # 时间止损
    TRAILING_STOP = 'trailing_stop' # 移动止盈止损
    ATR_STOP = 'atr_stop'           # ATR止损
    NOT_TRIGGERED = 'not_triggered'  # 未触发


@dataclass
class StopCheckResult:
    """止损检查结果"""
    should_close: bool
    reason: str
    current_price: float
    entry_price: float
    profit_ratio: float = 0.0
    hold_days: int = 0
    message: str = ''
    
    def __post_init__(self):
        if self.entry_price > 0:
            self.profit_ratio = (self.current_price - self.entry_price) / self.entry_price
        
        if not self.should_close:
            self.reason = StopReason.NOT_TRIGGERED.value
        
        self.message = self._generate_message()
    
    def _generate_message(self) -> str:
        """生成消息"""
        if not self.should_close:
            return f"未触发止盈止损，当前盈利: {self.profit_ratio*100:.2f}%"
        
        return f"触发{self.reason}，盈利: {self.profit_ratio*100:.2f}%"


class BaseStopLoss(ABC):
    """止损基类"""
    
    @abstractmethod
    def check(
        self,
        entry_price: float,
        current_price: float,
        **kwargs
    ) -> StopCheckResult:
        """
        检查是否需要止损
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
            **kwargs: 其他参数
            
        Returns:
            StopCheckResult
        """
        pass
    
    def check_series(
        self,
        entry_price: float,
        price_series: pd.Series,
        **kwargs
    ) -> List[StopCheckResult]:
        """
        检查价格序列
        
        Args:
            entry_price: 入场价格
            price_series: 价格序列
            
        Returns:
            止损结果列表
        """
        results = []
        
        for i, current_price in enumerate(price_series):
            result = self.check(entry_price, current_price, **kwargs)
            results.append(result)
            
            if result.should_close:
                break
        
        return results


class FixedStopLoss(BaseStopLoss):
    """
    固定止盈止损
    
    特点:
    - 固定止盈比例
    - 固定止损比例
    - 简单直接
    """
    
    def __init__(
        self,
        stop_profit: float = 0.10,  # 止盈比例 (10%)
        stop_loss: float = 0.05,    # 止损比例 (5%)
        trailing: bool = False      # 是否启用移动止盈
    ):
        """
        初始化
        
        Args:
            stop_profit: 止盈比例 (如0.10表示10%)
            stop_loss: 止损比例 (如0.05表示5%)
            trailing: 是否启用移动止盈
        """
        self.stop_profit = stop_profit
        self.stop_loss = stop_loss
        self.trailing = trailing
    
    def check(
        self,
        entry_price: float,
        current_price: float,
        **kwargs
    ) -> StopCheckResult:
        """
        检查是否需要止盈止损
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
            
        Returns:
            StopCheckResult
        """
        profit_ratio = (current_price - entry_price) / entry_price
        
        # 1. 检查止盈
        if profit_ratio >= self.stop_profit:
            return StopCheckResult(
                should_close=True,
                reason=StopReason.STOP_PROFIT.value,
                current_price=current_price,
                entry_price=entry_price,
                profit_ratio=profit_ratio,
                message=f"✅ 触发止盈 (+{profit_ratio*100:.2f}%)"
            )
        
        # 2. 检查止损
        if profit_ratio <= -self.stop_loss:
            return StopCheckResult(
                should_close=True,
                reason=StopReason.STOP_LOSS.value,
                current_price=current_price,
                entry_price=entry_price,
                profit_ratio=profit_ratio,
                message=f"🛑 触发止损 ({profit_ratio*100:.2f}%)"
            )
        
        # 3. 未触发
        return StopCheckResult(
            should_close=False,
            reason=StopReason.NOT_TRIGGERED.value,
            current_price=current_price,
            entry_price=entry_price,
            profit_ratio=profit_ratio,
            message=f"未触发 ({profit_ratio*100:.2f}%)"
        )


class TrailingStopLoss(BaseStopLoss):
    """
    移动止盈止损
    
    特点:
    - 追踪最高点
    - 回撤达到阈值时止盈
    - 避免过早止盈
    """
    
    def __init__(
        self,
        trailing_stop: float = 0.10,  # 回撤阈值 (10%)
        activation: float = 0.05,    # 激活阈值 (5%)
        type_: str = 'stop_profit'   # 'stop_profit' 或 'stop_loss'
    ):
        """
        初始化
        
        Args:
            trailing_stop: 回撤阈值
            activation: 激活阈值 (需要先盈利多少才启用移动止盈)
            type_: 类型 ('stop_profit'=移动止盈, 'stop_loss'=移动止损)
        """
        self.trailing_stop = trailing_stop
        self.activation = activation
        self.type_ = type_
        
        # 追踪状态
        self.highest_price: float = 0
        self.activated: bool = False
    
    def reset(self):
        """重置状态"""
        self.highest_price = 0
        self.activated = False
    
    def check(
        self,
        entry_price: float,
        current_price: float,
        **kwargs
    ) -> StopCheckResult:
        """
        检查是否需要移动止盈止损
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
        """
        # 更新最高点
        if current_price > self.highest_price:
            self.highest_price = current_price
        
        # 计算从最高点的回撤
        if self.highest_price > 0:
            drawdown = (self.highest_price - current_price) / self.highest_price
        else:
            drawdown = 0
        
        # 计算当前盈利
        profit_ratio = (current_price - entry_price) / entry_price
        
        # 检查是否激活
        if not self.activated:
            if profit_ratio >= self.activation:
                self.activated = True
        
        # 检查移动止盈
        if self.activated and self.type_ == 'stop_profit':
            if drawdown >= self.trailing_stop:
                return StopCheckResult(
                    should_close=True,
                    reason=StopReason.TRAILING_STOP.value,
                    current_price=current_price,
                    entry_price=entry_price,
                    profit_ratio=profit_ratio,
                    message=f"✅ 触发移动止盈 (回撤: {drawdown*100:.2f}%)"
                )
        
        # 检查移动止损
        if self.activated and self.type_ == 'stop_loss':
            # 移动止损线
            stop_line = self.highest_price * (1 - self.trailing_stop)
            
            if current_price <= stop_line:
                return StopCheckResult(
                    should_close=True,
                    reason=StopReason.TRAILING_STOP.value,
                    current_price=current_price,
                    entry_price=entry_price,
                    profit_ratio=profit_ratio,
                    message=f"🛑 触发移动止损 (止损线: {stop_line:.2f})"
                )
        
        # 未触发
        return StopCheckResult(
            should_close=False,
            reason=StopReason.NOT_TRIGGERED.value,
            current_price=current_price,
            entry_price=entry_price,
            profit_ratio=profit_ratio,
            message=f"未触发 (回撤: {drawdown*100:.2f}%)"
        )


class TimeStopLoss(BaseStopLoss):
    """
    时间止损
    
    特点:
    - 持有超过N天强制平仓
    - 避免长期套牢
    """
    
    def __init__(
        self,
        max_hold_days: int = 5,
        stop_profit: float = None,
        stop_loss: float = None
    ):
        """
        初始化
        
        Args:
            max_hold_days: 最大持有天数
            stop_profit: 止盈比例 (可选)
            stop_loss: 止损比例 (可选)
        """
        self.max_hold_days = max_hold_days
        self.stop_profit = stop_profit
        self.stop_loss = stop_loss
    
    def check(
        self,
        entry_price: float,
        current_price: float,
        entry_date: date = None,
        current_date: date = None,
        **kwargs
    ) -> StopCheckResult:
        """
        检查是否需要时间止损
        
        Args:
            entry_price: 入场价格
            current_price: 当前价格
            entry_date: 入场日期
            current_date: 当前日期
        """
        # 计算持有天数
        hold_days = 0
        if entry_date and current_date:
            hold_days = (current_date - entry_date).days
        
        # 检查时间止损
        if hold_days >= self.max_hold_days:
            profit_ratio = (current_price - entry_price) / entry_price
            
            return StopCheckResult(
                should_close=True,
                reason=StopReason.TIME_STOP.value,
                current_price=current_price,
                entry_price=entry_price,
                profit_ratio=profit_ratio,
                hold_days=hold_days,
                message=f"⏰ 触发时间止损 (持有{hold_days}天)"
            )
        
        # 如果有止盈止损参数，也检查
        if self.stop_profit or self.stop_loss:
            profit_ratio = (current_price - entry_price) / entry_price
            
            if self.stop_profit and profit_ratio >= self.stop_profit:
                return StopCheckResult(
                    should_close=True,
                    reason=StopReason.STOP_PROFIT.value,
                    current_price=current_price,
                    entry_price=entry_price,
                    profit_ratio=profit_ratio,
                    hold_days=hold_days,
                    message=f"✅ 触发止盈 ({profit_ratio*100:.2f}%)"
                )
            
            if self.stop_loss and profit_ratio <= -self.stop_loss:
                return StopCheckResult(
                    should_close=True,
                    reason=StopReason.STOP_LOSS.value,
                    current_price=current_price,
                    entry_price=entry_price,
                    profit_ratio=profit_ratio,
                    hold_days=hold_days,
                    message=f"🛑 触发止损 ({profit_ratio*100:.2f}%)"
                )
        
        # 未触发
        return StopCheckResult(
            should_close=False,
            reason=StopReason.NOT_TRIGGERED.value,
            current_price=current_price,
            entry_price=entry_price,
            hold_days=hold_days
        )


class CombinedStopLoss(BaseStopLoss):
    """
    组合止损
    
    组合多种止损条件:
    - 固定止盈止损
    - 移动止盈止损
    - 时间止损
    """
    
    def __init__(self):
        self.stoplosss: List[BaseStopLoss] = []
    
    def add_stoploss(self, stoploss: BaseStopLoss):
        """添加止损条件"""
        self.stoplosss.append(stoploss)
    
    def check(
        self,
        entry_price: float,
        current_price: float,
        **kwargs
    ) -> StopCheckResult:
        """
        检查所有止损条件
        
        只要有一个触发，就平仓
        """
        for stoploss in self.stoplosss:
            result = stoploss.check(entry_price, current_price, **kwargs)
            
            if result.should_close:
                return result
        
        # 都没有触发
        profit_ratio = (current_price - entry_price) / entry_price
        
        return StopCheckResult(
            should_close=False,
            reason=StopReason.NOT_TRIGGERED.value,
            current_price=current_price,
            entry_price=entry_price,
            profit_ratio=profit_ratio
        )


# ==================== 导出 ====================

__all__ = [
    'FixedStopLoss',
    'TrailingStopLoss',
    'TimeStopLoss',
    'CombinedStopLoss',
    'StopCheckResult',
    'StopReason',
]
