"""
收益率因子与均值回归因子
Return & Mean Reversion Factors

收益率因子（动量与反转）:
- ret_1d → 1日收益率
- ret_5d → 5日收益率（适合周度调仓）
- ret_20d → 1月收益率（中期趋势）
- ret_60d → 3月收益率（长期季度动量）

均值回归因子:
- dist_ma10/20/60 → 价格偏离均线程度
- zscore_60 → 60日标准分 (Close - Mean60) / Std60
"""

import pandas as pd
import numpy as np
from ...core.base import Factor


# ==================== 收益率因子 ====================

class Return1dFactor(Factor):
    """
    1日收益率因子
    捕捉短期价格变动，适合高频调仓策略
    
    特点:
    - 对短期新闻和事件敏感
    - 可能存在反转效应
    - 换手率高
    """
    
    def __init__(self, description: str = "1日收益率因子"):
        """
        初始化
        
        Args:
            description: 因子描述
        """
        super().__init__("Return_1d", description)
        self.period = 1
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算1日收益率
        
        Args:
            data: 需要包含 'close' 列
            
        Returns:
            1日收益率序列
        """
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        
        if isinstance(close.index, pd.MultiIndex):
            ret = close.groupby(level='symbol').pct_change(periods=self.period)
        else:
            ret = close.pct_change(periods=self.period)
        
        ret = ret.replace([np.inf, -np.inf], np.nan)
        
        self.values = ret
        return ret


class Return5dFactor(Factor):
    """
    5日收益率因子
    适合周度调仓策略，捕捉周度价格动能
    
    特点:
    - 平滑日度噪声
    - 适合周频策略
    - 动量/反转效应皆可能
    """
    
    def __init__(self, description: str = "5日收益率因子"):
        super().__init__("Return_5d", description)
        self.period = 5
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """计算5日收益率"""
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        
        if isinstance(close.index, pd.MultiIndex):
            ret = close.groupby(level='symbol').pct_change(periods=self.period)
        else:
            ret = close.pct_change(periods=self.period)
        
        ret = ret.replace([np.inf, -np.inf], np.nan)
        
        self.values = ret
        return ret


class Return20dFactor(Factor):
    """
    20日收益率因子（1月收益率）
    捕捉中期价格趋势，适合月频调仓
    
    特点:
    - 中期趋势信号
    - 适用于月度策略
    - 动量效应通常较强
    """
    
    def __init__(self, description: str = "20日收益率因子（1月）"):
        super().__init__("Return_20d", description)
        self.period = 20
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """计算20日收益率"""
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        
        if isinstance(close.index, pd.MultiIndex):
            ret = close.groupby(level='symbol').pct_change(periods=self.period)
        else:
            ret = close.pct_change(periods=self.period)
        
        ret = ret.replace([np.inf, -np.inf], np.nan)
        
        self.values = ret
        return ret


class Return60dFactor(Factor):
    """
    60日收益率因子（3月收益率）
    捕捉长期季度动量，适合低频调仓
    
    特点:
    - 长期趋势信号
    - 季度调仓适用
    - 较强的动量持续性
    """
    
    def __init__(self, description: str = "60日收益率因子（3月）"):
        super().__init__("Return_60d", description)
        self.period = 60
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """计算60日收益率"""
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        
        if isinstance(close.index, pd.MultiIndex):
            ret = close.groupby(level='symbol').pct_change(periods=self.period)
        else:
            ret = close.pct_change(periods=self.period)
        
        ret = ret.replace([np.inf, -np.inf], np.nan)
        
        self.values = ret
        return ret


# ==================== 均值回归因子 ====================

class DistMA10Factor(Factor):
    """
    价格偏离10日均线程度
    捕捉短期价格偏离，判断是否超买/超卖
    
    公式: (Close - MA10) / MA10
    """
    
    def __init__(self, description: str = "价格偏离10日均线程度"):
        super().__init__("Dist_MA10", description)
        self.period = 10
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算偏离10日均线程度
        
        Formula: (Close - MA10) / MA10
        """
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        
        if isinstance(close.index, pd.MultiIndex):
            # 按股票分组计算
            ma = close.groupby(level='symbol').transform(
                lambda x: x.rolling(window=self.period, min_periods=5).mean()
            )
        else:
            ma = close.rolling(window=self.period, min_periods=5).mean()
        
        # 计算偏离程度
        dist = (close - ma) / ma
        
        dist = dist.replace([np.inf, -np.inf], np.nan)
        
        self.values = dist
        return dist


