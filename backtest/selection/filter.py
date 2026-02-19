"""
交集过滤器模块
Intersection Filter

功能:
- 多个因子筛选出的股票取交集
- 多个因子筛选出的股票取并集
- 条件组合

使用示例:
    from .filter import IntersectionFilter, UnionFilter
    
    # 取交集
    filter = IntersectionFilter()
    result = filter.filter({
        'momentum': selection1,
        'value': selection2,
        'quality': selection3
    })
"""

import pandas as pd
from typing import Dict, List, Set, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class FilterType(Enum):
    """过滤器类型"""
    INTERSECTION = 'intersection'  # 交集
    UNION = 'union'               # 并集
    DIFFERENCE = 'difference'     # 差集


@dataclass
class FilterResult:
    """过滤结果"""
    symbols: List[str]
    method: str
    count: int
    details: Dict[str, List[str]] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class BaseFilter:
    """过滤器基类"""
    
    @property
    def filter_type(self) -> FilterType:
        raise NotImplementedError
    
    def filter(
        self,
        selections: Dict[str, List[str]],
        min_count: int = None
    ) -> FilterResult:
        """
        执行过滤
        
        Args:
            selections: {因子名: 选中的股票列表}
            min_count: 最小满足条件数 (交集时使用)
            
        Returns:
            FilterResult
        """
        raise NotImplementedError


class IntersectionFilter(BaseFilter):
    """
    交集过滤器
    
    取多个因子筛选结果的交集
    即: 同时被所有因子选中的股票
    """
    
    @property
    def filter_type(self) -> FilterType:
        return FilterType.INTERSECTION
    
    def filter(
        self,
        selections: Dict[str, List[str]],
        min_count: int = None
    ) -> FilterResult:
        """
        执行交集过滤
        
        Args:
            selections: {因子名: 选中的股票列表}
            min_count: 最少满足的因子数 (默认=全部因子数)
            
        Returns:
            FilterResult: 取交集后的股票列表
        """
        if not selections:
            logger.warning("没有筛选结果")
            return FilterResult(
                symbols=[],
                method='intersection',
                count=0
            )
        
        # 计算每个股票的命中次数
        symbol_counts: Dict[str, int] = {}
        
        for name, symbols in selections.items():
            if not symbols:
                continue
            
            for symbol in symbols:
                symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        
        # 确定阈值
        if min_count is None:
            min_count = len(selections)
        
        # 筛选命中次数 >= min_count 的股票
        result_symbols = [
            s for s, count in symbol_counts.items()
            if count >= min_count
        ]
        
        result_symbols.sort()
        
        logger.info(
            f"✅ 交集过滤: {len(result_symbols)}只股票 "
            f"(要求命中{min_count}个因子)"
        )
        
        return FilterResult(
            symbols=result_symbols,
            method='intersection',
            count=len(result_symbols),
            details={
                'selection_counts': symbol_counts
            }
        )


class UnionFilter(BaseFilter):
    """
    并集过滤器
    
    取多个因子筛选结果的并集
    即: 被任一因子选中的股票
    """
    
    @property
    def filter_type(self) -> FilterType:
        return FilterType.UNION
    
    def filter(
        self,
        selections: Dict[str, List[str]],
        min_count: int = None
    ) -> FilterResult:
        """
        执行并集过滤
        
        Args:
            selections: {因子名: 选中的股票列表}
            min_count: (可选) 最少命中数
            
        Returns:
            FilterResult: 取并集后的股票列表
        """
        if not selections:
            logger.warning("没有筛选结果")
            return FilterResult(
                symbols=[],
                method='union',
                count=0
            )
        
        # 合并所有股票
        all_symbols: Set[str] = set()
        
        for name, symbols in selections.items():
            all_symbols.update(symbols)
        
        result_symbols = sorted(list(all_symbols))
        
        # 如果指定了min_count，进一步过滤
        if min_count and min_count > 1:
            # 计算命中次数
            symbol_counts: Dict[str, int] = {}
            
            for name, symbols in selections.items():
                for symbol in symbols:
                    symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
            
            result_symbols = [
                s for s in result_symbols
                if symbol_counts.get(s, 0) >= min_count
            ]
        
        logger.info(f"✅ 并集过滤: {len(result_symbols)}只股票")
        
        return FilterResult(
            symbols=result_symbols,
            method='union',
            count=len(result_symbols),
            details={
                'total_factors': len(selections)
            }
        )


