"""
常用因子定义
Common Factor Definitions
"""

import pandas as pd
import numpy as np
from ...core.base import Factor


class MomentumFactor(Factor):
    """
    动量因子
    衡量过去N个月的收益表现
    """
    
    def __init__(self, period: int = 12, description: str = "过去N个月累计收益"):
        """
        初始化动量因子
        
        Args:
            period: 回看期（月）
            description: 因子描述
        """
        super().__init__("Momentum", description)
        self.period = period
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算动量因子
        
        Args:
            data: 需要包含 'close' 列（收盘价）
            
        Returns:
            动量因子值
        """
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        
        # 计算累计收益
        momentum = close.pct_change(periods=self.period)
        
        self.values = momentum
        return momentum


class ValueFactor(Factor):
    """
    价值因子
    基于市盈率(PE)或市净率(PB)
    """
    
    def __init__(self, metric: str = "pe", description: str = "估值因子(PE/PB)"):
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
            价值因子值（负值，越低越好）
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
    """
    
    def __init__(self, metric: str = "roe", description: str = "盈利质量因子(ROE/ROA)"):
        """
        初始化质量因子
        
        Args:
            metric: 质量指标 ('roe' 或 'roa')
            description: 因子描述
        """
        super().__init__("Quality", description)
        self.metric = metric
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算质量因子
        
        Args:
            data: 需要包含 'roe' 或 'roa' 列
            
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
    衡量收益的波动程度
    """
    
    def __init__(self, period: int = 20, description: str = "收益波动率"):
        """
        初始化波动率因子
        
        Args:
            period: 回看期（天）
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
            波动率因子值（负值，低波动是优势）
        """
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        # 计算日收益率
        returns = data['close'].pct_change()
        
        # 计算滚动波动率
        volatility = returns.rolling(window=self.period).std()
        
        # 波动率因子：低波动是优势，取负值
        volatility_factor = -volatility
        
        self.values = volatility_factor
        return volatility_factor


class GrowthFactor(Factor):
    """
    成长因子
    基于营收或利润增长率
    """
    
    def __init__(self, metric: str = "revenue", period: int = 4, 
                 description: str = "营收/利润增长率"):
        """
        初始化成长因子
        
        Args:
            metric: 成长指标 ('revenue' 或 'profit')
            period: 回看期（季度）
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
            data: 需要包含 'revenue' 或 'profit' 列
            
        Returns:
            成长因子值
        """
        if self.metric not in data.columns:
            raise ValueError(f"数据必须包含 '{self.metric}' 列")
        
        # 计算同比增长率
        growth = data[self.metric].pct_change(periods=self.period)
        
        # 处理无效值
        growth = growth.replace([np.inf, -np.inf], np.nan)
        growth = growth.fillna(growth.median())
        
        self.values = growth
        return growth


class SizeFactor(Factor):
    """
    市值因子
    基于总市值
    """
    
    def __init__(self, description: str = "市值因子"):
        """
        初始化市值因子
        """
        super().__init__("Size", description)
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算市值因子
        
        Args:
            data: 需要包含 'market_cap' 列
            
        Returns:
            市值因子值（小市值是优势，取负值）
        """
        if 'market_cap' not in data.columns:
            raise ValueError("数据必须包含 'market_cap' 列")
        
        # 小市值是优势，取负值
        size = -data['market_cap']
        
        # 处理无效值
        size = size.replace([np.inf, -np.inf], np.nan)
        size = size.fillna(size.median())
        
        self.values = size
        return size


class LiquidityFactor(Factor):
    """
    流动性因子
    基于成交额或换手率
    """
    
    def __init__(self, period: int = 20, description: str = "流动性因子"):
        """
        初始化流动性因子
        
        Args:
            period: 回看期（天）
            description: 因子描述
        """
        super().__init__("Liquidity", description)
        self.period = period
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算流动性因子
        
        Args:
            data: 需要包含 'volume' 或 'turnover' 列
            
        Returns:
            流动性因子值（高流动性是优势）
        """
        if 'volume' not in data.columns:
            raise ValueError("数据必须包含 'volume' 列")
        
        # 计算滚动平均成交量
        avg_volume = data['volume'].rolling(window=self.period).mean()
        
        # 流动性因子
        liquidity = avg_volume
        
        self.values = liquidity
        return liquidity
