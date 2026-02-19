"""
股票排名器 - 根据因子值对股票进行排名
Stock Ranker

功能:
1. 单因子排名
2. 多因子加权排名
3. 行业中性化排名
4. 市值中性化排名
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass


@dataclass
class RankResult:
    """排名结果"""
    symbol: str
    score: float
    rank: int
    factor_values: Dict[str, float]


class StockRanker:
    """
    股票排名器
    
    根据因子值对股票进行综合排名
    """
    
    def __init__(self, method: str = 'rank'):
        """
        初始化
        
        Args:
            method: 排名方法 ('rank'/'percentile'/'zscore')
        """
        self.method = method
        self.weights: Dict[str, float] = {}
    
    def set_weights(self, weights: Dict[str, float]):
        """
        设置因子权重
        
        Args:
            weights: 因子名称 -> 权重
        """
        # 归一化权重
        total = sum(weights.values())
        if total > 0:
            self.weights = {k: v/total for k, v in weights.items()}
        else:
            self.weights = weights
    
    def rank_single_factor(
        self,
        df: pd.DataFrame,
        factor_column: str = 'value',
        ascending: bool = False,
        top_n: int = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        单因子排名
        
        Args:
            df: 包含因子数据的DataFrame
            factor_column: 因子值列名
            ascending: 是否升序（False=因子值大的排名靠前）
            top_n: 只返回前N名
            
        Returns:
            (排名后的DataFrame, 排名前N的股票列表)
        """
        # 去除空值
        valid_df = df.dropna(subset=[factor_column])
        
        if valid_df.empty:
            return df, []
        
        # 排名
        valid_df = valid_df.copy()
        valid_df['rank'] = valid_df[factor_column].rank(
            method='average',
            ascending=ascending
        ).astype(int)
        
        # 按排名排序
        if ascending:
            valid_df = valid_df.sort_values('rank')
        else:
            valid_df = valid_df.sort_values('rank', ascending=False)
        
        # 返回前N
        if top_n is not None:
            valid_df = valid_df.head(top_n)
        
        symbols = valid_df['symbol'].tolist()
        return valid_df, symbols
    
    def rank_multi_factor(
        self,
        df: pd.DataFrame,
        factor_columns: List[str],
        weights: Dict[str, float] = None,
        ascending_dict: Dict[str, bool] = None,
        top_n: int = None,
        neutralize_market_cap: bool = False
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        多因子加权排名
        
        Args:
            df: 包含因子数据的DataFrame
            factor_columns: 因子列名列表
            weights: 各因子权重
            ascending_dict: 各因子是否升序
            top_n: 只返回前N名
            neutralize_market_cap: 是否市值中性化
            
        Returns:
            (排名后的DataFrame, 排名前N的股票列表)
        """
        # 设置默认参数
        if weights is None:
            weights = {f: 1.0/len(factor_columns) for f in factor_columns}
        
        if ascending_dict is None:
            ascending_dict = {f: False for f in factor_columns}
        
        # 归一化权重
        total = sum(weights.values())
        if total > 0:
            weights = {k: v/total for k, v in weights.items()}
        
        # 复制数据
        rank_df = df.dropna(subset=factor_columns).copy()
        
        if rank_df.empty:
            return df, []
        
        # 行业中性化
        if neutralize_market_cap and 'market_cap' in rank_df.columns:
            for col in factor_columns:
                # 对每个行业分别回归
                rank_df[f'{col}_neutralized'] = rank_df.groupby('industry').apply(
                    lambda x: x[col] - x[col].mean()
                ).reset_index(level=0, drop=True)
                factor_columns = [f'{col}_neutralized' for col in factor_columns]
        
        # 计算综合得分
        scores = pd.Series(0.0, index=rank_df.index)
        
        for col in factor_columns:
            if col in rank_df.columns:
                # 标准化到0-1
                min_val = rank_df[col].min()
                max_val = rank_df[col].max()
                if max_val > min_val:
                    normalized = (rank_df[col] - min_val) / (max_val - min_val)
                else:
                    normalized = 0.5
                
                # 根据方向调整
                if ascending_dict.get(col, False):
                    normalized = 1 - normalized
                
                scores += normalized * weights.get(col, 0)
        
        rank_df['composite_score'] = scores
        
        # 排名
        rank_df['rank'] = rank_df['composite_score'].rank(
            method='average',
            ascending=False
        ).astype(int)
        
        # 排序
        rank_df = rank_df.sort_values('rank')
        
        # 返回前N
        if top_n is not None:
            rank_df = rank_df.head(top_n)
        
        symbols = rank_df['symbol'].tolist()
        return rank_df, symbols
    
    def rank_by_ic(
        self,
        df: pd.DataFrame,
        factor_columns: Dict[str, float],  # 因子名 -> IC
        top_n: int = None
    ) -> Tuple[pd.DataFrame, List[str]]:
        """
        基于IC排名
        
        Args:
            df: 包含因子数据的DataFrame
            factor_columns: 因子名 -> IC绝对值
            top_n: 只返回前N名
            
        Returns:
            (排名后的DataFrame, 排名前N的股票列表)
        """
        # 使用IC作为权重
        weights = {k: abs(v) for k, v in factor_columns.items()}
        return self.rank_multi_factor(df, list(factor_columns.keys()), weights, top_n=top_n)
    
    def rank_by_category(
        self,
        df: pd.DataFrame,
        category_column: str = 'industry',
        score_column: str = 'composite_score',
        top_n_per_category: int = 5
    ) -> pd.DataFrame:
        """
        按行业分组排名
        
        Args:
            df: 包含因子数据和行业数据的DataFrame
            category_column: 行业列名
            score_column: 得分列名
            top_n_per_category: 每个行业返回的数量
            
        Returns:
            排名后的DataFrame
        """
        # 按行业分组排名
        result = df.copy()
        result['category_rank'] = result.groupby(category_column)[score_column].rank(
            method='first',
            ascending=False
        ).astype(int)
        
        # 筛选每个行业前N
        result = result[result['category_rank'] <= top_n_per_category]
        
        return result.sort_values([category_column, 'category_rank'])
    
    def generate_rank_report(
        self,
        rank_df: pd.DataFrame,
        score_column: str = 'composite_score'
    ) -> Dict:
        """
        生成排名报告
        
        Args:
            rank_df: 排名后的DataFrame
            score_column: 得分列名
            
        Returns:
            报告字典
        """
        report = {
            'total_stocks': len(rank_df),
            'mean_score': rank_df[score_column].mean(),
            'std_score': rank_df[score_column].std(),
            'top_10': [],
            'industry_distribution': {}
        }
        
        # Top 10
        top_10 = rank_df.head(10)[['symbol', 'rank', score_column]]
        report['top_10'] = top_10.to_dict('records')
        
        # 行业分布
        if 'industry' in rank_df.columns:
            industry_counts = rank_df['industry'].value_counts()
            report['industry_distribution'] = industry_counts.to_dict()
        
        return report


def create_ranker(method: str = 'rank') -> StockRanker:
    """创建排名器"""
    return StockRanker(method)


# ==================== 导出 ====================

__all__ = [
    'StockRanker',
    'RankResult',
    'create_ranker',
]