class DifferenceFilter(BaseFilter):
    """
    差集过滤器
    
    取A集合中不属于B集合的部分
    即: 被A因子选中，但不被B因子选中的股票
    """
    
    @property
    def filter_type(self) -> FilterType:
        return FilterType.DIFFERENCE
    
    def filter(
        self,
        selections: Dict[str, List[str]],
        min_count: int = None
    ) -> FilterResult:
        """
        执行差集过滤
        
        Args:
            selections: {'A': [A选中的股票], 'B': [B选中的股票]}
            min_count: (可选) 无效
            
        Returns:
            FilterResult: A-B的差集
        """
        if len(selections) < 2:
            logger.warning("差集需要至少两个集合")
            return FilterResult(
                symbols=[],
                method='difference',
                count=0
            )
        
        # 获取前两个集合
        names = list(selections.keys())
        a_set = set(selections[names[0]])
        b_set = set(selections[names[1]])
        
        # 计算差集
        result_symbols = sorted(list(a_set - b_set))
        
        logger.info(
            f"✅ 差集过滤: {names[0]} - {names[1]} = {len(result_symbols)}只股票"
        )
        
        return FilterResult(
            symbols=result_symbols,
            method='difference',
            count=len(result_symbols),
            details={
                'set_a': list(a_set),
                'set_b': list(b_set)
            }
        )


class ConditionalFilter:
    """
    条件组合过滤器
    
    支持复杂的条件组合:
    - (A AND B) OR C
    - (A OR B) AND C
    - etc.
    """
    
    def __init__(self):
        self.conditions: List[Dict] = []
        self.operator: str = 'AND'  # AND / OR
    
    def add_condition(
        self,
        factor_name: str,
        operator: str,  # '>', '<', '>=', '<=', '==', '!='
        threshold: float
    ):
        """
        添加条件
        
        Args:
            factor_name: 因子名称
            operator: 比较运算符
            threshold: 阈值
        """
        self.conditions.append({
            'factor': factor_name,
            'operator': operator,
            'threshold': threshold
        })
    
    def set_operator(self, operator: str):
        """设置条件组合方式"""
        self.operator = operator.upper()  # AND / OR
    
    def filter(
        self,
        factor_data: Dict[str, pd.DataFrame]
    ) -> List[str]:
        """
        执行条件过滤
        
        Args:
            factor_data: {因子名: DataFrame}
            
        Returns:
            满足条件的股票列表
        """
        if not self.conditions:
            return []
        
        # 评估每个条件
        condition_results: Dict[str, Set[str]] = {}
        
        for cond in self.conditions:
            factor_name = cond['factor']
            operator = cond['operator']
            threshold = cond['threshold']
            
            if factor_name not in factor_data:
                continue
            
            df = factor_data[factor_name]
            if df.empty:
                continue
            
            # 根据运算符筛选
            if operator == '>':
                filtered = df[df['factor_value'] > threshold]['symbol'].tolist()
            elif operator == '>=':
                filtered = df[df['factor_value'] >= threshold]['symbol'].tolist()
            elif operator == '<':
                filtered = df[df['factor_value'] < threshold]['symbol'].tolist()
            elif operator == '<=':
                filtered = df[df['factor_value'] <= threshold]['symbol'].tolist()
            elif operator == '==':
                filtered = df[df['factor_value'] == threshold]['symbol'].tolist()
            elif operator == '!=':
                filtered = df[df['factor_value'] != threshold]['symbol'].tolist()
            else:
                logger.warning(f"不支持的运算符: {operator}")
                continue
            
            condition_results[cond['factor']] = set(filtered)
        
        if not condition_results:
            return []
        
        # 组合结果
        result_sets = list(condition_results.values())
        
        if self.operator == 'AND':
            # 取所有集合的交集
            final_set = result_sets[0]
            for s in result_sets[1:]:
                final_set = final_set & s
        else:
            # 取所有集合的并集
            final_set = result_sets[0]
            for s in result_sets[1:]:
                final_set = final_set | s
        
        result_symbols = sorted(list(final_set))
        
        logger.info(f"✅ 条件过滤: {len(result_symbols)}只股票 ({self.operator})")
        
        return result_symbols


# ==================== 导出 ====================

__all__ = [
    'IntersectionFilter',
    'UnionFilter',
    'DifferenceFilter',
    'ConditionalFilter',
    'FilterResult',
    'FilterType',
]
