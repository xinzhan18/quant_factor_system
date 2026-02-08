"""
常用因子定义
Common Factor Definitions

支持 MultiIndex（多股票数据）
"""

import pandas as pd
import numpy as np
from typing import Optional
from ...core.base import Factor


class MomentumFactor(Factor):
    """
    动量因子
    衡量过去N个月的收益表现
    
    支持 MultiIndex 数据，会按股票分组计算
    """
    
    def __init__(self, period: int = 20, description: str = "动量因子"):
        """
        初始化动量因子
        
        Args:
            period: 回看期（交易日）
            description: 因子描述
        """
        super().__init__("Momentum", description)
        self.period = period
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算动量因子
        
        Args:
            data: 需要包含 'close' 列
            
        Returns:
            动量因子值（按组计算）
        """
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        
        # 检测是否为 MultiIndex
        if isinstance(close.index, pd.MultiIndex):
            # 按股票分组计算动量
            momentum = close.groupby(level='symbol').pct_change(periods=self.period)
        else:
            # 单股票数据
            momentum = close.pct_change(periods=self.period)
        
        momentum = momentum.replace([np.inf, -np.inf], np.nan)
        
        self.values = momentum
        return momentum


class ValueFactor(Factor):
    """
    价值因子
    基于市盈率(PE)或市净率(PB)
    
    支持 MultiIndex 数据
    """
    
    def __init__(self, metric: str = "pe", description: str = "价值因子"):
        """
        初始化价值因子
        
        Args:
            metric: 估值指标 ('pe' 或 'pb')
            description: 因子描述
        """
        super().__init__("Value", description)
        self.metric = metric
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算价值因子
        
        Args:
            data: 需要包含 'pe' 或 'pb' 列
            
        Returns:
            价值因子值
        """
        if self.metric not in data.columns:
            raise ValueError(f"数据必须包含 '{self.metric}' 列")
        
        # 价值因子：低估值是优势，取负值
        value = -data[self.metric]
        
        # 处理无效值
        value = value.replace([np.inf, -np.inf], np.nan)
        value = value.fillna(value.median())
        
        self.values = value
        return value


class QualityFactor(Factor):
    """
    质量因子
    基于ROE、ROA等盈利质量指标
    
    支持 MultiIndex 数据
    """
    
    def __init__(self, metric: str = "roe", description: str = "质量因子"):
        """
        初始化质量因子
        
        Args:
            metric: 质量指标 ('roe', 'roa', 'gross_margin')
            description: 因子描述
        """
        super().__init__("Quality", description)
        self.metric = metric
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算质量因子
        
        Args:
            data: 需要包含对应指标列
            
        Returns:
            质量因子值
        """
        if self.metric not in data.columns:
            raise ValueError(f"数据必须包含 '{self.metric}' 列")
        
        quality = data[self.metric]
        
        # 处理无效值
        quality = quality.replace([np.inf, -np.inf], np.nan)
        quality = quality.fillna(quality.median())
        
        self.values = quality
        return quality


class VolatilityFactor(Factor):
    """
    波动率因子
    衡量股票收益的波动程度
    
    支持 MultiIndex 数据
    """
    
    def __init__(self, period: int = 20, description: str = "波动率因子"):
        """
        初始化波动率因子
        
        Args:
            period: 计算周期
            description: 因子描述
        """
        super().__init__("Volatility", description)
        self.period = period
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算波动率因子
        
        Args:
            data: 需要包含 'close' 列
            
        Returns:
            波动率因子值（波动率越低越好，取负值）
        """
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        
        # 计算收益率
        returns = close.pct_change()
        
        # 检测是否为 MultiIndex
        if isinstance(returns.index, pd.MultiIndex):
            # 按股票分组计算滚动波动率
            volatility = returns.groupby(level='symbol').rolling(
                window=self.period, min_periods=5
            ).std().droplevel('symbol') if hasattr(returns, 'droplevel') else returns
            # 对于 MultiIndex，使用 groupby+transform
            volatility = returns.groupby(level='symbol').transform(
                lambda x: x.rolling(window=self.period, min_periods=5).std()
            )
        else:
            # 单股票数据
            volatility = returns.rolling(window=self.period, min_periods=5).std()
        
        # 波动率越低越好，取负值
        volatility = -volatility.replace([np.inf, -np.inf], np.nan)
        volatility = volatility.fillna(volatility.median())
        
        self.values = volatility
        return volatility


