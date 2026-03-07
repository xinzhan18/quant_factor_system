"""
单因子选股模块
Single Factor Selector

功能:
- 基于因子值排序
- Top N选股
- 等权分配
- ST/次新股过滤

使用示例:
    from .single import SingleFactorSelector, SelectionResult
    
    selector = SingleFactorSelector(
        top_n=20,
        sort_order='desc'  # 因子值大的优先
    )
    result = selector.select(factor_df, factor_col='momentum_5d')
"""

import pandas as pd
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import date
import logging

logger = logging.getLogger(__name__)


class SortOrder(Enum):
    """排序方向"""
    ASCENDING = 'asc'   # 升序 (因子值小的优先)
    DESCENDING = 'desc' # 降序 (因子值大的优先)


@dataclass
class SelectionResult:
    """选股结果"""
    selected_symbols: List[str]          # 选中的股票
    factor_values: Dict[str, float]      # 因子值
    weights: Dict[str, float]           # 权重
    score: float = 0.0                  # 综合得分
    selection_date: date = None          # 选股日期
    
    def __post_init__(self):
        if self.selection_date is None:
            self.selection_date = date.today()
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'selected_symbols': self.selected_symbols,
            'factor_values': self.factor_values,
            'weights': self.weights,
            'score': self.score,
            'selection_date': str(self.selection_date)
        }
    
    def to_dataframe(self) -> pd.DataFrame:
        """转换为DataFrame"""
        if not self.selected_symbols:
            return pd.DataFrame()
        
        data = []
        for symbol in self.selected_symbols:
            data.append({
                'symbol': symbol,
                'factor_value': self.factor_values.get(symbol),
                'weight': self.weights.get(symbol)
            })
        
        return pd.DataFrame(data)


