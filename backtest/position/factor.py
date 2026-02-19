"""
因子值加权仓位管理
Factor Weighted Position Manager

功能:
- 根据因子值大小分配权重
- 因子值越大，权重越大
- 支持多种加权方法

使用示例:
    from quant_factor_system.position.factor import FactorWeightedManager
    
    manager = FactorWeightedManager(
        method='linear',  # linear/rank/exponential
        min_weight=0.01,
        max_weight=0.20
    )
    
    positions = manager.calculate_positions(
        signals={'SH600000': 0.5, 'SH600001': 0.3},
        cash=1000000
    )
"""

import pandas as pd
import numpy as np
from typing import Dict, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class WeightingMethod(Enum):
    """加权方法"""
    LINEAR = 'linear'       # 线性加权
    RANK = 'rank'           # 排名加权
    EXPONENTIAL = 'exp'     # 指数加权
    INVERSE_RANK = 'inv_rank'  # 逆排名加权


@dataclass
class FactorPositionResult:
    """因子加权仓位结果"""
    positions: Dict[str, dict]  # 包含weight, quantity, value, factor_value
    total_weight: float
    total_value: float
    weights_used: Dict[str, float]  # 实际使用的权重
    method: str


class FactorWeightedManager:
    """
    因子值加权仓位管理
    
    根据因子值大小分配权重:
    - 线性加权: 因子值越大，权重越大
    - 排名加权: 按排名分配权重
    - 指数加权: 排名越高，权重指数增长
    """
    
    def __init__(
        self,
        method: str = 'linear',
        min_weight: float = 0.01,
        max_weight: float = 0.20,
        lot_size: int = 100,
        normalize: bool = True
    ):
        """
        初始化
        
        Args:
            method: 加权方法 (linear/rank/exp/inv_rank)
            min_weight: 最小权重
            max_weight: 最大权重
            lot_size: 最小交易单位
            normalize: 是否归一化权重
        """
        self.method = WeightingMethod(method)
        self.min_weight = min_weight
        self.max_weight = max_weight
        self.lot_size = lot_size
        self.normalize = normalize
    
    def calculate_weights(
        self,
        signals: Dict[str, float]
    ) -> Tuple[Dict[str, float], Dict[str, float]]:
        """
        计算权重
        
        Args:
            signals: {symbol: factor_value}
            
        Returns:
            (raw_weights, normalized_weights)
        """
        if not signals:
            return {}, {}
        
        # 1. 排序
        sorted_signals = dict(sorted(signals.items(), key=lambda x: x[1], reverse=True))
        
        # 2. 根据方法计算权重
        if self.method == WeightingMethod.LINEAR:
            raw_weights = self._linear_weights(sorted_signals)
        elif self.method == WeightingMethod.RANK:
            raw_weights = self._rank_weights(sorted_signals)
        elif self.method == WeightingMethod.EXPONENTIAL:
            raw_weights = self._exponential_weights(sorted_signals)
        elif self.method == WeightingMethod.INVERSE_RANK:
            raw_weights = self._inverse_rank_weights(sorted_signals)
        else:
            raw_weights = self._linear_weights(sorted_signals)
        
        # 3. 归一化
        if self.normalize and raw_weights:
            total = sum(raw_weights.values())
            if total > 0:
                normalized = {k: v / total for k, v in raw_weights.items()}
            else:
                normalized = raw_weights
        else:
            normalized = raw_weights
        
        # 4. 限制权重范围
        normalized = self._clip_weights(normalized)
        
        return raw_weights, normalized
    
    def _linear_weights(self, sorted_signals: Dict[str, float]) -> Dict[str, float]:
        """线性加权"""
        n = len(sorted_signals)
        if n == 0:
            return {}
        
        # 因子值范围
        values = list(sorted_signals.values())
        min_val = min(values)
        max_val = max(values)
        val_range = max_val - min_val
        
        if val_range == 0:
            # 因子值相同，等权
            return {k: 1.0 for k in sorted_signals.keys()}
        
        # 线性映射到权重
        weights = {}
        for symbol, value in sorted_signals.items():
            # 归一化到0.1-1.0
            normalized = 0.1 + 0.9 * (value - min_val) / val_range
            weights[symbol] = normalized
        
        return weights
    
    def _rank_weights(self, sorted_signals: Dict[str, float]) -> Dict[str, float]:
        """排名加权"""
        n = len(sorted_signals)
        if n == 0:
            return {}
        
        weights = {}
        for i, (symbol, value) in enumerate(sorted_signals.items()):
            # 排名1获得最高权重
            rank = i + 1
            # 线性下降: 1/n 到 1
            weight = 1.0 / rank
            weights[symbol] = weight
        
        return weights
    
    def _exponential_weights(self, sorted_signals: Dict[str, float]) -> Dict[str, float]:
        """指数加权"""
        n = len(sorted_signals)
        if n == 0:
            return {}
        
        weights = {}
        for i, (symbol, value) in enumerate(sorted_signals.items()):
            # 排名1获得最高权重，指数衰减
            rank = i + 1
            # 2^(1-rank) 衰减
            weight = 2.0 ** (1 - rank)
            weights[symbol] = weight
        
        return weights
    
    def _inverse_rank_weights(self, sorted_signals: Dict[str, float]) -> Dict[str, float]:
        """逆排名加权 (因子值越小，权重越大)"""
        n = len(sorted_signals)
        if n == 0:
            return {}
        
        weights = {}
        for i, (symbol, value) in enumerate(sorted_signals.items()):
            # 排名1获得最低权重
            rank = i + 1
            # 反向: n 到 1
            weight = n - rank + 1
            weights[symbol] = weight
        
        return weights
    
    def _clip_weights(self, weights: Dict[str, float]) -> Dict[str, float]:
        """限制权重范围"""
        if not weights:
            return {}
        
        sum(weights.values())
        
        clipped = {}
        for symbol, weight in weights.items():
            # 限制单只权重
            clipped_weight = max(min(weight, self.max_weight), self.min_weight)
            clipped[symbol] = clipped_weight
        
        return clipped
    
    def calculate_positions(
        self,
        signals: Dict[str, float],
        cash: float,
        prices: Dict[str, float] = None,
        current_positions: Dict[str, float] = None
    ) -> FactorPositionResult:
        """
        计算仓位
        
        Args:
            signals: {symbol: factor_value}
            cash: 可用现金
            prices: {symbol: price}
            current_positions: {symbol: quantity}
            
        Returns:
            FactorPositionResult
        """
        # 1. 计算权重
        raw_weights, weights = self.calculate_weights(signals)
        
        if not weights:
            return FactorPositionResult(
                positions={},
                total_weight=0,
                total_value=0,
                weights_used={},
                method=self.method.value
            )
        
        # 2. 计算每个股票的仓位
        positions = {}
        total_value = 0
        
        for symbol, weight in weights.items():
            # 目标市值
            target_value = cash * weight
            
            # 价格
            price = prices.get(symbol, 0) if prices else 0
            
            # 计算数量
            if price > 0:
                quantity = int(target_value / price / self.lot_size) * self.lot_size
            else:
                quantity = 0
            
            actual_value = quantity * price
            total_value += actual_value
            
            positions[symbol] = {
                'weight': weight,
                'quantity': quantity,
                'price': price,
                'value': actual_value,
                'factor_value': signals.get(symbol, 0),
                'raw_weight': raw_weights.get(symbol, 0)
            }
        
        # 3. 计算剩余现金
        cash - total_value
        
        logger.info(f"✅ 因子加权仓位计算: {len(positions)}只股票, 方法: {self.method.value}")
        
        return FactorPositionResult(
            positions=positions,
            total_weight=sum(weights.values()),
            total_value=total_value,
            weights_used=weights,
            method=self.method.value
        )
    
    def calculate_rebalance(
        self,
        target_result: FactorPositionResult,
        current_positions: Dict[str, float],
        prices: Dict[str, float]
    ) -> Dict[str, Tuple[int, float]]:
        """
        计算调仓指令
        
        Returns:
            {symbol: (change_qty, change_value)}
        """
        trades = {}
        
        for symbol, target in target_result.positions.items():
            current_qty = current_positions.get(symbol, 0)
            target_qty = target['quantity']
            
            change_qty = target_qty - current_qty
            price = prices.get(symbol, 0)
            change_value = change_qty * price
            
            if change_qty != 0:
                trades[symbol] = (change_qty, change_value)
        
        return trades