class GrowthFactor(Factor):
    """
    成长因子
    基于营收、利润增长率
    
    支持 MultiIndex 数据
    """
    
    def __init__(self, metric: str = "revenue", period: int = 4, description: str = "成长因子"):
        """
        初始化成长因子
        
        Args:
            metric: 成长指标 ('revenue', 'profit', 'eps')
            period: 回看季度数
            description: 因子描述
        """
        super().__init__("Growth", description)
        self.metric = metric
        self.period = period
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算成长因子
        
        Args:
            data: 需要包含对应指标列
            
        Returns:
            成长因子值
        """
        if self.metric not in data.columns:
            raise ValueError(f"数据必须包含 '{self.metric}' 列")
        
        metric = data[self.metric]
        
        # 计算增长率
        if isinstance(metric.index, pd.MultiIndex):
            growth = metric.groupby(level='symbol').pct_change(periods=self.period)
        else:
            growth = metric.pct_change(periods=self.period)
        
        growth = growth.replace([np.inf, -np.inf], np.nan)
        growth = growth.fillna(growth.median())
        
        self.values = growth
        return growth


class SizeFactor(Factor):
    """
    规模因子
    基于市值大小
    
    支持 MultiIndex 数据
    """
    
    def __init__(self, description: str = "规模因子"):
        """
        初始化规模因子
        """
        super().__init__("Size", description)
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算规模因子
        
        Args:
            data: 需要包含 'market_cap' 列
            
        Returns:
            规模因子值（市值的对数）
        """
        if 'market_cap' not in data.columns:
            raise ValueError("数据必须包含 'market_cap' 列")
        
        size = np.log(data['market_cap'])
        
        # 处理无效值
        size = size.replace([np.inf, -np.inf], np.nan)
        size = size.fillna(size.median())
        
        self.values = size
        return size


class LiquidityFactor(Factor):
    """
    流动性因子
    基于成交量/成交额
    
    支持 MultiIndex 数据
    """
    
    def __init__(self, period: int = 20, description: str = "流动性因子"):
        """
        初始化流动性因子
        
        Args:
            period: 计算周期
            description: 因子描述
        """
        super().__init__("Liquidity", description)
        self.period = period
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算流动性因子
        
        Args:
            data: 需要包含 'volume' 列
            
        Returns:
            流动性因子值（成交量/成交额的对数）
        """
        if 'volume' not in data.columns:
            raise ValueError("数据必须包含 'volume' 列")
        
        volume = data['volume']
        
        # 计算平均成交量
        if isinstance(volume.index, pd.MultiIndex):
            liquidity = volume.groupby(level='symbol').transform(
                lambda x: x.rolling(window=self.period, min_periods=5).mean()
            )
        else:
            liquidity = volume.rolling(window=self.period, min_periods=5).mean()
        
        liquidity = np.log(liquidity)
        
        # 处理无效值
        liquidity = liquidity.replace([np.inf, -np.inf], np.nan)
        liquidity = liquidity.fillna(liquidity.median())
        
        self.values = liquidity
        return liquidity


class EarningsYieldFactor(Factor):
    """
    盈利收益率因子
    基于 PE 的倒数
    
    支持 MultiIndex 数据
    """
    
    def __init__(self, description: str = "盈利收益率因子"):
        """
        初始化盈利收益率因子
        """
        super().__init__("EarningsYield", description)
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算盈利收益率因子
        
        Args:
            data: 需要包含 'pe' 列
            
        Returns:
            盈利收益率因子值（1/PE）
        """
        if 'pe' not in data.columns:
            raise ValueError("数据必须包含 'pe' 列")
        
        # PE 的倒数
        ey = 1.0 / data['pe']
        
        # 处理无效值
        ey = ey.replace([np.inf, -np.inf], np.nan)
        ey = ey.fillna(ey.median())
        
        self.values = ey
        return ey
