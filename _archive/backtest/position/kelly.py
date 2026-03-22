"""
凯利公式仓位管理
Kelly Criterion Position Manager

功能:
- 基于凯利公式计算最优仓位
- 支持半凯利模式
- 支持多种Kelly变体

使用示例:
    from quant_factor_system.position.kelly import KellyManager
    
    manager = KellyManager(fraction=0.5)  # 半凯利
    
    result = manager.calculate_positions(
        returns=0.05,  # 预期收益率
        win_rate=0.55,  # 胜率
        win_loss_ratio=1.5,  # 盈亏比
        cash=1000000
    )
"""

import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class KellyVariant(Enum):
    """Kelly变体"""
    CLASSIC = 'classic'       # 经典凯利
    HALF = 'half'            # 半凯利
    THIRD = 'third'          # 三分之一凯利
    FRACTIONAL = 'fractional'  # 分数凯利


@dataclass
class KellyResult:
    """凯利仓位结果"""
    kelly_fraction: float  # Kelly分数
    optimal_weight: float  # 最优权重
    expected_growth: float  # 预期增长率
    win_rate: float       # 胜率
    win_loss_ratio: float  # 盈亏比
    risk_warning: str = ''  # 风险警告


class KellyManager:
    """
    凯利公式仓位管理
    
    凯利公式:
    f* = (bp - q) / b
    其中:
    - p = 胜率
    - q = 1 - p = 败率
    - b = 盈亏比 (盈/亏)
    - f* = 最优仓位比例
    """
    
    def __init__(
        self,
        fraction: float = 0.5,
        variant: str = 'fractional',
        max_weight: float = 0.5,
        min_weight: float = 0.01
    ):
        """
        初始化
        
        Args:
            fraction: Kelly分数 (1=全凯利, 0.5=半凯利, 0.33=三分之一)
            variant: Kelly变体
            max_weight: 最大权重
            min_weight: 最小权重
        """
        self.fraction = fraction
        self.variant = KellyVariant(variant)
        self.max_weight = max_weight
        self.min_weight = min_weight
    
    def calculate_kelly(
        self,
        win_rate: float,
        win_loss_ratio: float
    ) -> float:
        """
        计算凯利分数
        
        Args:
            win_rate: 胜率 (0-1)
            win_loss_ratio: 盈亏比 (盈/亏)
            
        Returns:
            Kelly分数
        """
        # 败率
        loss_rate = 1 - win_rate
        
        # Kelly公式
        if win_loss_ratio <= 0:
            return 0
        
        kelly = (win_rate * win_loss_ratio - loss_rate) / win_loss_ratio
        
        return kelly
    
    def calculate_positions(
        self,
        signals: Dict[str, float] = None,
        cash: float = 0,
        returns: float = None,
        win_rate: float = None,
        win_loss_ratio: float = None,
        prices: Dict[str, float] = None,
        current_positions: Dict[str, float] = None
    ) -> KellyResult:
        """
        计算凯利仓位
        
        Args:
            signals: 选股信号 (可选)
            cash: 可用现金
            returns: 预期收益率 (可选，如果提供则计算整体仓位)
            win_rate: 胜率 (可选)
            win_loss_ratio: 盈亏比 (可选)
            prices: 当前价格
            current_positions: 当前持仓
            
        Returns:
            KellyResult
        """
        # 1. 如果提供了胜率和盈亏比，直接计算
        if win_rate is not None and win_loss_ratio is not None:
            kelly = self.calculate_kelly(win_rate, win_loss_ratio)
            
            # 应用分数
            if self.variant == KellyVariant.CLASSIC:
                fraction = 1.0
            elif self.variant == KellyVariant.HALF:
                fraction = 0.5
            elif self.variant == KellyVariant.THIRD:
                fraction = 0.33
            else:  # FRACTIONAL
                fraction = self.fraction
            
            optimal_weight = max(0, kelly * fraction)
            
            # 限制范围
            optimal_weight = max(
                min(optimal_weight, self.max_weight),
                self.min_weight
            )
            
            # 计算预期增长率
            expected_growth = self._expected_growth(
                optimal_weight, win_rate, win_loss_ratio
            )
            
            # 风险警告
            risk_warning = self._get_risk_warning(kelly, fraction)
            
            return KellyResult(
                kelly_fraction=kelly,
                optimal_weight=optimal_weight,
                expected_growth=expected_growth,
                win_rate=win_rate,
                win_loss_ratio=win_loss_ratio,
                risk_warning=risk_warning
            )
        
        # 2. 如果提供了收益率数据，计算基于数据的Kelly
        if returns is not None:
            return self._calculate_from_returns(returns, cash)
        
        # 3. 默认返回等权结果
        return KellyResult(
            kelly_fraction=0,
            optimal_weight=1.0 / len(signals) if signals else 0,
            expected_growth=0,
            win_rate=0,
            win_loss_ratio=0,
            risk_warning=''
        )
    
    def _calculate_from_returns(
        self,
        returns: float,
        cash: float
    ) -> KellyResult:
        """从收益率数据计算Kelly"""
        # 使用经验公式
        # 简化: 假设收益服从正态分布
        mu = returns
        sigma = abs(returns) * 0.5  # 简化假设
        
        # 简化的Kelly计算
        if sigma <= 0:
            kelly = 0
        else:
            kelly = mu / (sigma ** 2)
        
        # 应用分数
        fraction = self._get_fraction()
        optimal_weight = max(0, kelly * fraction)
        
        # 限制范围
        optimal_weight = max(
            min(optimal_weight, self.max_weight),
            self.min_weight
        )
        
        return KellyResult(
            kelly_fraction=kelly,
            optimal_weight=optimal_weight,
            expected_growth=0,
            win_rate=0,
            win_loss_ratio=0,
            risk_warning=self._get_risk_warning(kelly, fraction)
        )
    
    def _get_fraction(self) -> float:
        """获取分数"""
        if self.variant == KellyVariant.CLASSIC:
            return 1.0
        elif self.variant == KellyVariant.HALF:
            return 0.5
        elif self.variant == KellyVariant.THIRD:
            return 0.33
        else:
            return self.fraction
    
    def _expected_growth(
        self,
        weight: float,
        win_rate: float,
        win_loss_ratio: float
    ) -> float:
        """
        计算预期增长率
        
        G = p * log(1 + b*f) + q * log(1 - f)
        """
        loss_rate = 1 - win_rate
        
        # 避免log(0)或log(负数)
        if weight <= 0:
            return 0
        
        if weight >= 1:
            return float('-inf')
        
        # Kelly增长率公式
        try:
            growth = (
                win_rate * np.log(1 + win_loss_ratio * weight) +
                loss_rate * np.log(1 - weight)
            )
            return growth
        except:
            return 0
    
    def _get_risk_warning(self, kelly: float, fraction: float) -> str:
        """获取风险警告"""
        if kelly <= 0:
            return '⚠️ 凯利分数<=0，不建议投资'
        
        if kelly > 1.0:
            return '⚠️ 凯利分数>1，可能过度集中'
        
        if kelly * fraction > 0.5:
            return '⚠️ 仓位过高，建议降低'
        
        return ''
    
    def calculate_optimal_f(
        self,
        p: float,
        b: float
    ) -> float:
        """
        计算最优凯利分数
        
        Args:
            p: 胜率
            b: 盈亏比
            
        Returns:
            f* 最优分数
        """
        q = 1 - p
        
        if b <= 0:
            return 0
        
        kelly = (p * b - q) / b
        
        return max(0, kelly)


