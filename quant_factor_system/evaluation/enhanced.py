"""
增强的因子评估模块
提供 IC 序列分析、分组收益分析、因子相关性等功能
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


@dataclass
class EnhancedFactorResult:
    """增强的因子评估结果"""
    factor_name: str
    
    # 基础指标
    ic: float = 0.0
    ic_ir: float = 0.0
    ic_sign_ratio: float = 0.0
    ic_std: float = 0.0
    
    # IC 序列
    ic_series: pd.Series = None
    
    # 分组收益
    group_returns: Dict[str, float] = None
    group_cum_returns: Dict[str, pd.Series] = None
    
    # 换手率
    turnover: float = 0.0
    
    # 收益统计
    long_short_return: float = 0.0
    long_short_sharpe: float = 0.0
    max_drawdown: float = 0.0
    
    # 相关性
    factor_correlation: pd.DataFrame = None
    
    # IC 衰减
    ic_decay: pd.Series = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            'factor_name': self.factor_name,
            'ic': self.ic,
            'ic_ir': self.ic_ir,
            'ic_sign_ratio': self.ic_sign_ratio,
            'ic_std': self.ic_std,
            'turnover': self.turnover,
            'long_short_return': self.long_short_return,
            'long_short_sharpe': self.long_short_sharpe,
            'max_drawdown': self.max_drawdown,
        }
        
        # 序列化复杂对象
        if self.ic_series is not None:
            result['ic_series'] = self.ic_series.to_dict()
        
        if self.group_returns is not None:
            result['group_returns'] = self.group_returns
        
        if self.factor_correlation is not None:
            result['factor_correlation'] = self.factor_correlation.to_dict()
        
        if self.ic_decay is not None:
            result['ic_decay'] = self.ic_decay.to_dict()
        
        return result


class EnhancedICAnalyzer:
    """
    增强的 IC 分析器
    提供 IC 序列、滚动 IC、IC 衰减等分析
    """
    
    def __init__(self, rolling_window: int = 60):
        """
        初始化
        
        Args:
            rolling_window: 滚动 IC 窗口
        """
        self.rolling_window = rolling_window
    
    def calculate_ic(self, factor: pd.Series, 
                    returns: pd.Series) -> Dict[str, float]:
        """
        计算基础 IC 统计
        
        Args:
            factor: 因子值
            returns: 收益率
            
        Returns:
            IC 统计字典
        """
        # 对齐
        common_idx = factor.dropna().index.intersection(returns.dropna().index)
        if len(common_idx) < 30:
            return {'ic': 0, 'ic_ir': 0, 'ic_sign_ratio': 0, 'ic_std': 0}
        
        f = factor.loc[common_idx].astype(float)
        r = returns.loc[common_idx].astype(float)
        
        # IC
        ic = f.corr(r)
        
        # IC 标准差
        ic_std = f.std()
        
        # IC IR
        ic_ir = abs(ic) / (ic_std + 1e-8)
        
        # 胜率
        ic_sign_ratio = (np.sign(f.values) == np.sign(r.values)).mean()
        
        return {
            'ic': ic,
            'ic_ir': ic_ir,
            'ic_sign_ratio': ic_sign_ratio,
            'ic_std': ic_std,
            'num_samples': len(f)
        }
    
    def calculate_ic_series(self, factor: pd.Series,
                           returns: pd.Series,
                           period: str = 'M') -> pd.Series:
        """
        计算 IC 时间序列（按月/年聚合）
        
        Args:
            factor: 因子值
            returns: 收益率
            period: 聚合周期 ('D', 'W', 'M', 'Q', 'Y')
            
        Returns:
            IC 序列
        """
        # 对齐
        common_idx = factor.dropna().index.intersection(returns.dropna().index)
        if len(common_idx) < 30:
            return pd.Series()
        
        data = pd.DataFrame({
            'factor': factor.loc[common_idx],
            'returns': returns.loc[common_idx]
        })
        
        # 处理 MultiIndex
        if isinstance(data.index, pd.MultiIndex):
            # 使用日期级别索引
            date_idx = data.index.get_level_values('date')
        else:
            date_idx = data.index
        
        # 按周期聚合
        if period == 'D':
            data['period'] = date_idx
        elif period == 'W':
            data['period'] = date_idx.to_period('W').to_timestamp()
        elif period == 'M':
            data['period'] = date_idx.to_period('M').to_timestamp()
        elif period == 'Q':
            data['period'] = date_idx.to_period('Q').to_timestamp()
        elif period == 'Y':
            data['period'] = date_idx.to_period('Y').to_timestamp()
        else:
            data['period'] = date_idx
        
        # 计算周期 IC
        ic_series = data.groupby('period').apply(
            lambda x: x['factor'].corr(x['returns']) if len(x) > 10 else np.nan
        )
        
        return ic_series
    
    def calculate_rolling_ic(self, factor: pd.Series,
                            returns: pd.Series,
                            window: int = None) -> pd.Series:
        """
        计算滚动 IC
        
        Args:
            factor: 因子值
            returns: 收益率
            window: 滚动窗口
            
        Returns:
            滚动 IC 序列
        """
        if window is None:
            window = self.rolling_window
        
        # 对齐
        common_idx = factor.dropna().index.intersection(returns.dropna().index)
        if len(common_idx) < window + 10:
            return pd.Series()
        
        data = pd.DataFrame({
            'factor': factor.loc[common_idx],
            'returns': returns.loc[common_idx]
        })
        
        # 滚动计算 IC
        rolling_ic = data['factor'].rolling(window=window).corr(data['returns'])
        
        return rolling_ic
    
    def calculate_ic_distribution(self, factor: pd.Series,
                                   returns: pd.Series) -> Dict[str, Any]:
        """
        计算 IC 分布统计
        
        Args:
            factor: 因子值
            returns: 收益率
            
        Returns:
            IC 分布统计
        """
        # 对齐
        common_idx = factor.dropna().index.intersection(returns.dropna().index)
        if len(common_idx) < 30:
            return {}
        
        f = factor.loc[common_idx].astype(float)
        r = returns.loc[common_idx].astype(float)
        
        # 计算每期 IC
        ic_series = self.calculate_ic_series(f, r, period='D')
        ic_series = ic_series.dropna()
        
        if len(ic_series) < 5:
            return {}
        
        # 分布统计
        return {
            'ic_mean': ic_series.mean(),
            'ic_std': ic_series.std(),
            'ic_min': ic_series.min(),
            'ic_max': ic_series.max(),
            'ic_skewness': ic_series.skew(),
            'ic_kurtosis': ic_series.kurtosis(),
            'ic_t_stat': ic_series.mean() / (ic_series.std() + 1e-8) * np.sqrt(len(ic_series)),
            'ic_series': ic_series
        }
    
    def calculate_ic_decay(self, factor: pd.Series,
                          returns: pd.Series,
                          lags: List[int] = None) -> pd.Series:
        """
        计算 IC 衰减
        
        Args:
            factor: 因子值
            returns: 收益率
            lags: 滞后列表
            
        Returns:
            IC 衰减序列
        """
        if lags is None:
            lags = [1, 2, 3, 4, 5, 10, 20, 60]
        
        # 对齐
        common_idx = factor.dropna().index.intersection(returns.dropna().index)
        if len(common_idx) < max(lags) + 30:
            return pd.Series()
        
        f = factor.loc[common_idx].astype(float)
        r = returns.loc[common_idx].astype(float)
        
        decay = {}
        
        for lag in lags:
            # 因子滞后，收益不滞后
            f_lagged = f.shift(lag)
            
            common = f_lagged.dropna().index.intersection(r.index)
            
            if len(common) > 30:
                ic = f_lagged.loc[common].corr(r.loc[common])
                decay[f'lag_{lag}'] = ic
        
        return pd.Series(decay)


class GroupReturnsAnalyzer:
    """
    分组收益分析器
    提供分组净值曲线、换手率、最大回撤等分析
    """
    
    def __init__(self, num_groups: int = 5):
        """
        初始化
        
        Args:
            num_groups: 分组数
        """
        self.num_groups = num_groups
    
    def create_groups(self, factor: pd.Series,
                      n_groups: int = None) -> pd.Series:
        """
        创建分组
        
        Args:
            factor: 因子值
            n_groups: 分组数
            
        Returns:
            分组标签
        """
        if n_groups is None:
            n_groups = self.num_groups
        
        # 去极值后分五组
        factor_clean = factor.dropna()
        if len(factor_clean) < n_groups:
            return pd.Series(index=factor.index)
        
        try:
            groups = pd.qcut(factor_clean, q=n_groups, labels=[f'Q{i+1}' for i in range(n_groups)])
        except:
            # 如果分位数相同，使用 rank
            groups = pd.qcut(factor_clean.rank(method='first'), q=n_groups, labels=[f'Q{i+1}' for i in range(n_groups)])
        
        return groups.reindex(factor.index)
    
    def calculate_group_returns(self, factor: pd.Series,
                                returns: pd.Series,
                                n_groups: int = None) -> Dict[str, float]:
        """
        计算各组平均收益
        
        Args:
            factor: 因子值
            returns: 收益率
            n_groups: 分组数
            
        Returns:
            各组收益字典
        """
        if n_groups is None:
            n_groups = self.num_groups
        
        # 创建分组
        groups = self.create_groups(factor, n_groups)
        
        # 对齐
        common_idx = groups.dropna().index.intersection(returns.dropna().index)
        if len(common_idx) < 100:
            return {}
        
        g = groups.loc[common_idx]
        r = returns.loc[common_idx]
        
        # 计算每组收益
        group_rets = {}
        for name in [f'Q{i+1}' for i in range(n_groups)]:
            mask = g == name
            if mask.sum() > 0:
                group_rets[name] = r[mask].mean()
        
        return group_rets
    
    def calculate_cum_returns(self, factor: pd.Series,
                              returns: pd.Series,
                              n_groups: int = None) -> Dict[str, pd.Series]:
        """
        计算各组累计收益
        
        Args:
            factor: 因子值
            returns: 收益率
            n_groups: 分组数
            
        Returns:
            各组累计收益序列
        """
        if n_groups is None:
            n_groups = self.num_groups
        
        # 创建分组
        groups = self.create_groups(factor, n_groups)
        
        # 对齐
        common_idx = groups.dropna().index.intersection(returns.dropna().index)
        if len(common_idx) < 100:
            return {}
        
        g = groups.loc[common_idx]
        r = returns.loc[common_idx]
        
        # 计算每组累计收益
        cum_rets = {}
        for name in [f'Q{i+1}' for i in range(n_groups)]:
            mask = g == name
            if mask.sum() > 0:
                group_ret = r[mask]
                # 转为日期索引
                cum_ret = (1 + group_ret).cumprod() - 1
                cum_rets[name] = cum_ret
        
        return cum_rets
    
    def calculate_turnover(self, factor: pd.Series,
                          n_groups: int = None) -> float:
        """
        计算分组换手率
        
        Args:
            factor: 因子值
            n_groups: 分组数
            
        Returns:
            平均换手率
        """
        if n_groups is None:
            n_groups = self.num_groups
        
        groups = self.create_groups(factor, n_groups)
        groups = groups.dropna()
        
        if len(groups) < n_groups * 2:
            return 0.0
        
        # 计算相邻期分组变化
        group_change = groups != groups.shift(1)
        turnover = group_change.mean()
        
        return turnover
    
    def calculate_max_drawdown(self, returns: pd.Series) -> float:
        """
        计算最大回撤
        
        Args:
            returns: 收益率序列
            
        Returns:
            最大回撤
        """
        cum_ret = (1 + returns).cumprod()
        running_max = cum_ret.expanding().max()
        drawdown = (cum_ret - running_max) / running_max
        max_dd = drawdown.min()
        
        return max_dd
    
    def calculate_group_stats(self, factor: pd.Series,
                             returns: pd.Series,
                             n_groups: int = None) -> Dict[str, Any]:
        """
        计算分组完整统计
        
        Args:
            factor: 因子值
            returns: 收益率
            n_groups: 分组数
            
        Returns:
            完整统计字典
        """
        if n_groups is None:
            n_groups = self.num_groups
        
        # 创建分组
        groups = self.create_groups(factor, n_groups)
        
        # 对齐
        common_idx = groups.dropna().index.intersection(returns.dropna().index)
        if len(common_idx) < 100:
            return {}
        
        g = groups.loc[common_idx]
        r = returns.loc[common_idx]
        
        stats = {}
        
        for name in [f'Q{i+1}' for i in range(n_groups)]:
            mask = g == name
            group_ret = r[mask]
            
            if len(group_ret) > 0:
                stats[name] = {
                    'mean_return': group_ret.mean(),
                    'std': group_ret.std(),
                    'sharpe': group_ret.mean() / (group_ret.std() + 1e-8) * np.sqrt(252) if group_ret.std() > 0 else 0,
                    'max_drawdown': self.calculate_max_drawdown(group_ret),
                    'count': mask.sum()
                }
        
        # 多空统计
        if 'Q1' in stats and 'Q5' in stats:
            ls_ret = stats['Q5']['mean_return'] - stats['Q1']['mean_return']
            ls_std = np.sqrt(stats['Q5']['std']**2 + stats['Q1']['std']**2)
            stats['long_short'] = {
                'return': ls_ret,
                'sharpe': ls_ret / (ls_std + 1e-8) * np.sqrt(252) if ls_std > 0 else 0
            }
        
        return stats


class FactorCorrelator:
    """
    因子相关性分析器
    """
    
    def __init__(self, threshold: float = 0.7):
        """
        初始化
        
        Args:
            threshold: 高相关阈值
        """
        self.threshold = threshold
    
    def calculate_correlation(self, factor_data: pd.DataFrame) -> pd.DataFrame:
        """
        计算因子相关性矩阵
        
        Args:
            factor_data: 因子数据 DataFrame
            
        Returns:
            相关性矩阵
        """
        if factor_data.empty or factor_data.shape[1] < 2:
            return pd.DataFrame()
        
        return factor_data.corr()
    
    def calculate_ic_correlation(self, factors: Dict[str, pd.Series],
                                returns: pd.Series) -> pd.DataFrame:
        """
        计算因子 IC 相关性
        
        Args:
            factors: 因子字典
            returns: 收益率
            
        Returns:
            IC 相关性矩阵
        """
        ic_data = {}
        
        for name, factor in factors.items():
            # 计算每期 IC
            common_idx = factor.dropna().index.intersection(returns.dropna().index)
            if len(common_idx) < 30:
                continue
            
            f = factor.loc[common_idx]
            r = returns.loc[common_idx]
            
            # 按日期计算滚动 IC
            ic_series = f.rolling(20).corr(r)
            ic_data[name] = ic_series
        
        if len(ic_data) < 2:
            return pd.DataFrame()
        
        ic_df = pd.DataFrame(ic_data)
        return ic_df.corr()
    
    def find_high_correlation(self, corr_matrix: pd.DataFrame) -> List[Tuple[str, str, float]]:
        """
        找出高相关因子对
        
        Args:
            corr_matrix: 相关性矩阵
            
        Returns:
            高相关因子对列表
        """
        high_corr = []
        
        if corr_matrix.empty:
            return high_corr
        
        for i in range(len(corr_matrix.columns)):
            for j in range(i + 1, len(corr_matrix.columns)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) >= self.threshold:
                    high_corr.append((
                        corr_matrix.columns[i],
                        corr_matrix.columns[j],
                        corr_val
                    ))
        
        return high_corr


class EnhancedEvaluator:
    """
    增强的因子评估器
    整合 IC 分析、分组分析、相关性分析
    """
    
    def __init__(self, num_groups: int = 5):
        """
        初始化
        
        Args:
            num_groups: 分组数
        """
        self.num_groups = num_groups
        
        self.ic_analyzer = EnhancedICAnalyzer()
        self.group_analyzer = GroupReturnsAnalyzer(num_groups)
        self.correlator = FactorCorrelator()
    
    def evaluate(self, factor_name: str,
                factor: pd.Series,
                returns: pd.Series,
                save_to_db: bool = False,
                db=None) -> EnhancedFactorResult:
        """
        完整评估因子
        
        Args:
            factor_name: 因子名称
            factor: 因子值
            returns: 收益率
            save_to_db: 是否保存到数据库
            db: 数据库实例
            
        Returns:
            增强评估结果
        """
        result = EnhancedFactorResult(factor_name=factor_name)
        
        # 1. IC 分析
        ic_stats = self.ic_analyzer.calculate_ic(factor, returns)
        result.ic = ic_stats['ic']
        result.ic_ir = ic_stats['ic_ir']
        result.ic_sign_ratio = ic_stats['ic_sign_ratio']
        result.ic_std = ic_stats['ic_std']
        
        # IC 序列
        result.ic_series = self.ic_analyzer.calculate_ic_series(factor, returns, period='M')
        
        # IC 衰减
        result.ic_decay = self.ic_analyzer.calculate_ic_decay(factor, returns)
        
        # 2. 分组收益分析
        group_rets = self.group_analyzer.calculate_group_returns(factor, returns)
        result.group_returns = group_rets
        
        group_cum_rets = self.group_analyzer.calculate_cum_returns(factor, returns)
        result.group_cum_returns = group_cum_rets
        
        # 换手率
        result.turnover = self.group_analyzer.calculate_turnover(factor)
        
        # 多空收益
        if 'Q1' in group_rets and 'Q5' in group_rets:
            result.long_short_return = group_rets['Q5'] - group_rets['Q1']
        
        # 3. 保存到数据库
        if save_to_db and db is not None:
            db.save_evaluation(factor_name, {
                'eval_date': datetime.now().strftime('%Y-%m-%d'),
                'ic': result.ic,
                'ic_ir': result.ic_ir,
                'ic_std': result.ic_std,
                'win_rate': result.ic_sign_ratio,
                'long_short_return': result.long_short_return,
                'num_groups': self.num_groups,
                'group_returns': result.group_returns,
                'ic_series': result.ic_series.to_dict() if result.ic_series is not None else {},
                'ic_decay': result.ic_decay.to_dict() if result.ic_decay is not None else {}
            })
        
        return result
    
    def evaluate_multiple(self, factors: Dict[str, pd.Series],
                         returns: pd.Series,
                         save_to_db: bool = False,
                         db=None) -> Dict[str, EnhancedFactorResult]:
        """
        批量评估因子
        
        Args:
            factors: 因子字典
            returns: 收益率
            save_to_db: 是否保存到数据库
            db: 数据库实例
            
        Returns:
            评估结果字典
        """
        results = {}
        
        for name, factor in factors.items():
            if factor is None or factor.empty:
                continue
            
            try:
                result = self.evaluate(name, factor, returns, save_to_db, db)
                results[name] = result
            except Exception as e:
                print(f"评估因子 {name} 失败: {e}")
        
        return results
    
    def calculate_factor_correlation(self, factors: Dict[str, pd.Series],
                                    returns: pd.Series) -> Tuple[pd.DataFrame, List]:
        """
        计算因子相关性
        
        Args:
            factors: 因子字典
            returns: 收益率
            
        Returns:
            (相关性矩阵, 高相关对列表)
        """
        # IC 相关性
        ic_corr = self.correlator.calculate_ic_correlation(factors, returns)
        
        # 原始因子相关性
        factor_df = pd.DataFrame(factors)
        raw_corr = self.correlator.calculate_correlation(factor_df)
        
        # 高相关对
        high_corr = self.correlator.find_high_correlation(ic_corr)
        
        return ic_corr, raw_corr, high_corr


# ========== 便捷函数 ==========

def evaluate_factor(factor_name: str,
                   factor: pd.Series,
                   returns: pd.Series,
                   num_groups: int = 5) -> EnhancedFactorResult:
    """
    快速评估因子
    
    Args:
        factor_name: 因子名称
        factor: 因子值
        returns: 收益率
        num_groups: 分组数
        
    Returns:
        评估结果
    """
    evaluator = EnhancedEvaluator(num_groups)
    return evaluator.evaluate(factor_name, factor, returns)


if __name__ == '__main__':
    # 测试
    print("=" * 60)
    print("🧪 测试增强评估模块")
    print("=" * 60)
    
    import numpy as np
    np.random.seed(42)
    
    # 创建测试数据
    dates = pd.date_range('2023-01-01', periods=500, freq='B')
    n_stocks = 100
    
    # 因子数据
    factor_data = {}
    for i in range(n_stocks):
        factor_data[f'STOCK_{i:03d}'] = pd.Series(
            np.random.randn(500),
            index=dates
        )
    
    # 收益数据
    returns_data = {}
    for i in range(n_stocks):
        returns_data[f'STOCK_{i:03d}'] = pd.Series(
            np.random.randn(500) * 0.02,
            index=dates
        )
    
    # 合并
    factor_all = pd.concat(factor_data)
    returns_all = pd.concat(returns_data)
    
    print("\n1. 测试 IC 分析:")
    ic_analyzer = EnhancedICAnalyzer()
    ic_stats = ic_analyzer.calculate_ic(factor_all, returns_all)
    print(f"   IC: {ic_stats['ic']:.4f}")
    print(f"   IC IR: {ic_stats['ic_ir']:.4f}")
    print(f"   胜率: {ic_stats['ic_sign_ratio']:.2%}")
    
    print("\n2. 测试分组收益分析:")
    group_analyzer = GroupReturnsAnalyzer(num_groups=5)
    group_rets = group_analyzer.calculate_group_returns(factor_all, returns_all)
    print(f"   分组数: {len(group_rets)}")
    print(f"   Q1 收益: {group_rets.get('Q1', 0):.6f}")
    print(f"   Q5 收益: {group_rets.get('Q5', 0):.6f}")
    
    turnover = group_analyzer.calculate_turnover(factor_all)
    print(f"   换手率: {turnover:.2%}")
    
    print("\n3. 测试完整评估:")
    evaluator = EnhancedEvaluator(num_groups=5)
    result = evaluator.evaluate('TestFactor', factor_all, returns_all)
    print(f"   IC: {result.ic:.4f}")
    print(f"   多空收益: {result.long_short_return:.6f}")
    print(f"   IC 序列长度: {len(result.ic_series)}")
    print(f"   IC 衰减长度: {len(result.ic_decay)}")
    
    print("\n4. 测试因子相关性:")
    factors = {
        'Momentum': factor_all,
        'Value': factor_all * 0.5 + np.random.randn(50000) * 0.5,
        'Quality': factor_all * 0.3 + np.random.randn(50000) * 0.7
    }
    ic_corr, raw_corr, high_corr = evaluator.calculate_factor_correlation(factors, returns_all)
    print(f"   IC 相关性矩阵形状: {ic_corr.shape}")
    print(f"   高相关对: {len(high_corr)}")
    
    print("\n" + "=" * 60)
    print("✅ 增强评估模块测试完成!")
    print("=" * 60)
