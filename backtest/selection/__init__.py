"""
选股模块
Stock Selection Module

提供因子选择、股票过滤、排名打分功能

主要组件:
- FactorSelector: 因子选择器
- StockFilter: 股票过滤器
- StockRanker: 股票排名器
- SingleFactorSelector: 单因子选股
- MultiFactorCombiner: 多因子组合
- IntersectionFilter/UnionFilter/DifferenceFilter: 集合过滤器

使用方式:
    # 底层工具
    from quant_factor_system.backtest.selection import (
        FactorSelector,
        StockFilter,
        StockRanker,
        create_composite_filter
    )
    
    # 策略级别
    from quant_factor_system.backtest.selection import (
        SingleFactorSelector,
        MultiFactorCombiner,
        IntersectionFilter,
    )
"""

from .factor_selector import (
    FactorSelector,
    FactorScore,
    create_factor_selector,
)

from .stock_filter import (
    StockFilter,
    FilterType,
    FilterCondition,
    industry_filter,
    market_cap_filter,
    liquidity_filter,
    listing_date_filter,
    limit_up_down_filter,
    create_composite_filter,
)

from .ranker import (
    StockRanker,
    RankResult,
    create_ranker,
)

from .single import (
    SingleFactorSelector,
    SelectionResult,
    SortOrder,
)

from .multi import (
    MultiFactorCombiner,
    CombinedFactor,
    CombinationMethod,
)

from .filter import (
    IntersectionFilter,
    UnionFilter,
    DifferenceFilter,
    FilterResult,
)

__all__ = [
    # 因子选择
    'FactorSelector',
    'FactorScore',
    'create_factor_selector',
    
    # 股票过滤
    'StockFilter',
    'FilterType',
    'FilterCondition',
    'industry_filter',
    'market_cap_filter',
    'liquidity_filter',
    'listing_date_filter',
    'limit_up_down_filter',
    'create_composite_filter',
    
    # 排名
    'StockRanker',
    'RankResult',
    'create_ranker',
    
    # 单因子选股
    'SingleFactorSelector',
    'SelectionResult',
    'SortOrder',
    
    # 多因子组合
    'MultiFactorCombiner',
    'CombinedFactor',
    'CombinationMethod',
    
    # 集合过滤
    'IntersectionFilter',
    'UnionFilter',
    'DifferenceFilter',
    'FilterResult',
]
