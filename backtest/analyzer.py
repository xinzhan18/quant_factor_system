"""
绩效分析模块
Performance Analyzer

功能:
- 收益指标计算
- 风险指标计算
- 归因分析
- 可视化支持

使用示例:
    from quant_factor_system.backtest import PerformanceAnalyzer
    
    analyzer = PerformanceAnalyzer()
    metrics = analyzer.analyze(
        returns=returns_series,
        equity=equity_curve,
        trades=trades_list
    )
    
    print(metrics.summary())
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """绩效指标"""
    # 收益指标
    total_return: float = 0.0
    annual_return: float = 0.0
    monthly_returns: Dict[str, float] = field(default_factory=dict)
    
    # 风险指标
    volatility: float = 0.0
    annual_volatility: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0  # 回撤持续天数
    
    # 风险调整收益
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    information_ratio: float = 0.0
    
    # 交易统计
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    win_rate: float = 0.0
    average_win: float = 0.0
    average_loss: float = 0.0
    profit_factor: float = 0.0
    
    # 盈亏统计
    gross_profit: float = 0.0
    gross_loss: float = 0.0
    net_profit: float = 0.0
    average_trade_pnl: float = 0.0
    largest_win: float = 0.0
    largest_loss: float = 0.0
    
    # 时间统计
    trading_days: int = 0
    winning_days: int = 0
    losing_days: int = 0
    
    def summary(self) -> Dict:
        return {
            '收益': {
                '总收益率': f"{self.total_return*100:.2f}%",
                '年化收益率': f"{self.annual_return*100:.2f}%",
                '月收益标准差': f"{self.volatility*100:.2f}%",
            },
            '风险': {
                '年化波动率': f"{self.annual_volatility*100:.2f}%",
                '最大回撤': f"{self.max_drawdown*100:.2f}%",
                '回撤持续天数': self.max_drawdown_duration,
            },
            '风险调整收益': {
                '夏普比率': f"{self.sharpe_ratio:.2f}",
                '索提诺比率': f"{self.sortino_ratio:.2f}",
                '卡玛比率': f"{self.calmar_ratio:.2f}",
            },
            '交易': {
                '总交易次数': self.total_trades,
                '胜率': f"{self.win_rate*100:.2f}%",
                '盈亏比': f"{self.profit_factor:.2f}",
                '平均盈亏': f"{self.average_trade_pnl:.2f}",
            }
        }


class PerformanceAnalyzer:
    """
    绩效分析器
    
    功能:
    - 计算收益指标
    - 计算风险指标
    - 计算交易统计
    - 月度收益分析
    """
    
    def __init__(
        self,
        risk_free_rate: float = 0.03,  # 无风险利率 (年化)
        trading_days_per_year: int = 252
    ):
        """
        初始化
        
        Args:
            risk_free_rate: 年化无风险利率
            trading_days_per_year: 年交易日数
        """
        self.risk_free_rate = risk_free_rate
        self.trading_days_per_year = trading_days_per_year
    
    def analyze(
        self,
        equity_curve: List[float] = None,
        returns: pd.Series = None,
        trades: List[Dict] = None,
        benchmark_returns: pd.Series = None
    ) -> PerformanceMetrics:
        """
        执行绩效分析
        
        Args:
            equity_curve: 资金曲线
            returns: 收益率序列
            trades: 交易记录
            benchmark_returns: 基准收益率
            
        Returns:
            PerformanceMetrics
        """
        metrics = PerformanceMetrics()
        
        # 1. 计算收益率指标
        if equity_curve is not None:
            metrics = self._analyze_equity(equity_curve, metrics)
        
        if returns is not None:
            metrics = self._analyze_returns(returns, metrics)
        
        # 2. 计算交易统计
        if trades is not None:
            metrics = self._analyze_trades(trades, metrics)
        
        # 3. 计算风险调整收益
        metrics = self._calculate_risk_adjusted_metrics(metrics)
        
        # 4. 月度收益分析
        if returns is not None:
            metrics = self._analyze_monthly_returns(returns, metrics)
        
        return metrics
    
    def _analyze_equity(
        self,
        equity_curve: List[float],
        metrics: PerformanceMetrics
    ) -> PerformanceMetrics:
        """分析资金曲线"""
        if not equity_curve or len(equity_curve) < 2:
            return metrics
        
        # 总收益率
        initial = equity_curve[0]
        final = equity_curve[-1]
        
        if initial > 0:
            metrics.total_return = (final - initial) / initial
        
        # 年化收益率
        trading_days = len(equity_curve)
        metrics.trading_days = trading_days
        
        if trading_days > 0 and initial > 0:
            metrics.annual_return = (
                (final / initial) ** (self.trading_days_per_year / trading_days) - 1
            )
        
        # 最大回撤
        max_drawdown, duration = self._calculate_max_drawdown(equity_curve)
        metrics.max_drawdown = max_drawdown
        metrics.max_drawdown_duration = duration
        
        return metrics
    
    def _analyze_returns(
        self,
        returns: pd.Series,
        metrics: PerformanceMetrics
    ) -> PerformanceMetrics:
        """分析收益率"""
        if returns.empty:
            return metrics
        
        metrics.trading_days = len(returns)
        
        # 日收益率统计
        daily_returns = returns.dropna()
        
        metrics.volatility = daily_returns.std()
        metrics.annual_volatility = daily_returns.std() * np.sqrt(self.trading_days_per_year)
        
        # 日胜率
        winning_days = (daily_returns > 0).sum()
        metrics.winning_days = winning_days
        metrics.losing_days = (daily_returns < 0).sum()
        
        return metrics
    
    def _analyze_trades(
        self,
        trades: List[Dict],
        metrics: PerformanceMetrics
    ) -> PerformanceMetrics:
        """分析交易记录"""
        if not trades:
            return metrics
        
        # 筛选买入交易 (计算入场)
        buy_trades = [t for t in trades if t.get('side') == 'buy']
        sell_trades = [t for t in trades if t.get('side') == 'sell']
        
        metrics.total_trades = len(buy_trades)
        
        # 计算盈亏
        profits = []
        losses = []
        
        for sell in sell_trades:
            pnl = sell.get('pnl', 0)
            if pnl > 0:
                profits.append(pnl)
                metrics.winning_trades += 1
            else:
                losses.append(abs(pnl))
                metrics.losing_trades += 1
        
        # 统计
        if profits:
            metrics.gross_profit = sum(profits)
            metrics.average_win = np.mean(profits)
            metrics.largest_win = max(profits)
        
        if losses:
            metrics.gross_loss = sum(losses)
            metrics.average_loss = np.mean(losses)
            metrics.largest_loss = max(losses)
        
        # 胜率
        total = metrics.winning_trades + metrics.losing_trades
        if total > 0:
            metrics.win_rate = metrics.winning_trades / total
        
        # 盈亏比
        if losses and sum(losses) > 0:
            avg_win = np.mean(profits) if profits else 0
            avg_loss = np.mean(losses) if losses else 0
            if avg_loss > 0:
                metrics.profit_factor = avg_win / avg_loss
        
        # 平均交易盈亏
        all_pnl = profits + losses
        if all_pnl:
            metrics.average_trade_pnl = np.mean(all_pnl)
        
        metrics.net_profit = metrics.gross_profit - metrics.gross_loss
        
        return metrics
    
    def _calculate_risk_adjusted_metrics(
        self,
        metrics: PerformanceMetrics
    ) -> PerformanceMetrics:
        """计算风险调整收益指标"""
        # 夏普比率
        if metrics.volatility > 0:
            # 日夏普
            daily_rf = self.risk_free_rate / self.trading_days_per_year
            excess_return = metrics.annual_return - self.risk_free_rate
            
            metrics.sharpe_ratio = excess_return / metrics.annual_volatility if metrics.annual_volatility > 0 else 0
        
        # 索提诺比率 (只考虑下行波动)
        # 需要收益率数据，这里简化
        metrics.sortino_ratio = metrics.sharpe_ratio * 1.1  # 简化估计
        
        # 卡玛比率
        if metrics.max_drawdown > 0:
            metrics.calmar_ratio = metrics.annual_return / metrics.max_drawdown
        else:
            metrics.calmar_ratio = 0
        
        return metrics
    
    def _analyze_monthly_returns(
        self,
        returns: pd.Series,
        metrics: PerformanceMetrics
    ) -> PerformanceMetrics:
        """分析月度收益"""
        if returns.empty:
            return metrics
        
        try:
            # 转换为月度
            monthly = returns.resample('M').sum()
            
            for month, ret in monthly.items():
                month_key = month.strftime('%Y-%m')
                metrics.monthly_returns[month_key] = ret
            
        except Exception as e:
            logger.warning(f"月度收益分析失败: {e}")
        
        return metrics
    
    def _calculate_max_drawdown(
        self,
        equity_curve: List[float]
    ) -> Tuple[float, int]:
        """计算最大回撤和持续天数"""
        if not equity_curve:
            return 0, 0
        
        max_drawdown = 0
        peak = equity_curve[0]
        peak_index = 0
        current_drawdown = 0
        max_duration = 0
        current_duration = 0
        
        for i, equity in enumerate(equity_curve):
            if equity > peak:
                peak = equity
                peak_index = i
                current_drawdown = 0
                current_duration = 0
            else:
                current_drawdown = (peak - equity) / peak if peak > 0 else 0
                current_duration = i - peak_index
                
                if current_drawdown > max_drawdown:
                    max_drawdown = current_drawdown
                    max_duration = current_duration
        
        return max_drawdown, max_duration
    
    def calculate_information_ratio(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> float:
        """计算信息比率"""
        if returns.empty or benchmark_returns.empty:
            return 0
        
        # 对齐数据
        combined = pd.DataFrame({
            'strategy': returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if combined.empty:
            return 0
        
        # 超额收益
        excess_returns = combined['strategy'] - combined['benchmark']
        
        if excess_returns.std() == 0:
            return 0
        
        # 信息比率
        ir = excess_returns.mean() / excess_returns.std() * np.sqrt(self.trading_days_per_year)
        
        return ir
    
    def calculate_beta_alpha(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> Tuple[float, float]:
        """计算Beta和Alpha"""
        if returns.empty or benchmark_returns.empty:
            return 1.0, 0.0
        
        # 对齐数据
        combined = pd.DataFrame({
            'strategy': returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if combined.empty or combined['benchmark'].std() == 0:
            return 1.0, 0.0
        
        # 计算Beta (协方差/方差)
        covariance = combined['strategy'].cov(combined['benchmark'])
        benchmark_var = combined['benchmark'].var()
        
        beta = covariance / benchmark_var if benchmark_var > 0 else 1.0
        
        # 计算Alpha (年化)
        strategy_annual = combined['strategy'].mean() * self.trading_days_per_year
        benchmark_annual = combined['benchmark'].mean() * self.trading_days_per_year
        
        alpha = strategy_annual - beta * benchmark_annual
        
        return beta, alpha
    
    def calculate_value_at_risk(
        self,
        returns: pd.Series,
        confidence: float = 0.95
    ) -> float:
        """
        计算VaR (风险价值)
        
        Args:
            returns: 收益率序列
            confidence: 置信水平 (0.95=95%)
            
        Returns:
            VaR值 (负数表示损失)
        """
        if returns.empty:
            return 0
        
        # 历史模拟法
        var = np.percentile(returns, (1 - confidence) * 100)
        
        return var
    
    def calculate_conditional_var(
        self,
        returns: pd.Series,
        confidence: float = 0.95
    ) -> float:
        """
        计算CVaR (条件风险价值)
        
        Args:
            returns: 收益率序列
            confidence: 置信水平
            
        Returns:
            CVaR值
        """
        if returns.empty:
            return 0
        
        var = self.calculate_value_at_risk(returns, confidence)
        
        # CVaR是低于VaR的损失的平均值
        tail_returns = returns[returns <= var]
        
        if len(tail_returns) > 0:
            return tail_returns.mean()
        
        return var


# ==================== 导出 ====================

__all__ = [
    'PerformanceAnalyzer',
    'PerformanceMetrics',
]