class VolatilityWeightedManager:
    """
    波动率加权仓位管理
    
    根据波动率调整仓位:
    - 波动率高的股票，仓位低
    - 波动率低的股票，仓位高
    """
    
    def __init__(
        self,
        base_weight: float = 0.05,
        volatility_window: int = 20,
        risk_aversion: float = 1.0
    ):
        """
        Args:
            base_weight: 基础权重
            volatility_window: 波动率计算窗口
            risk_aversion: 风险厌恶系数
        """
        self.base_weight = base_weight
        self.volatility_window = volatility_window
        self.risk_aversion = risk_aversion
    
    def calculate_volatility(
        self,
        prices: Dict[str, pd.Series]
    ) -> Dict[str, float]:
        """
        计算波动率
        
        Args:
            prices: {symbol: price_series}
            
        Returns:
            {symbol: volatility}
        """
        volatilities = {}
        
        for symbol, price_series in prices.items():
            if len(price_series) < 2:
                volatilities[symbol] = 1.0
                continue
            
            # 计算收益率
            returns = price_series.pct_change().dropna()
            
            if len(returns) == 0:
                volatilities[symbol] = 1.0
                continue
            
            # 年化波动率
            vol = returns.std() * np.sqrt(252)
            volatilities[symbol] = vol
        
        return volatilities
    
    def calculate_weights(
        self,
        signals: Dict[str, float],
        volatilities: Dict[str, float]
    ) -> Dict[str, float]:
        """
        计算波动率加权权重
        
        Weight = base_weight / (volatility * risk_aversion)
        """
        weights = {}
        
        for symbol, signal in signals.items():
            vol = volatilities.get(symbol, 1.0)
            
            # 波动率倒数作为权重
            weight = self.base_weight / (vol * self.risk_aversion)
            
            # 限制范围
            weight = max(min(weight, 0.2), 0.01)
            
            weights[symbol] = weight
        
        return weights


# ==================== 导出 ====================

__all__ = [
    'FactorWeightedManager',
    'FactorPositionResult',
    'WeightingMethod',
    'VolatilityWeightedManager',
]
