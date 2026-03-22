"""
等权仓位管理模块
Equal Weight Position Manager

功能:
- 每个股票分配相同权重
- Top N选股后的等权分配
- 最小交易单位处理

使用示例:
    from quant_factor_system.position.equal import EqualWeightManager
    
    manager = EqualWeightManager(
        max_positions=20,
        min_weight=0.02,
        max_weight=0.15,
        lot_size=100
    )
    
    positions = manager.calculate_positions(
        signals={'SH600000': 0.5, 'SH600001': 0.3},
        cash=1000000
    )
"""

import pandas as pd
from typing import Dict, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


@dataclass
class Position:
    """单个持仓"""
    symbol: str
    weight: float           # 目标权重
    quantity: int = 0      # 持仓数量
    price: float = 0.0     # 当前价格
    value: float = 0.0     # 持仓市值
    
    def __post_init__(self):
        self.value = self.quantity * self.price


@dataclass
class PositionResult:
    """仓位计算结果"""
    positions: Dict[str, Position]
    total_weight: float
    total_value: float
    cash_remaining: float
    top_n: int
    
    def to_dataframe(self) -> pd.DataFrame:
        """转换为DataFrame"""
        if not self.positions:
            return pd.DataFrame()
        
        data = []
        for symbol, pos in self.positions.items():
            data.append({
                'symbol': symbol,
                'weight': pos.weight,
                'quantity': pos.quantity,
                'price': pos.price,
                'value': pos.value
            })
        
        return pd.DataFrame(data)
    
    def summary(self) -> Dict:
        """摘要"""
        return {
            'total_weight': self.total_weight,
            'total_value': self.total_value,
            'cash_remaining': self.cash_remaining,
            'num_positions': len(self.positions),
            'top_n': self.top_n
        }


class PositionManager(ABC):
    """仓位管理抽象基类"""
    
    @abstractmethod
    def calculate_positions(
        self,
        signals: Dict[str, float],  # symbol -> factor_value/score
        cash: float,
        current_positions: Dict[str, float] = None,
        prices: Dict[str, float] = None,
        selection_date: str = None
    ) -> PositionResult:
        """
        计算目标仓位
        
        Args:
            signals: 选股信号 (因子值或得分)
            cash: 可用现金
            current_positions: 当前持仓 {symbol: quantity}
            prices: 当前价格 {symbol: price}
            selection_date: 选股日期
            
        Returns:
            PositionResult
        """


