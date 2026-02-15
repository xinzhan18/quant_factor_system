"""
分钟聚合器
Minute Data Aggregator

功能:
- 将分钟数据聚合到日频
- 支持多种聚合方法
- 支持增量计算

使用示例:
    from quant_factor_system.factors import MinuteAggregator, AggregationMethod
    
    agg = MinuteAggregator(method='last')
    daily_factor = agg.aggregate(minute_df, symbol_col='symbol', price_col='close')
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable, Union
from dataclasses import dataclass
from enum import Enum
from datetime import date
import logging

logger = logging.getLogger(__name__)


class AggregationMethod(Enum):
    """聚合方法"""
    LAST = 'last'      # 最新值
    FIRST = 'first'    # 第一个值
    MEAN = 'mean'      # 均值
    MAX = 'max'        # 最大值
    MIN = 'min'        # 最小值
    STD = 'std'        # 标准差
    SUM = 'sum'        # 求和


@dataclass
class AggregationResult:
    """聚合结果"""
    symbol: str
    date: date
    factor_value: float
    method: str = ''


class MinuteAggregator:
    """
    分钟聚合器
    
    将分钟数据聚合为日频因子
    
    支持的聚合方法:
    - LAST: 当日最后一根K线的值
    - FIRST: 当日第一根K线的值
    - MEAN: 当日均值
    - MAX: 当日最大值
    - MIN: 当日最小值
    - STD: 当日标准差
    - SUM: 当日求和
    """
    
    # 聚合方法映射
    AGG_METHODS: Dict[AggregationMethod, Callable] = {
        AggregationMethod.LAST: lambda x: x.iloc[-1],
        AggregationMethod.FIRST: lambda x: x.iloc[0],
        AggregationMethod.MEAN: lambda x: x.mean(),
        AggregationMethod.MAX: lambda x: x.max(),
        AggregationMethod.MIN: lambda x: x.min(),
        AggregationMethod.STD: lambda x: x.std(),
        AggregationMethod.SUM: lambda x: x.sum(),
    }
    
    def __init__(
        self,
        method: Union[str, AggregationMethod] = 'last',
        price_col: str = 'close',
        symbol_col: str = 'symbol',
        datetime_col: str = 'datetime'
    ):
        """
        初始化聚合器
        
        Args:
            method: 聚合方法 (last/mean/max/min/std/first/sum)
            price_col: 价格列名
            symbol_col: 股票代码列名
            datetime_col: 时间戳列名
        """
        # 解析聚合方法
        if isinstance(method, str):
            try:
                self.method = AggregationMethod(method.lower())
            except ValueError:
                raise ValueError(
                    f"不支持的聚合方法: {method}\n"
                    f"支持的: {[m.value for m in AggregationMethod]}"
                )
        else:
            self.method = method
        
        self.price_col = price_col
        self.symbol_col = symbol_col
        self.datetime_col = datetime_col
    
    @property
    def agg_func(self) -> Callable:
        """获取聚合函数"""
        return self.AGG_METHODS[self.method]
    
    def aggregate(
        self,
        minute_df: pd.DataFrame,
        target_col: str = None
    ) -> pd.DataFrame:
        """
        将分钟数据聚合为日频
        
        Args:
            minute_df: 分钟级数据
            target_col: 目标列，默认使用price_col
            
        Returns:
            日频因子DataFrame (symbol, date, factor_value)
        """
        if minute_df.empty:
            return pd.DataFrame()
        
        df = minute_df.copy()
        
        # 1. 确保时间列是datetime类型
        if self.datetime_col not in df.columns:
            raise ValueError(f"缺少时间列: {self.datetime_col}")
        
        df[self.datetime_col] = pd.to_datetime(df[self.datetime_col])
        
        # 2. 提取日期
        df['date'] = df[self.datetime_col].dt.date
        
        # 3. 确定目标列
        price_col = target_col or self.price_col
        
        if price_col not in df.columns:
            raise ValueError(f"缺少价格列: {price_col}")
        
        # 4. 按股票和日期分组聚合
        try:
            result = (
                df.groupby([self.symbol_col, 'date'])[price_col]
                .apply(self.agg_func)
                .reset_index()
            )
        except Exception as e:
            logger.error(f"聚合失败: {e}")
            return pd.DataFrame()
        
        # 5. 重命名列
        result.columns = [self.symbol_col, 'date', 'factor_value']
        result['date'] = pd.to_datetime(result['date'])
        
        return result
    
    def aggregate_with_stats(
        self,
        minute_df: pd.DataFrame,
        target_col: str = None
    ) -> pd.DataFrame:
        """
        聚合并返回统计信息
        
        Returns:
            包含factor_value, count, std, min, max
        """
        if minute_df.empty:
            return pd.DataFrame()
        
        df = minute_df.copy()
        df[self.datetime_col] = pd.to_datetime(df[self.datetime_col])
        df['date'] = df[self.datetime_col].dt.date
        
        price_col = target_col or self.price_col
        
        # 多统计量聚合
        agg_result = (
            df.groupby([self.symbol_col, 'date'])[price_col]
            .agg(['mean', 'std', 'min', 'max', 'count'])
            .reset_index()
        )
        
        agg_result.columns = [
            self.symbol_col, 'date', 
            'mean', 'std', 'min', 'max', 'count'
        ]
        
        # 添加聚合方法
        agg_result['method列'] = self.method.value
        
        return agg_result


class MultiColumnAggregator:
    """
    多列聚合器
    
    同时聚合多个列 (如OHLCV)
    """
    
    def __init__(
        self,
        symbol_col: str = 'symbol',
        datetime_col: str = 'datetime',
        default_method: str = 'last'
    ):
        """
        初始化
        
        Args:
            symbol_col: 股票代码列名
            datetime_col: 时间戳列名
            default_method: 默认聚合方法
        """
        self.symbol_col = symbol_col
        self.datetime_col = datetime_col
        self.default_method = default_method
    
    def aggregate(
        self,
        minute_df: pd.DataFrame,
        column_methods: Dict[str, str] = None
    ) -> pd.DataFrame:
        """
        聚合多个列
        
        Args:
            minute_df: 分钟级数据
            column_methods: {列名: 聚合方法}，默认使用default_method
            
        Returns:
            多列日频DataFrame
        """
        if minute_df.empty:
            return pd.DataFrame()
        
        df = minute_df.copy()
        df[self.datetime_col] = pd.to_datetime(df[self.datetime_col])
        df['date'] = df[self.datetime_col].dt.date
        
        # 确定要聚合的列
        exclude_cols = [self.symbol_col, self.datetime_col, 'date']
        price_cols = [c for c in df.columns if c not in exclude_cols]
        
        if column_methods is None:
            column_methods = {col: self.default_method for col in price_cols}
        
        # 分别聚合每个列
        results = []
        for col, method in column_methods.items():
            agg = MinuteAggregator(
                method=method,
                price_col=col,
                symbol_col=self.symbol_col,
                datetime_col=self.datetime_col
            )
            
            result = agg.aggregate(df, target_col=col)
            
            if not result.empty:
                # 重命名
                result = result.rename(columns={'factor_value': f'{col}_{method}'})
                results.append(result)
        
        # 合并结果
        if not results:
            return pd.DataFrame()
        
        # 以symbol和date为基准合并
        merged = results[0]
        for result in results[1:]:
            merged = merged.merge(
                result,
                on=[self.symbol_col, 'date'],
                how='outer'
            )
        
        return merged


class FactorAggregator:
    """
    因子聚合器
    
    支持:
    - 分钟因子聚合到日频
    - 日频因子聚合到周/月频
    - 多列聚合
    """
    
    def __init__(
        self,
        symbol_col: str = 'symbol',
        datetime_col: str = 'datetime'
    ):
        self.symbol_col = symbol_col
        self.datetime_col = datetime_col
    
    def aggregate_to_daily(
        self,
        df: pd.DataFrame,
        value_col: str = 'factor_value',
        method: str = 'last'
    ) -> pd.DataFrame:
        """
        聚合到日频
        
        Args:
            df: 原始数据
            value_col: 值列名
            method: 聚合方法
            
        Returns:
            日频数据
        """
        agg = MinuteAggregator(
            method=method,
            price_col=value_col,
            symbol_col=self.symbol_col,
            datetime_col=self.datetime_col
        )
        return agg.aggregate(df, target_col=value_col)
    
    def aggregate_to_weekly(
        self,
        df: pd.DataFrame,
        value_col: str = 'factor_value',
        method: str = 'last'
    ) -> pd.DataFrame:
        """
        聚合到周频
        
        Args:
            df: 原始数据
            value_col: 值列名
            method: 聚合方法
            
        Returns:
            周频数据
        """
        df = df.copy()
        df[self.datetime_col] = pd.to_datetime(df[self.datetime_col])
        
        # 计算周开始日期 (周一)
        df['week'] = df[self.datetime_col].dt.to_period('W').dt.start_time
        
        agg_func = MinuteAggregator.AGG_METHODS[AggregationMethod(method)]
        
        result = (
            df.groupby([self.symbol_col, 'week'])[value_col]
            .apply(agg_func)
            .reset_index()
        )
        result.columns = [self.symbol_col, 'date', value_col]
        
        return result
    
    def aggregate_to_monthly(
        self,
        df: pd.DataFrame,
        value_col: str = 'factor_value',
        method: str = 'last'
    ) -> pd.DataFrame:
        """
        聚合到月频
        
        Args:
            df: 原始数据
            value_col: 值列名
            method: 聚合方法
            
        Returns:
            月频数据
        """
        df = df.copy()
        df[self.datetime_col] = pd.to_datetime(df[self.datetime_col])
        
        # 计算月初日期
        df['month'] = df[self.datetime_col].dt.to_period('M').dt.start_time
        
        agg_func = MinuteAggregator.AGG_METHODS[AggregationMethod(method)]
        
        result = (
            df.groupby([self.symbol_col, 'month'])[value_col]
            .apply(agg_func)
            .reset_index()
        )
        result.columns = [self.symbol_col, 'date', value_col]
        
        return result


# ==================== 便捷函数 ====================

def aggregate_minute_to_daily(
    minute_df: pd.DataFrame,
    method: str = 'last',
    price_col: str = 'close',
    symbol_col: str = 'symbol',
    datetime_col: str = 'datetime'
) -> pd.DataFrame:
    """
    分钟聚合到日频 (便捷函数)
    
    Args:
        minute_df: 分钟数据
        method: 聚合方法
        price_col: 价格列
        symbol_col: 股票代码列
        datetime_col: 时间戳列
        
    Returns:
        日频数据
    """
    agg = MinuteAggregator(
        method=method,
        price_col=price_col,
        symbol_col=symbol_col,
        datetime_col=datetime_col
    )
    return agg.aggregate(minute_df)


# ==================== 导出 ====================

__all__ = [
    'MinuteAggregator',
    'AggregationMethod',
    'AggregationResult',
    'MultiColumnAggregator',
    'FactorAggregator',
    'aggregate_minute_to_daily',
]
