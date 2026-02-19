"""
IC分析器 - 生成信息系数相关图表
Information Coefficient Analyzer

功能:
1. IC时间序列图
2. IC分布图
3. 滚动IC统计图
4. IC衰减分析
"""

import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from typing import Dict, List, Optional, Tuple
from datetime import datetime


class ICAnalyzer:
    """
    IC分析器
    
    用于计算和可视化因子的信息系数(IC)
    """
    
    def __init__(self, factor_name: str = None):
        """
        初始化
        
        Args:
            factor_name: 因子名称
        """
        self.factor_name = factor_name
        self.ic_results: Dict[str, pd.DataFrame] = {}
    
    def compute_ic(
        self,
        factor_df: pd.DataFrame,
        price_df: pd.DataFrame,
        split_date: datetime = None,
        method: str = 'spearman'
    ) -> Dict:
        """
        计算IC
        
        Args:
            factor_df: 因子数据 (time, symbol, value)
            price_df: 价格数据 (time, symbol, close)
            split_date: 训练/测试集分界日期
            method: 相关性方法 (pearson/spearman)
            
        Returns:
            IC结果字典
        """
        # 合并数据
        merged = pd.merge(factor_df, price_df, on=['time', 'symbol'], how='inner')
        
        if len(merged) < 100:
            return {'error': '数据量不足'}
        
        # 计算未来收益率
        merged = merged.sort_values(['symbol', 'time'])
        merged['future_return'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
        merged = merged.dropna(subset=['value', 'future_return'])
        merged = merged[merged['future_return'].abs() < 0.11]  # 去除涨跌停
        
        if len(merged) < 100:
            return {'error': '合并后数据不足'}
        
        # 划分训练/测试集
        if split_date:
            merged['period'] = merged['time'].apply(
                lambda x: 'train' if x <= split_date else 'test'
            )
        
        result = {}
        
        # 计算各周期IC
        periods = ['train', 'test'] if split_date else ['all']
        for period in periods:
            if period == 'all':
                period_data = merged
            else:
                period_data = merged[merged['period'] == period]
            
            if len(period_data) > 100:
                ic = period_data['value'].corr(period_data['future_return'], method=method)
                result[f'ic_{period}'] = ic
                result[f'samples_{period}'] = len(period_data)
        
        # 整体IC
        result['ic_all'] = merged['value'].corr(merged['future_return'], method=method)
        result['samples_all'] = len(merged)
        
        # 计算滚动IC
        window = 60
        daily_ic = merged.groupby('time').apply(
            lambda x: x['value'].corr(x['future_return'], method=method)
            if x['future_return'].std() > 0 else 0
        ).reset_index()
        daily_ic.columns = ['date', 'IC']
        
        if split_date:
            daily_ic['period'] = daily_ic['date'].apply(
                lambda x: 'train' if x <= split_date else 'test'
            )
        
        result['rolling_ic'] = daily_ic
        
        return result
    
    def plot_ic_timeseries(
        self,
        rolling_ic_df: pd.DataFrame,
        split_date: datetime = None,
        title: str = None,
        show_legend: bool = True
    ) -> go.Figure:
        """
        绘制IC时间序列图
        
        Args:
            rolling_ic_df: 滚动IC数据 (date, IC, period)
            split_date: 分界日期
            title: 标题
            show_legend: 是否显示图例
            
        Returns:
            Plotly Figure
        """
        if title is None:
            title = f"{self.factor_name} IC时间序列" if self.factor_name else "IC时间序列"
        
        # 创建颜色映射
        color_map = {'train': 'green', 'test': 'red', 'all': 'blue'}
        
        fig = px.line(
            rolling_ic_df, 
            x='date', 
            y='IC',
            color='period' if 'period' in rolling_ic_df.columns else None,
            title=title,
            color_discrete_map=color_map if 'period' in rolling_ic_df.columns else None
        )
        
        # 添加参考线
        fig.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.5)
        fig.add_hline(y=0.02, line_dash="dot", line_color="blue", opacity=0.5)
        fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", opacity=0.5)
        
        # 添加分界线
        if split_date:
            fig.add_vline(
                x=split_date,
                line_dash="dash",
                line_color="gray",
                annotation_text="Train/Test Split"
            )
        
        fig.update_layout(
            template='plotly_white',
            showlegend=show_legend,
            height=400,
            xaxis_title='日期',
            yaxis_title='IC'
        )
        
        return fig
    
    def plot_ic_distribution(
        self,
        rolling_ic_df: pd.DataFrame,
        title: str = None,
        show_kde: bool = True
    ) -> go.Figure:
        """
        绘制IC分布图
        
        Args:
            rolling_ic_df: 滚动IC数据
            title: 标题
            show_kde: 是否显示KDE
            
        Returns:
            Plotly Figure
        """
        if title is None:
            title = f"{self.factor_name} IC分布" if self.factor_name else "IC分布"
        
        # 子图
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=['IC分布直方图', 'IC箱线图'],
            specs=[[{"type": "histogram"}, {"type": "box"}]]
        )
        
        # 直方图
        if 'period' in rolling_ic_df.columns:
            for period in rolling_ic_df['period'].unique():
                data = rolling_ic_df[rolling_ic_df['period'] == period]['IC']
                fig.add_trace(
                    go.Histogram(
                        x=data,
                        name=period,
                        opacity=0.7,
                        histnorm='probability density'
                    ),
                    row=1, col=1
                )
        else:
            fig.add_trace(
                go.Histogram(
                    x=rolling_ic_df['IC'],
                    opacity=0.7,
                    histnorm='probability density'
                ),
                row=1, col=1
            )
        
        # 箱线图
        if 'period' in rolling_ic_df.columns:
            for i, period in enumerate(rolling_ic_df['period'].unique()):
                data = rolling_ic_df[rolling_ic_df['period'] == period]['IC']
                fig.add_trace(
                    go.Box(
                        y=data,
                        name=period,
                        boxpoints='outliers'
                    ),
                    row=1, col=2
                )
        else:
            fig.add_trace(
                go.Box(
                    y=rolling_ic_df['IC'],
                    boxpoints='outliers'
                ),
                row=1, col=2
            )
        
        # 添加参考线
        fig.add_hline(y=0, line_dash="dot", line_color="black", row=1, col=1)
        fig.add_hline(y=0.02, line_dash="dot", line_color="blue", row=1, col=1)
        
        fig.update_layout(
            title=title,
            template='plotly_white',
            height=400,
            showlegend=False
        )
        
        return fig
    
    def plot_rolling_ic_comparison(
        self,
        daily_ic: pd.Series,
        windows: List[int] = [20, 60, 120],
        title: str = None
    ) -> go.Figure:
        """
        绘制多窗口滚动IC对比图
        
        Args:
            daily_ic: 每日IC Series
            windows: 窗口大小列表
            title: 标题
            
        Returns:
            Plotly Figure
        """
        if title is None:
            title = f"{self.factor_name} 滚动IC对比" if self.factor_name else "滚动IC对比"
        
        # 计算不同窗口的滚动IC
        df = pd.DataFrame({'IC': daily_ic})
        for w in windows:
            df[f'IC_{w}d'] = df['IC'].rolling(window=w, min_periods=10).mean()
        
        # 绘制
        fig = px.line(
            df,
            title=title,
            labels={'value': 'IC', 'index': '日期'}
        )
        
        # 添加参考线
        fig.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.5)
        fig.add_hline(y=0.02, line_dash="dot", line_color="blue", opacity=0.5)
        fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", opacity=0.5)
        
        fig.update_layout(
            template='plotly_white',
            height=400,
            xaxis_title='日期',
            yaxis_title='IC'
        )
        
        return fig
    
    def compute_ic_statistics(self, rolling_ic_df: pd.DataFrame) -> pd.DataFrame:
        """
        计算IC统计指标
        
        Args:
            rolling_ic_df: 滚动IC数据
            
        Returns:
            统计指标DataFrame
        """
        if 'period' in rolling_ic_df.columns:
            stats = rolling_ic_df.groupby('period')['IC'].agg([
                'count', 'mean', 'std', 'min', 'max', 'median'
            ])
            
            # 计算胜率
            win_rate = rolling_ic_df.groupby('period').apply(
                lambda x: (x['IC'] > 0).mean()
            )
            ic_rate = rolling_ic_df.groupby('period').apply(
                lambda x: (x['IC'].abs() > 0.02).mean()
            )
            
            stats['win_rate'] = win_rate
            stats['ic_rate'] = ic_rate
        else:
            stats = pd.DataFrame({
                'IC': rolling_ic_df['IC'].agg(['count', 'mean', 'std', 'min', 'max', 'median'])
            }).T
            stats['win_rate'] = (rolling_ic_df['IC'] > 0).mean()
            stats['ic_rate'] = (rolling_ic_df['IC'].abs() > 0.02).mean()
        
        return stats
    
    def generate_ic_report(
        self,
        factor_df: pd.DataFrame,
        price_df: pd.DataFrame,
        split_date: datetime = None,
        output_dir: str = None
    ) -> Dict:
        """
        生成完整的IC分析报告
        
        Args:
            factor_df: 因子数据
            price_df: 价格数据
            split_date: 分界日期
            output_dir: 输出目录
            
        Returns:
            报告字典
        """
        # 计算IC
        result = self.compute_ic(factor_df, price_df, split_date)
        
        if 'error' in result:
            return result
        
        # 生成图表
        report = {
            'factor_name': self.factor_name,
            'ic_all': result['ic_all'],
            'samples_all': result['samples_all'],
            'ic_stats': None,
            'charts': {}
        }
        
        if split_date:
            report['ic_train'] = result.get('ic_train')
            report['ic_test'] = result.get('ic_test')
            report['samples_train'] = result.get('samples_train')
            report['samples_test'] = result.get('samples_test')
        
        # IC时间序列图
        report['charts']['ic_timeseries'] = self.plot_ic_timeseries(
            result['rolling_ic'], split_date
        )
        
        # IC分布图
        report['charts']['ic_distribution'] = self.plot_ic_distribution(
            result['rolling_ic']
        )
        
        # 滚动IC对比图
        report['charts']['rolling_ic'] = self.plot_rolling_ic_comparison(
            result['rolling_ic'].set_index('date')['IC']
        )
        
        # 统计指标
        report['ic_stats'] = self.compute_ic_statistics(result['rolling_ic'])
        
        return report


# ==================== 便捷函数 ====================

def create_ic_analyzer(factor_name: str = None) -> ICAnalyzer:
    """创建IC分析器"""
    return ICAnalyzer(factor_name)


# ==================== 导出 ====================

__all__ = [
    'ICAnalyzer',
    'create_ic_analyzer',
]