class DistMA20Factor(Factor):
    """
    价格偏离20日均线程度
    捕捉中期价格偏离
    
    公式: (Close - MA20) / MA20
    """
    
    def __init__(self, description: str = "价格偏离20日均线程度"):
        super().__init__("Dist_MA20", description)
        self.period = 20
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """计算偏离20日均线程度"""
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        
        if isinstance(close.index, pd.MultiIndex):
            ma = close.groupby(level='symbol').transform(
                lambda x: x.rolling(window=self.period, min_periods=10).mean()
            )
        else:
            ma = close.rolling(window=self.period, min_periods=10).mean()
        
        dist = (close - ma) / ma
        
        dist = dist.replace([np.inf, -np.inf], np.nan)
        
        self.values = dist
        return dist


class DistMA60Factor(Factor):
    """
    价格偏离60日均线程度
    捕捉长期价格偏离
    
    公式: (Close - MA60) / MA60
    """
    
    def __init__(self, description: str = "价格偏离60日均线程度"):
        super().__init__("Dist_MA60", description)
        self.period = 60
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """计算偏离60日均线程度"""
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        
        if isinstance(close.index, pd.MultiIndex):
            ma = close.groupby(level='symbol').transform(
                lambda x: x.rolling(window=self.period, min_periods=30).mean()
            )
        else:
            ma = close.rolling(window=self.period, min_periods=30).mean()
        
        dist = (close - ma) / ma
        
        dist = dist.replace([np.inf, -np.inf], np.nan)
        
        self.values = dist
        return dist


class ZScore60Factor(Factor):
    """
    60日Z-Score因子
    标准化价格偏离，判断价格是否"跑太远该回归了"
    
    公式: ZScore = (Close - Mean60) / Std60
    
    解读:
    - ZScore > 2: 严重超买，可能反转下跌
    - ZScore < -2: 严重超卖，可能反弹上涨
    - ZScore 接近0: 价格在均线附近
    """
    
    def __init__(self, period: int = 60, description: str = "60日Z-Score因子"):
        """
        初始化
        
        Args:
            period: 计算周期（默认60日）
            description: 因子描述
        """
        super().__init__("ZScore_60", description)
        self.period = period
        self.weight = 1.0
        
    def calculate(self, data: pd.DataFrame) -> pd.Series:
        """
        计算60日Z-Score
        
        Formula: ZScore = (Close - Mean60) / Std60
        """
        if 'close' not in data.columns:
            raise ValueError("数据必须包含 'close' 列")
        
        close = data['close']
        
        if isinstance(close.index, pd.MultiIndex):
            # 按股票分组计算
            mean = close.groupby(level='symbol').transform(
                lambda x: x.rolling(window=self.period, min_periods=30).mean()
            )
            std = close.groupby(level='symbol').transform(
                lambda x: x.rolling(window=self.period, min_periods=30).std()
            )
        else:
            mean = close.rolling(window=self.period, min_periods=30).mean()
            std = close.rolling(window=self.period, min_periods=30).std()
        
        # 避免除以零
        std = std.replace(0, np.nan)
        
        # 计算Z-Score
        zscore = (close - mean) / std
        
        # 处理无效值
        zscore = zscore.replace([np.inf, -np.inf], np.nan)
        
        self.values = zscore
        return zscore


# ==================== 便捷函数 ====================

def create_return_factor(period: int) -> Factor:
    """
    创建收益率因子
    
    Args:
        period: 回看期（1/5/20/60日）
        
    Returns:
        对应的因子实例
    """
    if period == 1:
        return Return1dFactor()
    elif period == 5:
        return Return5dFactor()
    elif period == 20:
        return Return20dFactor()
    elif period == 60:
        return Return60dFactor()
    else:
        raise ValueError(f"不支持的周期: {period}")


def create_dist_ma_factor(period: int) -> Factor:
    """
    创建均线偏离因子
    
    Args:
        period: 均线周期（10/20/60）
        
    Returns:
        对应的因子实例
    """
    if period == 10:
        return DistMA10Factor()
    elif period == 20:
        return DistMA20Factor()
    elif period == 60:
        return DistMA60Factor()
    else:
        raise ValueError(f"不支持的周期: {period}")


# ==================== 导出 ====================

__all__ = [
    # 收益率因子
    'Return1dFactor',
    'Return5dFactor', 
    'Return20dFactor',
    'Return60dFactor',
    
    # 均值回归因子
    'DistMA10Factor',
    'DistMA20Factor',
    'DistMA60Factor',
    'ZScore60Factor',
    
    # 便捷函数
    'create_return_factor',
    'create_dist_ma_factor',
]
