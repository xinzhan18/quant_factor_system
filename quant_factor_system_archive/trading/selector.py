"""
选股与组合模块
提供单因子选股、多因子组合、持仓管理功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


@dataclass
class StockPosition:
    """股票持仓"""
    stock_code: str
    factor_value: float
    rank: int
    weight: float
    direction: str = "long"  # long or short


@dataclass
class Portfolio:
    """投资组合"""
    name: str
    positions: List[StockPosition] = field(default_factory=list)
    total_value: float = 0.0
    cash: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'positions': [
                {
                    'stock_code': p.stock_code,
                    'factor_value': p.factor_value,
                    'rank': p.rank,
                    'weight': p.weight,
                    'direction': p.direction
                }
                for p in self.positions
            ],
            'total_value': self.total_value,
            'cash': self.cash
        }


class SingleFactorPicker:
    """
    单因子选股器
    基于单个因子值选择股票
    """
    
    def __init__(self, ascending: bool = False):
        """
        初始化
        
        Args:
            ascending: 是否升序排列（True=值越小越好，如PE）
        """
        self.ascending = ascending
    
    def pick_top_n(self, factor_data: pd.DataFrame,
                   n: int = 50,
                   value_col: str = 'value',
                   stock_col: str = 'stock_code') -> List[StockPosition]:
        """
        选取 Top N 股票
        
        Args:
            factor_data: 因子数据 DataFrame
            n: 选取数量
            value_col: 因子值列名
            stock_col: 股票代码列名
            
        Returns:
            持仓列表
        """
        if factor_data.empty:
            return []
        
        # 排序
        sorted_data = factor_data.sort_values(value_col, ascending=self.ascending)
        
        # 选取 Top N
        top_data = sorted_data.head(n)
        
        # 计算权重（等权）
        weight = 1.0 / len(top_data)
        
        # 构建持仓
        positions = []
        for rank, (idx, row) in enumerate(top_data.iterrows()):
            position = StockPosition(
                stock_code=str(row[stock_col]) if stock_col in row.index else str(idx),
                factor_value=row[value_col],
                rank=rank + 1,
                weight=weight,
                direction="long"
            )
            positions.append(position)
        
        return positions
    
    def pick_by_threshold(self, factor_data: pd.DataFrame,
                         threshold: float,
                         direction: str = 'above',
                         value_col: str = 'value',
                         stock_col: str = 'stock_code') -> List[StockPosition]:
        """
        按阈值选股
        
        Args:
            factor_data: 因子数据
            threshold: 阈值
            direction: 方向 ('above' 或 'below')
            value_col: 因子值列名
            stock_col: 股票代码列名
            
        Returns:
            持仓列表
        """
        if factor_data.empty:
            return []
        
        # 筛选
        if direction == 'above':
            filtered = factor_data[factor_data[value_col] > threshold]
        else:
            filtered = factor_data[factor_data[value_col] < threshold]
        
        if filtered.empty:
            return []
        
        # 排序
        sorted_data = filtered.sort_values(value_col, ascending=self.ascending)
        
        # 计算权重
        weight = 1.0 / len(sorted_data)
        
        # 构建持仓
        positions = []
        for rank, (idx, row) in enumerate(sorted_data.iterrows()):
            position = StockPosition(
                stock_code=str(row[stock_col]) if stock_col in row.index else str(idx),
                factor_value=row[value_col],
                rank=rank + 1,
                weight=weight,
                direction="long"
            )
            positions.append(position)
        
        return positions


class MultiFactorCombiner:
    """
    多因子组合器
    合并多个因子，构建复合因子
    """
    
    def __init__(self, method: str = 'zscore_avg'):
        """
        初始化
        
        Args:
            method: 组合方法
                - 'zscore_avg': Z-score 标准化后等权平均
                - 'ic_weight': IC 加权平均
                - 'equal_weight': 等权平均
                - 'optimize': 优化权重
        """
        self.method = method
    
    def standardize_zscore(self, factor: pd.Series) -> pd.Series:
        """
        Z-score 标准化
        
        Args:
            factor: 因子值
            
        Returns:
            标准化后的因子值
        """
        mean = factor.mean()
        std = factor.std()
        
        if std == 0 or pd.isna(std):
            return factor - mean
        
        return (factor - mean) / std
    
    def standardize_rank(self, factor: pd.Series) -> pd.Series:
        """
        排名标准化
        
        Args:
            factor: 因子值
            
        Returns:
            标准化后的因子值 (0-1)
        """
        return factor.rank(pct=True)
    
    def combine(self, factors: Dict[str, pd.Series],
               weights: Dict[str, float] = None,
               standardize_method: str = 'zscore') -> pd.Series:
        """
        合并因子
        
        Args:
            factors: 因子字典
            weights: 权重字典
            standardize_method: 标准化方法
            
        Returns:
            复合因子值
        """
        if not factors:
            return pd.Series()
        
        # 默认等权
        if weights is None:
            weights = {name: 1.0 / len(factors) for name in factors.keys()}
        
        # 标准化并加权
        combined = pd.Series(0, index=list(factors.values())[0].index)
        
        for name, factor in factors.items():
            weight = weights.get(name, 1.0)
            
            # 标准化
            if standardize_method == 'zscore':
                std_factor = self.standardize_zscore(factor)
            elif standardize_method == 'rank':
                std_factor = self.standardize_rank(factor)
            else:
                std_factor = factor
            
            # 累积
            combined += std_factor * weight
        
        return combined
    
    def calculate_ic_weights(self, ic_scores: Dict[str, float]) -> Dict[str, float]:
        """
        基于 IC 计算权重
        
        Args:
            ic_scores: IC 分数字典
            
        Returns:
            权重字典
        """
        if not ic_scores:
            return {}
        
        # 转换为绝对值并归一化
        abs_ic = {name: abs(ic) for name, ic in ic_scores.items()}
        total = sum(abs_ic.values())
        
        if total == 0:
            return {name: 1.0 / len(abs_ic) for name in abs_ic.keys()}
        
        return {name: ic / total for name, ic in abs_ic.items()}


class PortfolioConstructor:
    """
    投资组合构造器
    根据因子得分构建投资组合
    """
    
    def __init__(self, portfolio_type: str = 'long_only'):
        """
        初始化
        
        Args:
            portfolio_type: 组合类型
                - 'long_only': 只做多
                - 'long_short': 多空组合
                - 'market_neutral': 市场中性
        """
        self.portfolio_type = portfolio_type
    
    def construct_equal_weight(self, factor_scores: pd.DataFrame,
                             top_n: int = 50,
                             direction: str = 'long') -> Portfolio:
        """
        构造等权组合
        
        Args:
            factor_scores: 因子得分 DataFrame
            top_n: 持仓数量
            direction: 方向 ('long' 或 'short')
            
        Returns:
            投资组合
        """
        if factor_scores.empty:
            return Portfolio(name="Empty")
        
        # 获取得分最高的 N 只股票
        if direction == 'long':
            top = factor_scores.nlargest(top_n, 'score')
        else:
            top = factor_scores.nsmallest(top_n, 'score')
        
        # 等权
        weight = 1.0 / len(top)
        
        # 构建持仓
        positions = []
        for rank, (idx, row) in enumerate(top.iterrows()):
            position = StockPosition(
                stock_code=str(idx[1]) if isinstance(idx, tuple) else str(idx),
                factor_value=row['score'],
                rank=rank + 1,
                weight=weight,
                direction=direction
            )
            positions.append(position)
        
        return Portfolio(
            name=f"EqualWeight_{direction}_{top_n}",
            positions=positions,
            total_value=1.0
        )
    
    def construct_cap_weight(self, factor_scores: pd.DataFrame,
                           market_cap: pd.Series,
                           top_n: int = 50,
                           direction: str = 'long') -> Portfolio:
        """
        构造市值加权组合
        
        Args:
            factor_scores: 因子得分 DataFrame
            market_cap: 市值序列
            top_n: 持仓数量
            direction: 方向
            
        Returns:
            投资组合
        """
        if factor_scores.empty or market_cap.empty:
            return Portfolio(name="Empty")
        
        # 合并得分和市值
        scores_with_cap = factor_scores.copy()
        
        if isinstance(scores_with_cap.index, pd.MultiIndex):
            codes = scores_with_cap.index.get_level_values('stock_code')
            if 'stock_code' not in scores_with_cap.columns:
                scores_with_cap['stock_code'] = codes
        else:
            scores_with_cap['stock_code'] = scores_with_cap.index
        
        # 合并市值
        scores_with_cap = scores_with_cap.reset_index().merge(
            market_cap.reset_index(),
            on='stock_code',
            how='left'
        )
        
        # 获取 Top N
        if direction == 'long':
            top = scores_with_cap.nlargest(top_n, 'score')
        else:
            top = scores_with_cap.nsmallest(top_n, 'score')
        
        # 市值加权
        total_cap = top['market_cap'].sum()
        
        positions = []
        for rank, (_, row) in enumerate(top.iterrows()):
            weight = row['market_cap'] / total_cap
            position = StockPosition(
                stock_code=str(row['stock_code']),
                factor_value=row['score'],
                rank=rank + 1,
                weight=weight,
                direction=direction
            )
            positions.append(position)
        
        return Portfolio(
            name=f"CapWeight_{direction}_{top_n}",
            positions=positions,
            total_value=1.0
        )
    
    def construct_factor_weight(self, factor_scores: pd.DataFrame,
                               factor_weights: Dict[str, float],
                               top_n: int = 50) -> Portfolio:
        """
        构造因子加权组合
        
        Args:
            factor_scores: 因子得分 DataFrame
            factor_weights: 各因子权重
            top_n: 持仓数量
            
        Returns:
            投资组合
        """
        if factor_scores.empty:
            return Portfolio(name="Empty")
        
        # 计算综合得分
        scores = factor_scores.copy()
        
        if isinstance(scores.index, pd.MultiIndex):
            codes = scores.index.get_level_values('stock_code')
        else:
            codes = scores.index
        
        scores = scores.reset_index()
        
        # 计算加权得分
        weighted_score = pd.Series(0, index=scores.index)
        for factor, weight in factor_weights.items():
            if factor in scores.columns:
                weighted_score += scores[factor] * weight
        
        scores['score'] = weighted_score
        
        # 获取 Top N
        top = scores.nlargest(top_n, 'score')
        
        # 等权
        weight = 1.0 / len(top)
        
        positions = []
        for rank, (_, row) in enumerate(top.iterrows()):
            stock_code = str(row['stock_code']) if 'stock_code' in row.index else str(row['index'])
            position = StockPosition(
                stock_code=stock_code,
                factor_value=row['score'],
                rank=rank + 1,
                weight=weight,
                direction="long"
            )
            positions.append(position)
        
        return Portfolio(
            name=f"FactorWeight_{top_n}",
            positions=positions,
            total_value=1.0
        )
    
    def construct_long_short(self, factor_scores: pd.DataFrame,
                            top_n: int = 50,
                            hedge_ratio: float = 1.0) -> Tuple[Portfolio, Portfolio]:
        """
        构造多空组合
        
        Args:
            factor_scores: 因子得分 DataFrame
            top_n: 多空各 N 只
            hedge_ratio: 对冲比率
            
        Returns:
            (多头组合, 空头组合)
        """
        long = self.construct_equal_weight(factor_scores, top_n, 'long')
        short = self.construct_equal_weight(factor_scores, top_n, 'short')
        
        return long, short


class WeightOptimizer:
    """
    权重优化器
    基于不同目标优化因子权重
    """
    
    def __init__(self, objective: str = 'sharpe'):
        """
        初始化
        
        Args:
            objective: 优化目标 ('sharpe', 'return', 'ic')
        """
        self.objective = objective
    
    def optimize_equal_ic(self, ic_scores: Dict[str, float],
                        factor_returns: Dict[str, pd.Series]) -> Dict[str, float]:
        """
        基于 IC 等权优化
        
        Args:
            ic_scores: IC 分数
            factor_returns: 各因子收益序列
            
        Returns:
            最优权重
        """
        # 使用绝对 IC 作为权重
        abs_ic = {name: abs(ic) for name, ic in ic_scores.items() if not pd.isna(ic)}
        total = sum(abs_ic.values())
        
        if total == 0:
            return {name: 1.0 / len(abs_ic) for name in abs_ic.keys()}
        
        return {name: ic / total for name, ic in abs_ic.items()}
    
    def optimize_max_ic(self, ic_scores: Dict[str, float]) -> Dict[str, float]:
        """
        最大化 IC 权重
        
        Args:
            ic_scores: IC 分数
            
        Returns:
            权重（IC 为负的设为 0）
        """
        # 只选择 IC 为正的因子
        positive_ic = {name: ic for name, ic in ic_scores.items() 
                      if not pd.isna(ic) and ic > 0}
        
        if not positive_ic:
            return {name: 0 for name in ic_scores.keys()}
        
        # 等权
        return {name: (1.0 / len(positive_ic) if name in positive_ic else 0)
                for name in ic_scores.keys()}
    
    def optimize_diversified(self, factor_correlation: pd.DataFrame,
                            ic_scores: Dict[str, float],
                            target_corr: float = 0.3) -> Dict[str, float]:
        """
        分散化优化
        
        Args:
            factor_correlation: 因子相关性矩阵
            ic_scores: IC 分数
            target_corr: 目标相关性
            
        Returns:
            权重
        """
        # 简化的分散化权重
        # 降低高相关因子的权重
        abs_ic = {name: abs(ic) for name, ic in ic_scores.items()}
        total_ic = sum(abs_ic.values())
        
        if total_ic == 0:
            n = len(ic_scores)
            return {name: 1.0 / n for name in ic_scores.keys()}
        
        # 基础权重
        base_weights = {name: ic / total_ic for name, ic in abs_ic.items()}
        
        # 调整高相关因子的权重
        adjusted_weights = base_weights.copy()
        
        if not factor_correlation.empty:
            for i, name1 in enumerate(factor_correlation.columns):
                for j, name2 in enumerate(factor_correlation.columns):
                    if i < j:
                        corr = factor_correlation.iloc[i, j]
                        if abs(corr) > target_corr:
                            # 降低两个因子的权重
                            adjusted_weights[name1] *= (1 - abs(corr))
                            adjusted_weights[name2] *= (1 - abs(corr))
        
        # 归一化
        total = sum(adjusted_weights.values())
        if total > 0:
            return {name: w / total for name, w in adjusted_weights.items()}
        
        return base_weights


class StockSelector:
    """
    选股引擎
    整合单因子、多因子选股功能
    """
    
    def __init__(self):
        """初始化"""
        self.single_picker = SingleFactorPicker()
        self.multi_combiner = MultiFactorCombiner()
        self.portfolio_constructor = PortfolioConstructor()
    
    def select_single_factor(self,
                           factor_data: pd.DataFrame,
                           n: int = 50,
                           ascending: bool = False,
                           value_col: str = 'value') -> Portfolio:
        """
        单因子选股
        
        Args:
            factor_data: 因子数据
            n: 选股数量
            ascending: 是否升序
            value_col: 因子值列
            
        Returns:
            投资组合
        """
        self.single_picker.ascending = ascending
        
        positions = self.single_picker.pick_top_n(
            factor_data, n, value_col
        )
        
        return Portfolio(
            name=f"SingleFactor_{n}",
            positions=positions,
            total_value=1.0
        )
    
    def select_multi_factor(self,
                          factors: Dict[str, pd.Series],
                          ic_scores: Dict[str, float] = None,
                          factor_returns: Dict[str, pd.Series] = None,
                          factor_correlation: pd.DataFrame = None,
                          n: int = 50,
                          method: str = 'zscore_avg') -> Portfolio:
        """
        多因子选股
        
        Args:
            factors: 因子字典
            ic_scores: IC 分数（可选，用于权重）
            factor_returns: 因子收益（可选）
            factor_correlation: 相关性矩阵（可选）
            n: 选股数量
            method: 组合方法
            
        Returns:
            投资组合
        """
        # 计算权重
        weights = None
        
        if method == 'ic_weight' and ic_scores:
            weights = self.multi_combiner.calculate_ic_weights(ic_scores)
        elif method == 'optimize' and ic_scores and factor_correlation is not None:
            optimizer = WeightOptimizer()
            weights = optimizer.optimize_diversified(
                factor_correlation, ic_scores
            )
        
        # 合并因子
        combined_score = self.multi_combiner.combine(factors, weights, 'zscore')
        
        # 构建组合
        scores_df = pd.DataFrame({'score': combined_score})
        
        portfolio = self.portfolio_constructor.construct_equal_weight(
            scores_df, n, 'long'
        )
        
        return portfolio
    
    def generate_trading_signals(self, portfolio: Portfolio,
                                current_positions: List[str] = None) -> Dict[str, str]:
        """
        生成交易信号
        
        Args:
            portfolio: 目标组合
            current_positions: 当前持仓
            
        Returns:
            交易信号字典 {stock_code: signal}
        """
        if current_positions is None:
            current_positions = []
        
        signals = {}
        
        target_stocks = {p.stock_code for p in portfolio.positions}
        
        # 卖出信号（当前有但目标没有）
        for stock in current_positions:
            if stock not in target_stocks:
                signals[stock] = 'sell'
        
        # 买入信号（目标有但当前没有或权重增加）
        for position in portfolio.positions:
            if position.stock_code not in current_positions:
                signals[position.stock_code] = 'buy'
            elif position.weight > 0.01:  # 权重增加的
                signals[position.stock_code] = 'hold'
        
        return signals


# ========== 便捷函数 ==========

def single_factor_pick(factor_data: pd.DataFrame,
                     n: int = 50,
                     ascending: bool = False) -> List[Dict]:
    """
    快速单因子选股
    
    Args:
        factor_data: 因子数据
        n: 选股数量
        ascending: 是否升序
        
    Returns:
        选股结果列表
    """
    picker = SingleFactorPicker(ascending)
    positions = picker.pick_top_n(factor_data, n)
    
    return [
        {
            'stock_code': p.stock_code,
            'factor_value': p.factor_value,
            'rank': p.rank,
            'weight': p.weight
        }
        for p in positions
    ]


def multi_factor_combine(factors: Dict[str, pd.Series],
                        weights: Dict[str, float] = None) -> pd.Series:
    """
    快速多因子合并
    
    Args:
        factors: 因子字典
        weights: 权重
        
    Returns:
        复合因子
    """
    combiner = MultiFactorCombiner()
    return combiner.combine(factors, weights)


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 测试选股与组合模块")
    print("=" * 60)
    
    import numpy as np
    np.random.seed(42)
    
    # 创建测试数据
    n_stocks = 500
    n_dates = 100
    
    dates = pd.date_range('2024-01-01', periods=n_dates, freq='B')
    symbols = [f'STOCK_{i:04d}' for i in range(n_stocks)]
    
    # 多Index 数据
    index_tuples = []
    momentum_vals = []
    value_vals = []
    quality_vals = []
    
    for symbol in symbols:
        for date in dates:
            index_tuples.append((symbol, date))
            momentum_vals.append(np.random.randn())
            value_vals.append(np.random.randn() * 0.5 + 0.1)
            quality_vals.append(np.random.uniform(0.05, 0.25))
    
    multi_index = pd.MultiIndex.from_tuples(index_tuples, names=['symbol', 'date'])
    
    factors = {
        'Momentum': pd.Series(momentum_vals, index=multi_index),
        'Value': pd.Series(value_vals, index=multi_index),
        'Quality': pd.Series(quality_vals, index=multi_index)
    }
    
    print("\n1. 测试单因子选股:")
    picker = SingleFactorPicker()
    
    # 获取最新的因子数据
    latest_momentum = factors['Momentum'].groupby(level='symbol').last()
    latest_momentum.name = 'value'
    latest_momentum.index.name = 'stock_code'
    
    top_stocks = picker.pick_top_n(latest_momentum.reset_index(), n=10)
    print(f"   选取 {len(top_stocks)} 只股票")
    print(f"   第1只: {top_stocks[0].stock_code}, 因子值: {top_stocks[0].factor_value:.4f}")
    
    print("\n2. 测试多因子合并:")
    combiner = MultiFactorCombiner()
    combined = combiner.combine(factors)
    print(f"   复合因子形状: {combined.shape}")
    
    print("\n3. 测试组合构造:")
    constructor = PortfolioConstructor()
    
    # 构建因子得分 DataFrame
    scores = combined.groupby(level='symbol').last().reset_index()
    scores.columns = ['stock_code', 'score']
    
    portfolio = constructor.construct_equal_weight(scores, top_n=20)
    print(f"   组合名称: {portfolio.name}")
    print(f"   持仓数量: {len(portfolio.positions)}")
    
    print("\n4. 测试权重优化:")
    optimizer = WeightOptimizer()
    ic_scores = {'Momentum': 0.05, 'Value': 0.03, 'Quality': 0.02}
    weights = optimizer.optimize_equal_ic(ic_scores, None)
    print(f"   最优权重: {weights}")
    
    print("\n5. 测试选股引擎:")
    selector = StockSelector()
    
    portfolio = selector.select_multi_factor(
        factors,
        ic_scores=ic_scores,
        n=30,
        method='ic_weight'
    )
    print(f"   选股数量: {len(portfolio.positions)}")
    
    print("\n" + "=" * 60)
    print("✅ 选股与组合模块测试完成!")
    print("=" * 60)
