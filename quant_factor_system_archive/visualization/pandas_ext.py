"""
Pandas 扩展模块
基于 QuantStats extend_pandas 设计

功能:
- Series 扩展方法 (sharpe, sortino, max_drawdown, etc.)
- DataFrame 扩展方法
- 一键报告生成
"""

import pandas as pd
import numpy as np
from typing import Union, Optional
import warnings
warnings.filterwarnings('ignore')


# ========== 注册扩展 ==========

_pandas_extended = False


def extend_pandas():
    """
    为 pandas 扩展量化分析方法
    
    扩展后的 Series 方法:
    - .sharpe()         夏普比率
    - .sortino()        索提诺比率
    - .calmar()         卡玛比率
    - .max_drawdown()   最大回撤
    - .volatility()     波动率
    - .cagr()           年化收益
    - .win_rate()       胜率
    - .avg_win()        平均盈利
    - .avg_loss()       平均亏损
    - .profit_factor()  盈利因子
    
    使用示例:
        import quantstats as qs
        qs.extend_pandas()
        
        returns.sharpe()
        returns.max_drawdown()
    """
    global _pandas_extended
    
    if _pandas_extended:
        return
    
    # 注册 Series 访问器
    @pd.api.extensions.register_series_accessor('quant')
    class QuantSeriesAccessor:
        """Series 量化分析访问器"""
        
        def __init__(self, series):
            self._series = series
        
        def sharpe(self, rf: float = 0.0, periods: int = 252) -> float:
            """计算夏普比率"""
            excess = self._series - rf / periods
            return (excess.mean() / (self._series.std() + 1e-8)) * np.sqrt(periods)
        
        def sortino(self, rf: float = 0.0, periods: int = 252) -> float:
            """计算索提诺比率"""
            excess = self._series - rf / periods
            downside = self._series[self._series < rf / periods]
            downside_std = downside.std() if len(downside) > 0 else 0
            return (excess.mean() / (downside_std + 1e-8)) * np.sqrt(periods)
        
        def calmar(self, rf: float = 0.0, periods: int = 252) -> float:
            """计算卡玛比率"""
            cagr = self.cagr(rf=rf, periods=periods)
            dd = self.max_drawdown()
            return cagr / (abs(dd) + 1e-8)
        
        def max_drawdown(self) -> float:
            """计算最大回撤"""
            cum_ret = (1 + self._series).cumprod()
            running_max = cum_ret.expanding().max()
            drawdown = (cum_ret - running_max) / running_max
            return drawdown.min()
        
        def volatility(self, periods: int = 252) -> float:
            """计算年化波动率"""
            return self._series.std() * np.sqrt(periods)
        
        def cagr(self, rf: float = 0.0, periods: int = 252) -> float:
            """计算年化收益 (CAGR)"""
            cum_ret = (1 + self._series).prod()
            n_years = len(self._series) / periods
            return (cum_ret ** (1 / n_years) if n_years > 0 else 0) - 1 - rf
        
        def win_rate(self) -> float:
            """计算胜率"""
            return (self._series > 0).mean()
        
        def avg_win(self) -> float:
            """计算平均盈利"""
            wins = self._series[self._series > 0]
            return wins.mean() if len(wins) > 0 else 0
        
        def avg_loss(self) -> float:
            """计算平均亏损"""
            losses = self._series[self._series < 0]
            return losses.mean() if len(losses) > 0 else 0
        
        def profit_factor(self) -> float:
            """计算盈利因子"""
            gross_profit = self._series[self._series > 0].sum()
            gross_loss = abs(self._series[self._series < 0].sum())
            return gross_profit / (gross_loss + 1e-8)
        
        def skewness(self) -> float:
            """计算偏度"""
            return self._series.skew()
        
        def kurtosis(self) -> float:
            """计算峰度"""
            return self._series.kurtosis()
        
        def tail_ratio(self) -> float:
            """计算尾部比率"""
            return abs(self._series[self._series > 0].mean()) / \
                   abs(self._series[self._series < 0].mean() + 1e-8)
        
        def value_at_risk(self, confidence: float = 0.95) -> float:
            """计算 VaR"""
            return np.percentile(self._series, (1 - confidence) * 100)
        
        def conditional_var(self, confidence: float = 0.95) -> float:
            """计算 CVaR (Expected Shortfall)"""
            var = self.value_at_risk(confidence)
            tail = self._series[self._series <= var]
            return tail.mean() if len(tail) > 0 else var
        
        def to_drawdown_series(self) -> pd.Series:
            """转换为回撤序列"""
            cum_ret = (1 + self._series).cumprod()
            running_max = cum_ret.expanding().max()
            return (cum_ret - running_max) / running_max
        
        def describe(self) -> pd.Series:
            """完整统计描述"""
            return pd.Series({
                'count': len(self._series),
                'mean': self._series.mean(),
                'std': self._series.std(),
                'min': self._series.min(),
                'max': self._series.max(),
                'skewness': self.skewness(),
                'kurtosis': self.kurtosis(),
                'cagr': self.cagr(),
                'volatility': self.volatility(),
                'sharpe': self.sharpe(),
                'sortino': self.sortino(),
                'calmar': self.calmar(),
                'max_drawdown': self.max_drawdown(),
                'win_rate': self.win_rate(),
                'profit_factor': self.profit_factor(),
                'var_95': self.value_at_risk(0.95),
                'cvar_95': self.conditional_var(0.95),
            })
    
    # 注册 DataFrame 访问器
    @pd.api.extensions.register_dataframe_accessor('quant')
    class QuantDataFrameAccessor:
        """DataFrame 量化分析访问器"""
        
        def __init__(self, df):
            self._df = df
        
        def returns(self) -> pd.DataFrame:
            """转换为收益率"""
            return self._df.pct_change()
        
        def cumulative(self) -> pd.DataFrame:
            """计算累计收益"""
            return (1 + self._df.pct_change()).cumprod()


