"""
风险指标模块
基于 QuantStats 实现的风险分析指标

功能:
- 夏普比率 (Sharpe Ratio)
- 索提诺比率 (Sortino Ratio)
- 卡玛比率 (Calmar Ratio)
- 最大回撤 (Maximum Drawdown)
- 风险价值 (VaR)
- 条件风险价值 (CVaR/Expected Shortfall)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional, Any
from dataclasses import dataclass


@dataclass
class RiskMetrics:
    """风险指标结果"""
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_date: str = ""
    recovery_date: str = ""
    value_at_risk: float = 0.0
    conditional_value_at_risk: float = 0.0
    volatility: float = 0.0
    downside_volatility: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'calmar_ratio': self.calmar_ratio,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_date': self.max_drawdown_date,
            'recovery_date': self.recovery_date,
            'value_at_risk': self.value_at_risk,
            'conditional_value_at_risk': self.conditional_value_at_risk,
            'volatility': self.volatility,
            'downside_volatility': self.downside_volatility,
        }


class RiskAnalyzer:
    """
    风险指标分析器
    基于 QuantStats 实现
    """
    
    def __init__(self, risk_free_rate: float = 0.0, trading_days: int = 252):
        """
        初始化
        
        Args:
            risk_free_rate: 年化无风险利率 (默认 0)
            trading_days: 年交易日数 (默认 252)
        """
        self.risk_free_rate = risk_free_rate
        self.trading_days = trading_days
    
    def calculate_sharpe_ratio(self, returns: pd.Series, 
                              rf: float = None,
                              period: str = 'daily') -> float:
        """
        计算夏普比率
        
        Formula: (Rp - Rf) / σp
        
        Args:
            returns: 收益率序列
            rf: 无风险利率 (覆盖默认)
            period: 数据周期 ('daily', 'weekly', 'monthly')
            
        Returns:
            夏普比率
        """
        if returns.empty or returns.std() == 0:
            return 0.0
        
        if rf is None:
            rf = self.risk_free_rate
        
        # 调整无风险利率到对应周期
        if period == 'daily':
            rf_daily = rf / self.trading_days
        elif period == 'weekly':
            rf_daily = rf / 52
        elif period == 'monthly':
            rf_daily = rf / 12
        else:
            rf_daily = rf / self.trading_days
        
        excess_return = returns - rf_daily
        
        return excess_return.mean() / (returns.std() + 1e-8) * np.sqrt(self.trading_days)
    
    def calculate_rolling_sharpe(self, returns: pd.Series,
                                 window: int = 252,
                                 rf: float = None) -> pd.Series:
        """
        计算滚动夏普比率
        
        Args:
            returns: 收益率序列
            window: 滚动窗口
            rf: 无风险利率
            
        Returns:
            滚动夏普序列
        """
        if rf is None:
            rf = self.risk_free_rate
        
        rolling_mean = returns.rolling(window).mean() * self.trading_days
        rolling_std = returns.rolling(window).std() * np.sqrt(self.trading_days)
        
        rf_daily = rf / self.trading_days
        excess_return = rolling_mean - rf_daily
        
        return excess_return / (rolling_std + 1e-8)
    
    def calculate_sortino_ratio(self, returns: pd.Series,
                                rf: float = None,
                                period: str = 'daily') -> float:
        """
        计算索提诺比率
        
        Formula: (Rp - Rf) / σd
        
        where σd is downside deviation
        
        Args:
            returns: 收益率序列
            rf: 无风险利率
            period: 数据周期
            
        Returns:
            索提诺比率
        """
        if returns.empty or returns.std() == 0:
            return 0.0
        
        if rf is None:
            rf = self.risk_free_rate
        
        # 调整无风险利率
        if period == 'daily':
            rf_daily = rf / self.trading_days
        elif period == 'weekly':
            rf_daily = rf / 52
        elif period == 'monthly':
            rf_daily = rf / 12
        else:
            rf_daily = rf / self.trading_days
        
        excess_return = returns - rf_daily
        
        # 下行波动率
        downside = returns[returns < rf_daily]
        downside_std = downside.std() if len(downside) > 0 else 0
        
        return excess_return.mean() / (downside_std + 1e-8) * np.sqrt(self.trading_days)
    
    def calculate_max_drawdown(self, returns: pd.Series) -> Dict[str, Any]:
        """
        计算最大回撤及相关信息
        
        Args:
            returns: 收益率序列
            
        Returns:
            最大回撤信息字典
        """
        if returns.empty:
            return {'max_drawdown': 0, 'max_drawdown_date': '', 'recovery_date': ''}
        
        # 累计收益
        cum_returns = (1 + returns).cumprod()
        
        # 历史最高点
        running_max = cum_returns.expanding().max()
        
        # 回撤序列
        drawdown = (cum_returns - running_max) / running_max
        
        # 最大回撤
        max_dd = drawdown.min()
        
        # 最大回撤日期
        max_dd_idx = drawdown.idxmin()
        if isinstance(max_dd_idx, tuple):
            max_dd_date = max_dd_idx[0]
        else:
            max_dd_date = max_dd_idx
        
        # 恢复日期
        recovery_idx = None
        for i in range(drawdown.index.get_loc(max_dd_idx) + 1, len(drawdown)):
            if drawdown.iloc[i] == 0:
                recovery_idx = drawdown.index[i]
                break
        
        recovery_date = str(recovery_idx) if recovery_idx else "Not Recovered"
        
        return {
            'max_drawdown': max_dd,
            'max_drawdown_date': str(max_dd_date),
            'recovery_date': recovery_date
        }
    
    def calculate_max_drawdown_series(self, returns: pd.Series) -> pd.Series:
        """
        计算回撤序列
        
        Args:
            returns: 收益率序列
            
        Returns:
            回撤序列
        """
        cum_returns = (1 + returns).cumprod()
        running_max = cum_returns.expanding().max()
        drawdown = (cum_returns - running_max) / running_max
        
        return drawdown
    
    def calculate_calmar_ratio(self, returns: pd.Series,
                              rf: float = None) -> float:
        """
        计算卡玛比率
        
        Formula: CAGR / |Max Drawdown|
        
        Args:
            returns: 收益率序列
            rf: 无风险利率
            
        Returns:
            卡玛比率
        """
        # 年化收益率
        cagr = self.calculate_cagr(returns)
        
        # 最大回撤
        max_dd_info = self.calculate_max_drawdown(returns)
        max_dd = abs(max_dd_info['max_drawdown'])
        
        if max_dd == 0:
            return 0.0
        
        # 调整无风险利率
        if rf is not None:
            cagr = cagr - rf
        
        return cagr / (max_dd + 1e-8)
    
    def calculate_cagr(self, returns: pd.Series) -> float:
        """
        计算复合年化增长率
        
        Formula: (End Value / Start Value)^(1/n) - 1
        
        Args:
            returns: 收益率序列
            
        Returns:
            年化收益率
        """
        if returns.empty:
            return 0.0
        
        cum_return = (1 + returns).prod()
        
        # 计算年数
        if isinstance(returns.index, pd.DatetimeIndex):
            years = len(returns) / self.trading_days
        else:
            years = len(returns) / self.trading_days
        
        if years == 0:
            return 0.0
        
        return cum_return ** (1 / years) - 1
    
    def calculate_volatility(self, returns: pd.Series,
                             period: str = 'daily') -> float:
        """
        计算年化波动率
        
        Args:
            returns: 收益率序列
            period: 数据周期
            
        Returns:
            年化波动率
        """
        if returns.empty:
            return 0.0
        
        if period == 'daily':
            return returns.std() * np.sqrt(self.trading_days)
        elif period == 'weekly':
            return returns.std() * np.sqrt(52)
        elif period == 'monthly':
            return returns.std() * np.sqrt(12)
        else:
            return returns.std() * np.sqrt(self.trading_days)
    
    def calculate_value_at_risk(self, returns: pd.Series,
                               confidence: float = 0.95,
                               method: str = 'historical') -> float:
        """
        计算风险价值 (VaR)
        
        Args:
            returns: 收益率序列
            confidence: 置信水平 (0.95, 0.99)
            method: 方法 ('historical', 'parametric', 'monte_carlo')
            
        Returns:
            VaR 值
        """
        if returns.empty:
            return 0.0
        
        if method == 'historical':
            # 历史模拟法
            return np.percentile(returns, (1 - confidence) * 100)
        
        elif method == 'parametric':
            # 参数法 (正态分布)
            z_score = {0.95: 1.645, 0.99: 2.326}
            return returns.mean() - z_score.get(confidence, 1.645) * returns.std()
        
        else:
            # 默认使用历史法
            return np.percentile(returns, (1 - confidence) * 100)
    
    def calculate_conditional_var(self, returns: pd.Series,
                                  confidence: float = 0.95) -> float:
        """
        计算条件风险价值 (CVaR / Expected Shortfall)
        
        Args:
            returns: 收益率序列
            confidence: 置信水平
            
        Returns:
            CVaR 值
        """
        if returns.empty:
            return 0.0
        
        var = self.calculate_value_at_risk(returns, confidence)
        
        # 尾部损失平均值
        tail_losses = returns[returns <= var]
        return tail_losses.mean() if len(tail_losses) > 0 else var
    
    def calculate_all_metrics(self, returns: pd.Series) -> RiskMetrics:
        """
        计算所有风险指标
        
        Args:
            returns: 收益率序列
            
        Returns:
            风险指标结果
        """
        metrics = RiskMetrics()
        
        # 波动率
        metrics.volatility = self.calculate_volatility(returns)
        metrics.downside_volatility = self.calculate_volatility(
            returns[returns < 0]
        ) if len(returns[returns < 0]) > 0 else 0
        
        # 夏普比率
        metrics.sharpe_ratio = self.calculate_sharpe_ratio(returns)
        
        # 索提诺比率
        metrics.sortino_ratio = self.calculate_sortino_ratio(returns)
        
        # 卡玛比率
        metrics.calmar_ratio = self.calculate_calmar_ratio(returns)
        
        # 最大回撤
        dd_info = self.calculate_max_drawdown(returns)
        metrics.max_drawdown = dd_info['max_drawdown']
        metrics.max_drawdown_date = dd_info['max_drawdown_date']
        metrics.recovery_date = dd_info['recovery_date']
        
        # VaR
        metrics.value_at_risk = self.calculate_value_at_risk(returns, 0.95)
        metrics.conditional_value_at_risk = self.calculate_conditional_var(returns, 0.95)
        
        return metrics
    
    def calculate_rolling_metrics(self, returns: pd.Series,
                                  window: int = 252) -> pd.DataFrame:
        """
        计算滚动风险指标
        
        Args:
            returns: 收益率序列
            window: 滚动窗口
            
        Returns:
            滚动指标 DataFrame
        """
        df = pd.DataFrame(index=returns.index)
        
        df['rolling_sharpe'] = self.calculate_rolling_sharpe(returns, window)
        df['rolling_volatility'] = returns.rolling(window).std() * np.sqrt(self.trading_days)
        
        # 滚动最大回撤
        rolling_dd = []
        for i in range(len(returns)):
            if i < window:
                rolling_dd.append(0)
            else:
                window_returns = returns.iloc[i-window:i+1]
                dd_info = self.calculate_max_drawdown(window_returns)
                rolling_dd.append(dd_info['max_drawdown'])
        
        df['rolling_max_dd'] = rolling_dd
        
        return df


# ========== 便捷函数 ==========

def sharpe_ratio(returns: pd.Series, rf: float = 0.0) -> float:
    """计算夏普比率"""
    analyzer = RiskAnalyzer(risk_free_rate=rf)
    return analyzer.calculate_sharpe_ratio(returns)


def sortino_ratio(returns: pd.Series, rf: float = 0.0) -> float:
    """计算索提诺比率"""
    analyzer = RiskAnalyzer(risk_free_rate=rf)
    return analyzer.calculate_sortino_ratio(returns)


def max_drawdown(returns: pd.Series) -> float:
    """计算最大回撤"""
    analyzer = RiskAnalyzer()
    return analyzer.calculate_max_drawdown(returns)['max_drawdown']


def calmar_ratio(returns: pd.Series) -> float:
    """计算卡玛比率"""
    analyzer = RiskAnalyzer()
    return analyzer.calculate_calmar_ratio(returns)


def value_at_risk(returns: pd.Series, confidence: float = 0.95) -> float:
    """计算 VaR"""
    analyzer = RiskAnalyzer()
    return analyzer.calculate_value_at_risk(returns, confidence)


def conditional_var(returns: pd.Series, confidence: float = 0.95) -> float:
    """计算 CVaR"""
    analyzer = RiskAnalyzer()
    return analyzer.calculate_conditional_var(returns, confidence)


if __name__ == '__main__':
    print("=" * 60)
    print("🧪 测试风险指标模块")
    print("=" * 60)
    
    np.random.seed(42)
    
    # 创建测试数据
    dates = pd.date_range('2023-01-01', periods=500, freq='B')
    returns = pd.Series(np.random.randn(500) * 0.02, index=dates)
    
    # 测试
    print("\n1. 测试风险分析器:")
    analyzer = RiskAnalyzer(risk_free_rate=0.03)
    metrics = analyzer.calculate_all_metrics(returns)
    print(f"   夏普比率: {metrics.sharpe_ratio:.4f}")
    print(f"   索提诺比率: {metrics.sortino_ratio:.4f}")
    print(f"   卡玛比率: {metrics.calmar_ratio:.4f}")
    print(f"   最大回撤: {metrics.max_drawdown:.4f}")
    print(f"   VaR (95%): {metrics.value_at_risk:.4f}")
    print(f"   CVaR (95%): {metrics.conditional_value_at_risk:.4f}")
    print(f"   年化波动率: {metrics.volatility:.4f}")
    
    print("\n2. 测试便捷函数:")
    print(f"   sharpe_ratio: {sharpe_ratio(returns):.4f}")
    print(f"   sortino_ratio: {sortino_ratio(returns):.4f}")
    print(f"   max_drawdown: {max_drawdown(returns):.4f}")
    print(f"   calmar_ratio: {calmar_ratio(returns):.4f}")
    
    print("\n3. 测试滚动夏普:")
    rolling_sharpe = analyzer.calculate_rolling_sharpe(returns, window=252)
    print(f"   滚动夏普长度: {len(rolling_sharpe)}")
    print(f"   滚动夏普均值: {rolling_sharpe.mean():.4f}")
    
    print("\n" + "=" * 60)
    print("✅ 风险指标模块测试完成!")
    print("=" * 60)