class SingleFactorSelector:
    """
    单因子选股器
    
    功能:
    - 基于因子值排序
    - Top N选股
    - 过滤ST/次新股
    - 等权分配
    
    使用示例:
        selector = SingleFactorSelector(
            top_n=20,
            sort_order='desc'  # 因子值大的优先
        )
        result = selector.select(factor_df, factor_col='momentum_5d')
    """
    
    def __init__(
        self,
        top_n: int = 20,
        sort_order: str = 'desc',
        min_factor_value: float = None,
        max_factor_value: float = None,
        exclude_st: bool = True,
        exclude_new: bool = True,
        new_stock_days: int = 60,
        min_turnover: float = None,  # 最小换手率
        max_turnover: float = None,   # 最大换手率
        liquidity_threshold: float = None  # 最小流动性
    ):
        """
        初始化
        
        Args:
            top_n: 选股数量
            sort_order: 排序方向 (desc=因子值大的优先)
            min_factor_value: 最小因子值过滤
            max_factor_value: 最大因子值过滤
            exclude_st: 是否排除ST股票
            exclude_new: 是否排除次新股
            new_stock_days: 次新股排除天数
            min_turnover: 最小换手率
            max_turnover: 最大换手率
            liquidity_threshold: 最小流动性
        """
        self.top_n = top_n
        self.sort_order = SortOrder(sort_order)
        self.min_factor_value = min_factor_value
        self.max_factor_value = max_factor_value
        self.exclude_st = exclude_st
        self.exclude_new = exclude_new
        self.new_stock_days = new_stock_days
        self.min_turnover = min_turnover
        self.max_turnover = max_turnover
        self.liquidity_threshold = liquidity_threshold
    
    def select(
        self,
        factor_df: pd.DataFrame,
        factor_col: str = 'factor_value',
        selection_date: str = None,
        stock_info: pd.DataFrame = None
    ) -> SelectionResult:
        """
        执行选股
        
        Args:
            factor_df: 因子数据 (symbol, date, factor_value)
            factor_col: 因子值列名
            selection_date: 选股日期 (YYYY-MM-DD)
            stock_info: 股票信息 (用于过滤ST/次新股)
            
        Returns:
            SelectionResult
        """
        if factor_df.empty:
            logger.warning("因子数据为空")
            return SelectionResult(
                selected_symbols=[],
                factor_values={},
                weights={}
            )
        
        df = factor_df.copy()
        
        # 1. 过滤空值
        if factor_col in df.columns:
            df = df.dropna(subset=[factor_col])
        
        if df.empty:
            logger.warning("过滤后因子数据为空")
            return SelectionResult(
                selected_symbols=[],
                factor_values={},
                weights={}
            )
        
        # 2. 因子值过滤
        if self.min_factor_value is not None:
            df = df[df[factor_col] >= self.min_factor_value]
        
        if self.max_factor_value is not None:
            df = df[df[factor_col] <= self.max_factor_value]
        
        # 3. 股票信息过滤
        if self.exclude_st and stock_info is not None:
            st_stocks = self._get_st_stocks(stock_info)
            df = df[~df['symbol'].isin(st_stocks)]
        
        if self.exclude_new and stock_info is not None and selection_date:
            new_stocks = self._get_new_stocks(stock_info, selection_date, self.new_stock_days)
            df = df[~df['symbol'].isin(new_stocks)]
        
        # 4. 换手率过滤
        if (self.min_turnover is not None or self.max_turnover is not None) and stock_info is not None:
            turnover_dict = dict(zip(stock_info['code'], stock_info.get('turnover_rate', 0)))
            df = df[df['symbol'].apply(
                lambda x: self._check_turnover(x, turnover_dict)
            )]
        
        # 5. 排序
        ascending = self.sort_order == SortOrder.ASCENDING
        df = df.sort_values(factor_col, ascending=ascending)
        
        # 6. Top N
        top_df = df.head(self.top_n)
        
        # 7. 计算权重 (等权)
        n = len(top_df)
        weight = 1.0 / n if n > 0 else 0
        
        selected_symbols = top_df['symbol'].tolist()
        factor_values = dict(zip(top_df['symbol'], top_df[factor_col]))
        weights = {symbol: weight for symbol in selected_symbols}
        
        # 8. 计算综合得分
        if n > 0 and self.sort_order == SortOrder.DESCENDING:
            # 使用Top N因子的均值作为得分
            score = top_df[factor_col].mean()
        elif n > 0:
            score = -top_df[factor_col].mean()
        else:
            score = 0
        
        # 解析日期
        parsed_date = self._parse_date(selection_date)
        
        logger.info(f"✅ 选股完成: {n}只股票, 得分: {score:.4f}")
        
        return SelectionResult(
            selected_symbols=selected_symbols,
            factor_values=factor_values,
            weights=weights,
            score=score,
            selection_date=parsed_date
        )
    
    def _get_st_stocks(self, stock_info: pd.DataFrame) -> List[str]:
        """获取ST股票列表"""
        if stock_info is None:
            return []
        
        # 查找包含'ST'的股票
        if 'name' in stock_info.columns:
            st_mask = stock_info['name'].str.contains('ST', na=False)
            return stock_info[st_mask]['code'].tolist()
        
        if 'code' in stock_info.columns:
            return []
        
        return []
    
    def _get_new_stocks(
        self,
        stock_info: pd.DataFrame,
        current_date: str,
        days: int
    ) -> List[str]:
        """获取次新股列表"""
        if stock_info is None:
            return []
        
        if 'list_date' not in stock_info.columns:
            return []
        
        # 解析当前日期
        current = self._parse_date(current_date)
        if current is None:
            return []
        
        # 计算截止日期
        from datetime import timedelta
        limit_date = current - timedelta(days=days)
        
        # 筛选次新股
        new_mask = pd.to_datetime(stock_info['list_date']) > limit_date
        return stock_info[new_mask]['code'].tolist()
    
    def _check_turnover(self, symbol: str, turnover_dict: Dict) -> bool:
        """检查换手率"""
        if self.min_turnover is not None:
            turnover = turnover_dict.get(symbol, 0)
            if turnover < self.min_turnover:
                return False
        
        if self.max_turnover is not None:
            turnover = turnover_dict.get(symbol, float('inf'))
            if turnover > self.max_turnover:
                return False
        
        return True
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """解析日期字符串"""
        if date_str is None:
            return date.today()
        
        try:
            return pd.to_datetime(date_str).date()
        except (ValueError, TypeError):
            logger.warning(f"无法解析日期字符串: {date_str!r}, 使用今天日期")
            return date.today()


class MultiCriteriaSelector:
    """
    多条件选股器
    
    支持多个过滤条件:
    - 因子值范围
    - 行业分布
    - 市值范围
    """
    
    def __init__(self):
        self.filters = []
    
    def add_filter(self, filter_func):
        """添加过滤函数"""
        self.filters.append(filter_func)
    
    def select(
        self,
        factor_df: pd.DataFrame,
        stock_info: pd.DataFrame = None
    ) -> pd.DataFrame:
        """执行多条件选股"""
        df = factor_df.copy()
        
        for filter_func in self.filters:
            df = filter_func(df, stock_info)
        
        return df


# ==================== 导出 ====================

__all__ = [
    'SingleFactorSelector',
    'SelectionResult',
    'SortOrder',
    'MultiCriteriaSelector',
]