class AdaptiveKellyManager:
    """
    自适应凯利管理器
    
    根据历史表现动态调整Kelly参数
    """
    
    def __init__(
        self,
        base_win_rate: float = 0.5,
        base_win_loss_ratio: float = 1.0,
        lookback: int = 252,
        fraction: float = 0.5
    ):
        """
        Args:
            base_win_rate: 基准胜率
            base_win_loss_ratio: 基准盈亏比
            lookback: 回看天数
            fraction: 分数
        """
        self.base_win_rate = base_win_rate
        self.base_win_loss_ratio = base_win_loss_ratio
        self.lookback = lookback
        self.fraction = fraction
        
        # 历史记录
        self.trade_history: List[Dict] = []
    
    def add_trade(
        self,
        symbol: str,
        entry_price: float,
        exit_price: float,
        direction: str = 'long'
    ):
        """添加交易记录"""
        if direction == 'long':
            ret = (exit_price - entry_price) / entry_price
        else:
            ret = (entry_price - exit_price) / entry_price
        
        self.trade_history.append({
            'symbol': symbol,
            'return': ret,
            'win': ret > 0
        })
        
        # 只保留回看期内的记录
        if len(self.trade_history) > self.lookback:
            self.trade_history.pop(0)
    
    def calculate_adaptive_kelly(self) -> Tuple[float, float, float]:
        """
        计算自适应Kelly
        
        Returns:
            (win_rate, win_loss_ratio, kelly)
        """
        if len(self.trade_history) < 20:
            return self.base_win_rate, self.base_win_loss_ratio, 0
        
        # 计算实际胜率
        wins = [t for t in self.trade_history if t['win']]
        win_rate = len(wins) / len(self.trade_history)
        
        # 计算实际盈亏比
        win_returns = [abs(t['return']) for t in wins]
        loss_returns = [abs(t['return']) for t in self.trade_history if not t['win']]
        
        if win_returns and loss_returns:
            avg_win = np.mean(win_returns)
            avg_loss = np.mean(loss_returns)
            win_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 1.0
        else:
            win_loss_ratio = self.base_win_loss_ratio
        
        # 计算Kelly
        kelly = (win_rate * win_loss_ratio - (1 - win_rate)) / win_loss_ratio
        
        # 应用分数
        kelly = max(0, kelly * self.fraction)
        
        return win_rate, win_loss_ratio, kelly


# ==================== 导出 ====================

__all__ = [
    'KellyManager',
    'KellyResult',
    'KellyVariant',
    'AdaptiveKellyManager',
]
