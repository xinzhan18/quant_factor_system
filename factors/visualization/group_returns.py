"""
分组收益分析器 - 生成因子分组收益相关图表
Group Returns Analyzer

功能:
1. 分组收益柱状图
2. 累计收益曲线
3. 多空组合分析
4. 分组统计表
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class GroupReturnsAnalyzer:
    """
    分组收益分析器
    
    用于分析因子分组后的收益表现
    """
    
    def __init__(self, factor_name: str = None):
        """
        初始化
        
        Args:
            factor_name: 因子名称
        """
        self.factor_name = factor_name
        self.results: Dict = {}
    
    def compute_group_returns(
        self,
        factor_df: pd.DataFrame,
        price_df: pd.DataFrame,
        n_groups: int = 5,
        split_date: datetime = None
    ) -> Dict:
        """
        计算分组收益
        
        Args:
            factor_df: 因子数据 (time, symbol, value)
            price_df: 价格数据 (time, symbol, close)
            n_groups: 分组数量
            split_date: 分界日期
            
        Returns:
            分组收益结果
        """
        # 合并数据
        merged = pd.merge(factor_df, price_df, on=['time', 'symbol'], how='inner')
        
        if len(merged) < 100:
            return {'error': '数据量不足'}
        
        # 计算未来收益率
        merged = merged.sort_values(['symbol', 'time'])
        merged['future_return'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
        merged = merged.dropna(subset=['value', 'future_return'])
        merged = merged[merged['future_return'].abs() < 0.11]
        
        if len(merged) < 100:
            return {'error': '合并后数据不足'}
        
        # 划分训练/测试集
        if split_date:
            merged['period'] = merged['time'].apply(
                lambda x: 'train' if x <= split_date else 'test'
            )
        
        # 分组
        labels = [f'Q{i+1}' for i in range(n_groups)]
        merged['group'] = pd.qcut(merged['value'], q=n_groups, labels=labels)
        
        # 计算分组收益
        group_returns = merged.groupby(['time', 'group'])['future_return'].mean().reset_index()
        group_returns_pivot = group_returns.pivot(
            index='time', 
            columns='group', 
            values='future_return'
        )
        
        # 累计收益
        cumulative_returns = (1 + group_returns_pivot).cumprod() - 1
        
        # 统计指标
        mean_returns = group_returns_pivot.mean() * 252  # 年化收益
        std_returns = group_returns_pivot.std() * np.sqrt(252)  # 年化波动
        sharpe = mean_returns / std_returns
        
        result = {
            'group_returns_pivot': group_returns_pivot,
            'cumulative_returns': cumulative_returns,
            'mean_returns': mean_returns,
            'std_returns': std_returns,
            'sharpe': sharpe,
            'n_groups': n_groups,
            'samples': len(merged)
        }
        
        # 分周期统计
        if split_date:
            for period in ['train', 'test']:
                period_data = merged[merged['period'] == period]
                if len(period_data) > 100:
                    period_gr = period_data.groupby(['time', 'group'])['future_return'].mean()
                    period_pivot = period_gr.unstack(level='group')
                    result[f'mean_returns_{period}'] = period_pivot.mean() * 252
                    result[f'cumulative_returns_{period}'] = (1 + period_pivot).cumprod() - 1
        
        return result
    
    def plot_group_returns_bar(
        self,
        mean_returns: pd.Series,
        title: str = None,
        show_values: bool = True
    ) -> go.Figure:
        """
        绘制分组年化收益柱状图
        
        Args:
            mean_returns: 年化收益Series
            title: 标题
            show_values: 是否显示数值
            
        Returns:
            Plotly Figure
        """
        if title is None:
            title = f"{self.factor_name} 分组年化收益" if self.factor_name else "分组年化收益"
        
        # 颜色映射
        colors = px.colors.diverging.RdBu_r
        color_values = mean_returns.values * 100
        
        fig = px.bar(
            x=mean_returns.index,
            y=mean_returns.values * 100,
            title=title,
            labels={'x': '分组', 'y': '年化收益率 (%)'},
            color=color_values,
            color_continuous_scale='RdYlGn'
        )
        
        # 添加零线
        fig.add_hline(y=0, line_dash="dot", line_color="black")
        
        # 添加数值标签
        if show_values:
            for i, (idx, val) in enumerate(mean_returns.items()):
                fig.add_annotation(
                    x=idx,
                    y=val * 100,
                    text=f"{val*100:.2f}%",
                    showarrow=False,
                    yshift=10
                )
        
        fig.update_layout(
            template='plotly_white',
            height=400,
            coloraxis_colorbar=dict(title="收益率 (%)")
        )
        
        return fig
    
    def plot_cumulative_returns(
        self,
        cumulative_returns: pd.DataFrame,
        title: str = None,
        show_groups: bool = True,
        highlight_q: str = None
    ) -> go.Figure:
        """
        绘制累计收益曲线
        
        Args:
            cumulative_returns: 累计收益DataFrame
            title: 标题
            show_groups: 是否显示所有分组
            highlight_q: 高亮的分组 (如 'Q5' 或 'Q1')
            
        Returns:
            Plotly Figure
        """
        if title is None:
            title = f"{self.factor_name} 累计收益曲线" if self.factor_name else "累计收益曲线"
        
        if show_groups:
            fig = px.line(
                cumulative_returns,
                title=title,
                labels={'value': '累计收益', 'time': '日期', 'group': '分组'}
            )
            
            # 高亮指定分组
            if highlight_q and highlight_q in cumulative_returns.columns:
                fig.add_trace(
                    go.Scatter(
                        x=cumulative_returns.index,
                        y=cumulative_returns[highlight_q],
                        mode='lines',
                        name=f'{highlight_q} (高亮)',
                        line=dict(width=4, color='red')
                    )
                )
        else:
            # 只显示多空组合
            if 'Q5' in cumulative_returns.columns and 'Q1' in cumulative_returns.columns:
                long_short = cumulative_returns['Q5'] - cumulative_returns['Q1']
                fig = px.line(
                    long_short,
                    title=title,
                    labels={'value': '累计收益', 'index': '日期'}
                )
            else:
                fig = px.line(
                    cumulative_returns,
                    title=title
                )
        
        fig.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.5)
        
        fig.update_layout(
            template='plotly_white',
            height=400,
            xaxis_title='日期',
            yaxis_title='累计收益'
        )
        
        return fig
    
    def plot_long_short(
        self,
        cumulative_returns: pd.DataFrame,
        title: str = None
    ) -> go.Figure:
        """
        绘制多空组合收益曲线
        
        Args:
            cumulative_returns: 累计收益DataFrame
            title: 标题
            
        Returns:
            Plotly Figure
        """
        if 'Q5' not in cumulative_returns.columns or 'Q1' not in cumulative_returns.columns:
            raise ValueError("需要Q1和Q5分组数据")
        
        if title is None:
            title = f"{self.factor_name} 多空组合 (Q5-Q1)" if self.factor_name else "多空组合 (Q5-Q1)"
        
        long_short = cumulative_returns['Q5'] - cumulative_returns['Q1']
        
        fig = px.line(
            long_short,
            title=title,
            labels={'value': '累计收益', 'index': '日期'}
        )
        
        # 添加参考线
        fig.add_hline(y=0, line_dash="dot", line_color="black")
        
        # 填充收益区域
        fig.add_trace(
            go.Scatter(
                x=long_short.index,
                y=long_short,
                fill='tozeroy',
                fillcolor='rgba(0, 255, 0, 0.1)' if long_short.iloc[-1] > 0 else 'rgba(255, 0, 0, 0.1)',
                line=dict(color='rgba(0,0,0,0)'),
                showlegend=False
            )
        )
        
        fig.update_layout(
            template='plotly_white',
            height=400,
            xaxis_title='日期',
            yaxis_title='累计收益'
        )
        
        return fig
    
    def plot_returns_decay(
        self,
        factor_df: pd.DataFrame,
        price_df: pd.DataFrame,
        holding_periods: List[int] = None,
        title: str = None
    ) -> go.Figure:
        """
        绘制收益衰减图 - 因子在不同持有期的表现
        
        Args:
            factor_df: 因子数据
            price_df: 价格数据
            holding_periods: 持有期列表
            title: 标题
            
        Returns:
            Plotly Figure
        """
        if holding_periods is None:
            holding_periods = [1, 5, 10, 20, 60]
        
        if title is None:
            title = f"{self.factor_name} 收益衰减分析" if self.factor_name else "收益衰减分析"
        
        # 合并数据
        merged = pd.merge(factor_df, price_df, on=['time', 'symbol'], how='inner')
        merged = merged.sort_values(['symbol', 'time'])
        
        # 计算不同持有期的收益
        decay_results = []
        
        for period in holding_periods:
            # 计算N日收益率
            merged[f'return_{period}d'] = merged.groupby('symbol')['close'].pct_change(period)
            
            # 计算相关性
            valid_data = merged.dropna(subset=['value', f'return_{period}d'])
            if len(valid_data) > 100:
                ic = valid_data['value'].corr(valid_data[f'return_{period}d'])
                decay_results.append({
                    'holding_period': f'{period}d',
                    'period': period,
                    'ic': ic
                })
        
        decay_df = pd.DataFrame(decay_results)
        
        # 绘制
        fig = px.bar(
            decay_df,
            x='holding_period',
            y='ic',
            title=title,
            labels={'holding_period': '持有期', 'ic': 'IC'}
        )
        
        # 添加参考线
        fig.add_hline(y=0, line_dash="dot", line_color="black")
        
        fig.update_layout(
            template='plotly_white',
            height=400
        )
        
        return fig
    
    def compute_group_statistics(
        self,
        mean_returns: pd.Series,
        std_returns: pd.Series,
        sharpe: pd.Series,
        cumulative_returns: pd.DataFrame
    ) -> pd.DataFrame:
        """
        计算分组统计指标
        
        Args:
            mean_returns: 年化收益
            std_returns: 年化波动
            sharpe: 夏普比率
            cumulative_returns: 累计收益
            
        Returns:
            统计表
        """
        stats = pd.DataFrame({
            '分组': mean_returns.index,
            '年化收益(%)': (mean_returns * 100).round(2),
            '年化波动(%)': (std_returns * 100).round(2),
            '夏普比率': sharpe.round(2)
        })
        
        # 添加最大回撤
        max_drawdown = []
        for col in cumulative_returns.columns:
            dd = (cumulative_returns[col] - cumulative_returns[col].cummax()).min()
            max_drawdown.append(dd * 100)
        
        stats['最大回撤(%)'] = [round(dd, 2) for dd in max_drawdown]
        
        return stats
    
    def generate_group_report(
        self,
        factor_df: pd.DataFrame,
        price_df: pd.DataFrame,
        n_groups: int = 5,
        split_date: datetime = None,
        output_dir: str = None
    ) -> Dict:
        """
        生成分组收益完整报告
        
        Args:
            factor_df: 因子数据
            price_df: 价格数据
            n_groups: 分组数量
            split_date: 分界日期
            output_dir: 输出目录
            
        Returns:
            报告字典
        """
        # 计算分组收益
        result = self.compute_group_returns(
            factor_df, price_df, n_groups, split_date
        )
        
        if 'error' in result:
            return result
        
        report = {
            'factor_name': self.factor_name,
            'n_groups': n_groups,
            'samples': result['samples'],
            'charts': {},
            'statistics': None
        }
        
        # 分组收益柱状图
        report['charts']['group_returns_bar'] = self.plot_group_returns_bar(
            result['mean_returns']
        )
        
        # 累计收益曲线
        report['charts']['cumulative_returns'] = self.plot_cumulative_returns(
            result['cumulative_returns']
        )
        
        # 多空组合
        if 'Q5' in result['cumulative_returns'].columns and 'Q1' in result['cumulative_returns'].columns:
            report['charts']['long_short'] = self.plot_long_short(
                result['cumulative_returns']
            )
        
        # 统计表
        report['statistics'] = self.compute_group_statistics(
            result['mean_returns'],
            result['std_returns'],
            result['sharpe'],
            result['cumulative_returns']
        )
        
        return report


# ==================== 便捷函数 ====================

def create_group_analyzer(factor_name: str = None) -> GroupReturnsAnalyzer:
    """创建分组收益分析器"""
    return GroupReturnsAnalyzer(factor_name)


# ==================== 导出 ====================

__all__ = [
    'GroupReturnsAnalyzer',
    'create_group_analyzer',
]
