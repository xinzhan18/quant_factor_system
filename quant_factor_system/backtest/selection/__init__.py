"""
选股模块
Stock Selection Module

提供因子选择、股票过滤、排名打分功能

主要组件:
- FactorSelector: 因子选择器
- StockFilter: 股票过滤器
- StockRanker: 股票排名器

使用方式:
    from quant_factor_system.backtest.selection import (
        FactorSelector,
        StockFilter,
        StockRanker,
        create_composite_filter
    )

    # 创建过滤器
    filter = create_composite_filter(
        min_market_cap=100,
        exclude_limit_up=True
    )
    
    # 过滤股票
    symbols = filter.filter_df(df)
    
    # 排名
    ranker = StockRanker()
    ranked_df, top_symbols = ranker.rank_multi_factor(df, ['factor1', 'factor2'])
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
]