class EqualWeightManager(PositionManager):
    """
    等权仓位管理
    
    每个股票分配相同权重
    
    使用示例:
        manager = EqualWeightManager(max_positions=20)
        result = manager.calculate_positions(
            signals={'SH600000': 0.5, 'SH600001': 0.3},
            cash=1000000
        )
    """
    
    def __init__(
        self,
        max_positions: int = 20,
        min_weight: float = 0.02,
        max_weight: float = 0.15,
        lot_size: int = 100,  # A股最小交易单位
        allow_fraction: bool = False,  # 是否允许分数股
        select_by: str = 'value'  # 'value'按因子值排序, 'list'按传入顺序
    ):
        """
        初始化
        
        Args:
            max_positions: 最大持仓数量
            min_weight: 最小权重
            max_weight: 最大权重
            lot_size: 最小交易单位 (A股100股)
            allow_fraction: 是否允许分数股
            select_by: 选择排序方式
        """
        self.max_positions = max_positions
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.lot_size = lot_size
        self.allow_fraction = allow_fraction
        self.select_by = select_by
    
    def calculate_positions(
        self,
        signals: Dict[str, float],
        cash: float,
        current_positions: Dict[str, float] = None,
        prices: Dict[str, float] = None,
        selection_date: str = None
    ) -> PositionResult:
        """
        计算等权仓位
        """
        if not signals:
            logger.warning("选股信号为空")
            return PositionResult(
                positions={},
                total_weight=0,
                total_value=0,
                cash_remaining=cash,
                top_n=0
            )
        
        # 1. 过滤有价格的股票
        valid_signals = self._filter_by_prices(signals, prices)
        
        if not valid_signals:
            logger.warning("没有有效的选股信号")
            return PositionResult(
                positions={},
                total_weight=0,
                total_value=0,
                cash_remaining=cash,
                top_n=0
            )
        
        # 2. 按因子值排序
        sorted_signals = self._sort_signals(valid_signals, prices)
        
        # 3. Top N
        top_signals = dict(list(sorted_signals.items())[:self.max_positions])
        
        # 4. 计算等权
        n = len(top_signals)
        base_weight = 1.0 / n if n > 0 else 0
        
        # 5. 计算每个股票的仓位
        # 先计算并裁剪权重
        weights = {}
        for symbol in top_signals:
            weights[symbol] = max(min(base_weight, self.max_weight), self.min_weight)

        # 归一化权重，确保总和为1.0
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {s: w / total_weight for s, w in weights.items()}

        positions = {}
        total_value = 0

        for symbol, weight in weights.items():
            price = prices.get(symbol, 0) if prices else 0

            # 计算目标市值
            target_value = cash * weight
            
            # 计算数量
            if price > 0 and not self.allow_fraction:
                quantity = int(target_value / price / self.lot_size) * self.lot_size
            else:
                quantity = target_value / price if price > 0 else 0
            
            actual_value = quantity * price
            total_value += actual_value
            
            positions[symbol] = Position(
                symbol=symbol,
                weight=weight,
                quantity=quantity,
                price=price,
                value=actual_value
            )
        
        # 6. 计算剩余现金
        cash_remaining = cash - total_value
        
        logger.info(f"✅ 等权仓位计算: {n}只股票, 总市值: {total_value:.2f}")
        
        return PositionResult(
            positions=positions,
            total_weight=1.0,
            total_value=total_value,
            cash_remaining=cash_remaining,
            top_n=n
        )
    
    def _filter_by_prices(
        self,
        signals: Dict[str, float],
        prices: Dict[str, float] = None
    ) -> Dict[str, float]:
        """过滤有价格的股票"""
        if prices is None:
            return signals
        
        return {
            s: v for s, v in signals.items()
            if prices.get(s, 0) > 0
        }
    
    def _sort_signals(
        self,
        signals: Dict[str, float],
        prices: Dict[str, float] = None
    ) -> Dict[str, float]:
        """排序信号"""
        if self.select_by == 'value':
            # 按因子值降序排序
            return dict(sorted(signals.items(), key=lambda x: x[1], reverse=True))
        else:
            # 按传入顺序
            return signals
    
    def calculate_rebalance(
        self,
        target_result: PositionResult,
        current_positions: Dict[str, float],
        prices: Dict[str, float]
    ) -> Dict[str, Tuple[int, float]]:
        """
        计算调仓指令
        
        Args:
            target_result: 目标仓位
            current_positions: 当前持仓 {symbol: quantity}
            prices: 当前价格
            
        Returns:
            {symbol: (change_quantity, change_value)}
        """
        trades = {}
        
        for symbol, target_pos in target_result.positions.items():
            current_qty = current_positions.get(symbol, 0)
            target_qty = target_pos.quantity
            
            change_qty = target_qty - current_qty
            price = prices.get(symbol, 0)
            change_value = change_qty * price
            
            if change_qty != 0:
                trades[symbol] = (change_qty, change_value)
        
        return trades


class FixedWeightManager(PositionManager):
    """
    固定权重仓位管理
    
    根据预设权重分配仓位
    """
    
    def __init__(
        self,
        weights: Dict[str, float],
        lot_size: int = 100
    ):
        """
        Args:
            weights: 预设权重 {symbol: weight}
            lot_size: 最小交易单位
        """
        self.weights = weights
        self.lot_size = lot_size
    
    def calculate_positions(
        self,
        signals: Dict[str, float],
        cash: float,
        current_positions: Dict[str, float] = None,
        prices: Dict[str, float] = None,
        selection_date: str = None
    ) -> PositionResult:
        """计算固定权重仓位"""
        positions = {}
        total_value = 0
        
        for symbol, weight in self.weights.items():
            price = prices.get(symbol, 0) if prices else 0
            
            target_value = cash * weight
            
            if price > 0:
                quantity = int(target_value / price / self.lot_size) * self.lot_size
            else:
                quantity = 0
            
            actual_value = quantity * price
            total_value += actual_value
            
            positions[symbol] = Position(
                symbol=symbol,
                weight=weight,
                quantity=quantity,
                price=price,
                value=actual_value
            )
        
        return PositionResult(
            positions=positions,
            total_weight=sum(self.weights.values()),
            total_value=total_value,
            cash_remaining=cash - total_value,
            top_n=len(positions)
        )


# ==================== 导出 ====================

__all__ = [
    'Position',
    'PositionResult',
    'PositionManager',
    'EqualWeightManager',
    'FixedWeightManager',
]