# ========== 便捷函数 ==========

def sharpe(returns: pd.Series, rf: float = 0.0, periods: int = 252) -> float:
    """计算夏普比率"""
    if returns.empty or returns.std() == 0:
        return 0.0
    excess = returns - rf / periods
    return (excess.mean() / (returns.std() + 1e-8)) * np.sqrt(periods)


def sortino(returns: pd.Series, rf: float = 0.0, periods: int = 252) -> float:
    """计算索提诺比率"""
    if returns.empty:
        return 0.0
    excess = returns - rf / periods
    downside = returns[returns < rf / periods]
    downside_std = downside.std() if len(downside) > 0 else 0
    return (excess.mean() / (downside_std + 1e-8)) * np.sqrt(periods)


def calmar(returns: pd.Series, rf: float = 0.0, periods: int = 252) -> float:
    """计算卡玛比率"""
    cagr_ret = cagr(returns, rf, periods)
    dd = max_drawdown(returns)
    return cagr_ret / (abs(dd) + 1e-8)


def max_drawdown(returns: pd.Series) -> float:
    """计算最大回撤"""
    if returns.empty:
        return 0.0
    cum_ret = (1 + returns).cumprod()
    running_max = cum_ret.expanding().max()
    drawdown = (cum_ret - running_max) / running_max
    return drawdown.min()


def volatility(returns: pd.Series, periods: int = 252) -> float:
    """计算年化波动率"""
    if returns.empty:
        return 0.0
    return returns.std() * np.sqrt(periods)


def cagr(returns: pd.Series, rf: float = 0.0, periods: int = 252) -> float:
    """计算年化收益 (CAGR)"""
    if returns.empty:
        return 0.0
    cum_ret = (1 + returns).prod()
    n_years = len(returns) / periods
    if n_years == 0:
        return 0.0
    return (cum_ret ** (1 / n_years)) - 1 - rf


def win_rate(returns: pd.Series) -> float:
    """计算胜率"""
    if returns.empty:
        return 0.0
    return (returns > 0).mean()


def profit_factor(returns: pd.Series) -> float:
    """计算盈利因子"""
    if returns.empty:
        return 0.0
    gross_profit = returns[returns > 0].sum()
    gross_loss = abs(returns[returns < 0].sum())
    return gross_profit / (gross_loss + 1e-8)


def value_at_risk(returns: pd.Series, confidence: float = 0.95) -> float:
    """计算 VaR"""
    if returns.empty:
        return 0.0
    return np.percentile(returns, (1 - confidence) * 100)


def conditional_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """计算 CVaR (Expected Shortfall)"""
    if returns.empty:
        return 0.0
    var = value_at_risk(returns, confidence)
    tail = returns[returns <= var]
    return tail.mean() if len(tail) > 0 else var


def describe(returns: pd.Series) -> pd.Series:
    """完整统计描述"""
    if returns.empty:
        return pd.Series()
    
    return pd.Series({
        'count': len(returns),
        'mean': returns.mean(),
        'std': returns.std(),
        'min': returns.min(),
        'max': returns.max(),
        'skewness': returns.skew(),
        'kurtosis': returns.kurtosis(),
        'cagr': cagr(returns),
        'volatility': volatility(returns),
        'sharpe': sharpe(returns),
        'sortino': sortino(returns),
        'calmar': calmar(returns),
        'max_drawdown': max_drawdown(returns),
        'win_rate': win_rate(returns),
        'profit_factor': profit_factor(returns),
        'var_95': value_at_risk(returns, 0.95),
        'cvar_95': conditional_var(returns, 0.95),
    })


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 测试 Pandas 扩展模块")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 创建测试数据
    dates = pd.date_range('2024-01-01', periods=500, freq='B')
    returns = pd.Series(np.random.randn(500) * 0.02, index=dates)
    
    print("\n1. 测试便捷函数:")
    print(f"   Sharpe: {sharpe(returns):.4f}")
    print(f"   Sortino: {sortino(returns):.4f}")
    print(f"   Calmar: {calmar(returns):.4f}")
    print(f"   Max Drawdown: {max_drawdown(returns):.4f}")
    print(f"   Win Rate: {win_rate(returns):.2%}")
    print(f"   Profit Factor: {profit_factor(returns):.4f}")
    
    print("\n2. 测试 describe():")
    stats = describe(returns)
    print(stats)
    
    print("\n3. 测试 extend_pandas():")
    extend_pandas()
    
    print(f"   returns.quant.sharpe(): {returns.quant.sharpe():.4f}")
    print(f"   returns.quant.max_drawdown(): {returns.quant.max_drawdown():.4f}")
    print(f"   returns.quant.describe():")
    print(returns.quant.describe())
    
    print("\n" + "=" * 60)
    print("✅ Pandas 扩展模块测试完成!")
    print("=" * 60)
