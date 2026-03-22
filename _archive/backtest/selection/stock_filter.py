"""
股票过滤器 - 根据条件过滤股票
Stock Filter

功能:
1. 行业过滤
2. 市值过滤
3. 流动性过滤
4. 上市时间过滤
5. 涨跌停过滤
"""

import pandas as pd
import numpy as np
from typing import List, Callable
from dataclasses import dataclass
from enum import Enum


class FilterType(Enum):
    """过滤器类型"""
    INCLUDE = 'include'  # 保留满足条件的
    EXCLUDE = 'exclude'  # 排除满足条件的


@dataclass
class FilterCondition:
    """过滤条件"""
    name: str
    filter_type: FilterType
    condition: Callable[[pd.DataFrame], pd.Series]
    description: str = ''


class StockFilter:
    """
    股票过滤器
    
    组合多种条件过滤股票
    """
    
    def __init__(self):
        self.conditions: List[FilterCondition] = []
    
    def add_condition(
        self,
        name: str,
        filter_type: str,
        condition: Callable[[pd.DataFrame], pd.Series],
        description: str = ''
    ):
        """
        添加过滤条件
        
        Args:
            name: 条件名称
            filter_type: 'include' 或 'exclude'
            condition: 条件函数 (输入DataFrame，输出bool Series)
            description: 描述
        """
        ft = FilterType.INCLUDE if filter_type == 'include' else FilterType.EXCLUDE
        self.conditions.append(FilterCondition(name, ft, condition, description))
    
    def filter(
        self,
        df: pd.DataFrame,
        symbols: List[str] = None
    ) -> List[str]:
        """
        执行过滤
        
        Args:
            df: 包含股票数据的DataFrame
            symbols: 初始股票列表（如果为None，使用df中的symbol）
            
        Returns:
            过滤后的股票列表
        """
        if symbols is None:
            if 'symbol' not in df.columns:
                raise ValueError("df必须包含'symbol'列或提供symbols参数")
            symbols = df['symbol'].unique().tolist()
        
        # 逐个条件过滤
        for cond in self.conditions:
            # 计算满足条件的股票
            if 'symbol' not in df.columns:
                # 如果df是price数据，先合并
                continue
            
            mask = cond.condition(df)
            qualified_symbols = set(df.loc[mask, 'symbol'].unique()) if mask.any() else set()
            
            if cond.filter_type == FilterType.INCLUDE:
                # 保留满足条件的
                symbols = [s for s in symbols if s in qualified_symbols]
            else:
                # 排除满足条件的
                symbols = [s for s in symbols if s not in qualified_symbols]
        
        return symbols
    
    def filter_df(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        过滤DataFrame
        
        Args:
            df: 包含股票数据的DataFrame
            
        Returns:
            过滤后的DataFrame
        """
        for cond in self.conditions:
            if 'symbol' not in df.columns:
                continue
            
            mask = cond.condition(df)
            df = df[mask]
        
        return df
    
    def clear(self):
        """清空所有条件"""
        self.conditions = []
    
    def get_summary(self) -> pd.DataFrame:
        """
        获取条件汇总
        
        Returns:
            条件汇总DataFrame
        """
        data = []
        for cond in self.conditions:
            data.append({
                '名称': cond.name,
                '类型': '保留' if cond.filter_type == FilterType.INCLUDE else '排除',
                '描述': cond.description
            })
        return pd.DataFrame(data) if data else pd.DataFrame()


# ==================== 预定义过滤器 ====================

def industry_filter(
    include_industries: List[str] = None,
    exclude_industries: List[str] = None
) -> StockFilter:
    """
    创建行业过滤器
    
    Args:
        include_industries: 保留的行业列表
        exclude_industries: 排除的行业列表
        
    Returns:
        StockFilter
    """
    filter = StockFilter()
    
    if include_industries:
        filter.add_condition(
            '行业白名单',
            'include',
            lambda df: df.get('industry', pd.Series(['']*len(df))).isin(include_industries),
            f"保留行业: {include_industries}"
        )
    
    if exclude_industries:
        filter.add_condition(
            '行业黑名单',
            'exclude',
            lambda df: df.get('industry', pd.Series(['']*len(df))).isin(exclude_industries),
            f"排除行业: {exclude_industries}"
        )
    
    return filter


def market_cap_filter(
    min_cap: float = None,
    max_cap: float = None,
    cap_column: str = 'market_cap'
) -> StockFilter:
    """
    创建市值过滤器
    
    Args:
        min_cap: 最小市值（亿）
        max_cap: 最大市值（亿）
        cap_column: 市值列名
        
    Returns:
        StockFilter
    """
    filter = StockFilter()
    
    if min_cap is not None:
        filter.add_condition(
            '最小市值',
            'include',
            lambda df: df.get(cap_column, pd.Series([np.inf]*len(df))) >= min_cap,
            f"市值 >= {min_cap}亿"
        )
    
    if max_cap is not None:
        filter.add_condition(
            '最大市值',
            'include',
            lambda df: df.get(cap_column, pd.Series([0]*len(df))) <= max_cap,
            f"市值 <= {max_cap}亿"
        )
    
    return filter


def liquidity_filter(
    min_volume: float = None,
    avg_volume_window: int = 20,
    volume_column: str = 'volume'
) -> StockFilter:
    """
    创建流动性过滤器
    
    Args:
        min_volume: 最小成交量
        avg_volume_window: 平均成交量窗口
        volume_column: 成交量列名
        
    Returns:
        StockFilter
    """
    filter = StockFilter()
    
    if min_volume is not None:
        filter.add_condition(
            '最小成交量',
            'include',
            lambda df: df.get(volume_column, pd.Series([np.inf]*len(df))) >= min_volume,
            f"成交量 >= {min_volume}"
        )
    
    return filter


def listing_date_filter(
    min_listing_days: int = 60
) -> StockFilter:
    """
    创建上市时间过滤器
    
    Args:
        min_listing_days: 最小上市天数
        
    Returns:
        StockFilter
    """
    filter = StockFilter()
    
    filter.add_condition(
        '上市时间',
        'include',
        lambda df: df.get('listing_days', pd.Series([9999]*len(df))) >= min_listing_days,
        f"上市 >= {min_listing_days}天"
    )
    
    return filter


def limit_up_down_filter(
    exclude_limit_up: bool = True,
    exclude_limit_down: bool = False,
    price_column: str = 'close',
    pct_change_column: str = 'pct_change'
) -> StockFilter:
    """
    创建涨跌停过滤器
    
    Args:
        exclude_limit_up: 排除涨停股票
        exclude_limit_down: 排除跌停股票
        price_column: 价格列名
        pct_change_column: 涨跌幅列名
        
    Returns:
        StockFilter
    """
    filter = StockFilter()
    
    if exclude_limit_up:
        filter.add_condition(
            '排除涨停',
            'exclude',
            lambda df: df.get(pct_change_column, pd.Series([0]*len(df))) >= 9.8,
            '排除涨停股票'
        )
    
    if exclude_limit_down:
        filter.add_condition(
            '排除跌停',
            'exclude',
            lambda df: df.get(pct_change_column, pd.Series([0]*len(df))) <= -9.8,
            '排除跌停股票'
        )
    
    return filter


def create_composite_filter(
    include_industries: List[str] = None,
    exclude_industries: List[str] = None,
    min_market_cap: float = 50,
    min_volume: float = 10000000,
    min_listing_days: int = 60,
    exclude_limit_up: bool = True
) -> StockFilter:
    """
    创建组合过滤器
    
    Args:
        include_industries: 保留的行业
        exclude_industries: 排除的行业
        min_market_cap: 最小市值（亿）
        min_volume: 最小成交量
        min_listing_days: 最小上市天数
        exclude_limit_up: 是否排除涨停
        
    Returns:
        组合过滤器
    """
    filter = StockFilter()
    
    # 行业过滤
    if include_industries:
        filter.add_condition(
            '行业白名单',
            'include',
            lambda df: df.get('industry', pd.Series(['']*len(df))).isin(include_industries),
            f"保留行业: {include_industries}"
        )
    
    if exclude_industries:
        filter.add_condition(
            '行业黑名单',
            'exclude',
            lambda df: df.get('industry', pd.Series(['']*len(df))).isin(exclude_industries),
            f"排除行业: {exclude_industries}"
        )
    
    # 市值过滤
    if min_market_cap:
        filter.add_condition(
            '最小市值',
            'include',
            lambda df: df.get('market_cap', pd.Series([np.inf]*len(df))) >= min_market_cap,
            f"市值 >= {min_market_cap}亿"
        )
    
    # 流动性过滤
    if min_volume:
        filter.add_condition(
            '最小成交量',
            'include',
            lambda df: df.get('volume', pd.Series([0]*len(df))) >= min_volume,
            f"成交量 >= {min_volume}"
        )
    
    # 上市时间
    if min_listing_days:
        filter.add_condition(
            '上市时间',
            'include',
            lambda df: df.get('listing_days', pd.Series([9999]*len(df))) >= min_listing_days,
            f"上市 >= {min_listing_days}天"
        )
    
    # 涨跌停
    if exclude_limit_up:
        filter.add_condition(
            '排除涨停',
            'exclude',
            lambda df: df.get('pct_change', pd.Series([0]*len(df))) >= 9.8,
            '排除涨停股票'
        )
    
    return filter


# ==================== 导出 ====================

__all__ = [
    'StockFilter',
    'FilterType',
    'FilterCondition',
    'industry_filter',
    'market_cap_filter',
    'liquidity_filter',
    'listing_date_filter',
    'limit_up_down_filter',
    'create_composite_filter',
]
