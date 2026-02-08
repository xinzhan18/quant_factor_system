"""
因子评估器
Factor Evaluator
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from .base import Factor, FactorSystem


class FactorEvaluator:
    """
    因子评估器
    提供多种因子评估方法
    """
    
    def __init__(self, factor_system: FactorSystem):
        """
        初始化评估器
        
        Args:
            factor_system: 因子系统实例
        """
        self.factor_system = factor_system
        self.evaluation_results: Dict[str, Any] = {}
        
    def evaluate_ic(self, returns: pd.Series) -> Dict[str, Dict[str, float]]:
        """
        评估所有因子的信息系数 (IC)
        
        Args:
            returns: 收益率序列
            
        Returns:
            各因子的IC统计信息
        """
        ic_results = {}
        
        for name, factor in self.factor_system.factors.items():
            if factor.values is not None:
                ic_analysis = factor.ic_analysis(returns)
                ic_results[name] = ic_analysis
                
        self.evaluation_results['ic'] = ic_results
        return ic_results
    
    def evaluate_ic_decay(self, returns: pd.Series, lags: List[int] = None) -> Dict[str, pd.DataFrame]:
        """
        评估IC衰减特性
        
        Args:
            returns: 收益率序列
            lags: 滞后期列表
            
        Returns:
            IC衰减数据
        """
        if lags is None:
            lags = [1, 2, 3, 4, 5, 10, 20]
            
        ic_decay = {}
        
        for name, factor in self.factor_system.factors.items():
            if factor.values is None:
                continue
                
            decay_data = {}
            for lag in lags:
                # 计算滞后收益率的相关性
                lagged_returns = returns.shift(-lag)
                common_index = factor.values.index.intersection(lagged_returns.index)
                
                if len(common_index) > 10:
                    ic = factor.values.loc[common_index].corr(lagged_returns.loc[common_index])
                    decay_data[f'lag_{lag}'] = ic
                    
            ic_decay[name] = pd.Series(decay_data)
            
        return ic_decay
    
    def evaluate_group_return(self, returns: pd.Series, groups: int = 5) -> pd.DataFrame:
        """
        评估分组收益
        
        Args:
            returns: 收益率序列
            groups: 分组数量
            
        Returns:
            分组收益表
        """
        if self.factor_system.factor_values.empty:
            raise ValueError("请先计算因子值")
            
        group_returns = {}
        
        for name in self.factor_system.factors.keys():
            factor = self.factor_system.factor_values[name]
            
            # 按因子值分组
            try:
                quantile_labels = [f'Q{i+1}' for i in range(groups)]
                factor_groups = pd.qcut(factor, q=groups, labels=quantile_labels)
                
                # 计算每组收益
                group_ret = {}
                for i, label in enumerate(quantile_labels):
                    mask = factor_groups == label
                    if mask.sum() > 0:
                        group_ret[label] = returns[mask].mean()
                        
                group_returns[name] = pd.Series(group_ret)
                
            except Exception as e:
                print(f"分组计算出错 ({name}): {e}")
                continue
                
        return pd.DataFrame(group_returns)
    
    def evaluate_turnover(self, period: int = 20) -> Dict[str, float]:
        """
        评估因子换手率
        
        Args:
            period: 计算期
            
        Returns:
            各因子换手率
        """
        if self.factor_system.factor_values.empty:
            raise ValueError("请先计算因子值")
            
        turnover = {}
        
        for name in self.factor_system.factors.keys():
            factor_values = self.factor_system.factor_values[name].dropna()
            
            if len(factor_values) < period + 1:
                continue
                
            # 计算排名变化
            rank = factor_values.rank()
            rank_changes = rank.diff().abs()
            
            # 换手率 = 排名变化的比例
            turnover[name] = rank_changes.mean()
            
        return turnover
    
    def evaluate_sharpe_by_group(self, returns: pd.Series, groups: int = 5) -> pd.DataFrame:
        """
        评估分组夏普比率
        
        Args:
            returns: 收益率序列
            groups: 分组数量
            
        Returns:
            分组夏普比率表
        """
        group_returns = self.evaluate_group_return(returns, groups)
        
        sharpe_ratios = {}
        
        for name in group_returns.columns:
            rets = group_returns[name]
            mean_ret = rets.mean()
            std_ret = rets.std()
            
            if std_ret > 0:
                sharpe = mean_ret / std_ret * np.sqrt(252)  # 年化夏普
            else:
                sharpe = 0
                
            sharpe_ratios[name] = {
                'sharpe': sharpe,
                'mean_return': mean_ret,
                'std_return': std_ret,
                'spread': rets.max() - rets.min()  # 多空收益差
            }
            
        return pd.DataFrame(sharpe_ratios).T
    
    def get_factor_report(self, returns: pd.Series) -> Dict[str, Any]:
        """
        生成完整因子评估报告
        
        Args:
            returns: 收益率序列
            
        Returns:
            完整评估报告
        """
        report = {
            'factor_summary': self.factor_system.summary(),
            'ic_analysis': self.evaluate_ic(returns),
            'ic_decay': self.evaluate_ic_decay(returns),
            'group_returns': self.evaluate_group_return(returns).to_dict(),
            'turnover': self.evaluate_turnover(),
            'sharpe_by_group': self.evaluate_sharpe_by_group(returns).to_dict()
        }
        
        self.evaluation_results = report
        return report
    
    def print_report(self, returns: pd.Series) -> None:
        """
        打印因子评估报告
        """
        report = self.get_factor_report(returns)
        
        print("\n" + "="*60)
        print("📊 多因子评估报告")
        print("="*60)
        
        print("\n📌 因子概况:")
        summary = report['factor_summary']
        print(f"  系统名称: {summary['name']}")
        print(f"  因子数量: {summary['num_factors']}")
        print(f"  因子列表: {', '.join(summary['factor_names'])}")
        
        print("\n📈 IC分析:")
        for name, ic_info in report['ic_analysis'].items():
            print(f"  {name}: IC={ic_info['ic']:.4f}, IC_IR={ic_info['ic_ir']:.4f}, IC胜率={ic_info['ic_sign_ratio']:.2%}")
        
        print("\n📉 IC衰减:")
        for name, decay in report['ic_decay'].items():
            print(f"  {name}: {decay.to_dict()}")
            
        print("\n🔄 换手率:")
        for name, turnover in report['turnover'].items():
            print(f"  {name}: {turnover:.4f}")
            
        print("\n💰 分组夏普比率:")
        sharpe_df = pd.DataFrame(report['sharpe_by_group']).T
        print(sharpe_df.to_string())
        
        print("\n" + "="*60)


class BacktestEngine:
    """
    回测引擎
    简单的因子回测框架
    """
    
    def __init__(self, factor_system: FactorSystem, 
                 rebalance_period: int = 20,
                 top_n: int = 10):
        """
        初始化回测引擎
        
        Args:
            factor_system: 因子系统
            rebalance_period: 调仓周期（天）
            top_n: 选股数量
        """
        self.factor_system = factor_system
        self.rebalance_period = rebalance_period
        self.top_n = top_n
        self.portfolio_returns: pd.Series = pd.Series()
        
    def run_backtest(self, data: pd.DataFrame, returns: pd.Series) -> pd.Series:
        """
        运行回测
        
        Args:
            data: 价格数据
            returns: 收益率数据
            
        Returns:
            组合收益序列
        """
        # 计算所有因子
        factor_values = self.factor_system.calculate_all(data)
        
        # 获取综合得分
        scores = self.factor_system.get_composite_score()
        
        # 调仓日
        rebalance_dates = scores.index[::self.rebalance_period]
        
        portfolio_ret = []
        
        for date in rebalance_dates[:-1]:
            if date not in scores.index:
                continue
                
            # 获取当日因子得分
            date_scores = scores.loc[date]
            
            # 选取得分最高的股票
            if isinstance(date_scores, pd.Series):
                top_stocks = date_scores.nlargest(self.top_n).index.tolist()
            else:
                top_stocks = []
            
            # 计算下期收益
            next_date_idx = list(scores.index).index(date) + 1
            if next_date_idx < len(scores.index):
                next_date = scores.index[next_date_idx]
                if next_date in returns.index:
                    period_return = returns.loc[next_date]
                    
                    # 如果是Series（多股票），取平均
                    if isinstance(period_return, pd.Series):
                        if len(top_stocks) > 0:
                            # 简化处理：取所有股票平均
                            port_ret = period_return.mean()
                        else:
                            port_ret = 0
                    else:
                        port_ret = period_return
                        
                    portfolio_ret.append((next_date, port_ret))
        
        # 转换为Series
        dates = [d[0] for d in portfolio_ret]
        rets = [d[1] for d in portfolio_ret]
        self.portfolio_returns = pd.Series(rets, index=dates)
        
        return self.portfolio_returns
    
    def get_performance(self) -> Dict[str, float]:
        """
        获取回测绩效指标
        """
        if self.portfolio_returns.empty:
            return {}
            
        cumulative = (1 + self.portfolio_returns).cumprod()
        total_return = cumulative.iloc[-1] - 1 if len(cumulative) > 0 else 0
        annual_return = self.portfolio_returns.mean() * 252
        annual_vol = self.portfolio_returns.std() * np.sqrt(252)
        sharpe = annual_return / annual_vol if annual_vol > 0 else 0
        max_drawdown = (cumulative / cumulative.cummax() - 1).min()
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'annual_volatility': annual_vol,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown
        }
