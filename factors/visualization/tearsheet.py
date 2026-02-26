#!/usr/bin/env python3
"""
因子分析 Tear Sheet - 整合所有图表为一张大图
AlphaLens 风格
"""

import sys
sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace')

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

import psycopg2

OUTPUT_DIR = '/Users/xinzhan/.openclaw/workspace/quant_factor_system/output'
os.makedirs(OUTPUT_DIR, exist_ok=True)


class FactorAnalyzer:
    """
    统一因子分析器
    生成 AlphaLens 风格的 Tear Sheet
    """
    
    def __init__(self, factor_name: str):
        self.factor_name = factor_name
        self.results = {}
    
    def load_factor_data(self) -> pd.DataFrame:
        """从数据库加载因子数据"""
        conn = psycopg2.connect(
            host='localhost', port=5432, database='quant_data',
            user='postgres', password='quant123'
        )
        cursor = conn.cursor()
        
        # 获取因子数据
        cursor.execute(f'''
            SELECT symbol, time, value
            FROM {self.get_table_name()}
            ORDER BY symbol, time
        ''')
        
        data = cursor.fetchall()
        df = pd.DataFrame(data, columns=['symbol', 'time', 'factor'])
        df['time'] = pd.to_datetime(df['time'])
        
        # 获取价格数据
        cursor.execute('''
            SELECT symbol, time, close
            FROM price_daily
            WHERE time >= '2015-01-01' AND time <= '2024-12-31'
            ORDER BY symbol, time
        ''')
        
        price_data = cursor.fetchall()
        price_df = pd.DataFrame(price_data, columns=['symbol', 'time', 'close'])
        price_df['time'] = pd.to_datetime(price_df['time'])
        
        conn.close()
        
        return df, price_df
    
    def get_table_name(self) -> str:
        """获取因子表名"""
        table_map = {
            'intraday_momentum': 'factor_intraday_momentum',
        }
        return table_map.get(self.factor_name, f'factor_{self.factor_name}')
    
    def compute_ic(self, factor_df: pd.DataFrame, price_df: pd.DataFrame) -> dict:
        """计算IC"""
        merged = pd.merge(factor_df, price_df, on=['symbol', 'time'], how='inner')
        merged = merged.sort_values(['symbol', 'time'])
        
        # T+1 收益率
        merged['return_1d'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
        merged = merged.dropna(subset=['factor', 'return_1d'])
        merged = merged[merged['return_1d'].abs() < 0.11]
        
        # 整体IC (Spearman)
        ic_all, p_value = stats.spearmanr(merged['factor'], merged['return_1d'])
        
        # 每日IC
        daily_ic = merged.groupby('time').apply(
            lambda x: stats.spearmanr(x['factor'], x['return_1d'])[0]
            if x['return_1d'].std() > 0 else 0
        ).reset_index()
        daily_ic.columns = ['date', 'IC']
        
        # 统计
        ic_mean = daily_ic['IC'].mean()
        ic_std = daily_ic['IC'].std()
        ic_ir = ic_mean / ic_std if ic_std > 0 else 0
        ic_positive_ratio = (daily_ic['IC'] > 0).mean()
        
        return {
            'ic_all': ic_all,
            'ic_mean': ic_mean,
            'ic_std': ic_std,
            'ic_ir': ic_ir,
            'ic_positive_ratio': ic_positive_ratio,
            'samples': len(merged),
            'daily_ic': daily_ic
        }
    
    def compute_group_returns(self, factor_df: pd.DataFrame, price_df: pd.DataFrame) -> dict:
        """计算分组收益"""
        merged = pd.merge(factor_df, price_df, on=['symbol', 'time'], how='inner')
        merged = merged.sort_values(['symbol', 'time'])
        
        # T+1 收益率
        merged['return_1d'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
        merged = merged.dropna(subset=['factor', 'return_1d'])
        merged = merged[merged['return_1d'].abs() < 0.11]
        
        # 分组
        merged['group'] = pd.qcut(merged['factor'], 5, labels=['Q1','Q2','Q3','Q4','Q5'], duplicates='drop')
        
        # 分组收益
        group_returns = merged.groupby(['time', 'group'])['return_1d'].mean().reset_index()
        group_pivot = group_returns.pivot(index='time', columns='group', values='return_1d')
        
        # 累计收益
        cumulative = (1 + group_pivot).cumprod() - 1
        
        # 统计
        mean_returns = group_pivot.mean() * 252
        std_returns = group_pivot.std() * np.sqrt(252)
        sharpe = mean_returns / std_returns
        
        # 多空收益 (Q5累计 - Q1累计)
        long_short = group_pivot['Q5'] - group_pivot['Q1']
        
        return {
            'cumulative': cumulative,
            'mean_returns': mean_returns,
            'std_returns': std_returns,
            'sharpe': sharpe,
            'long_short': long_short,
            'samples': len(merged)
        }
    
    def analyze(self) -> dict:
        """执行完整分析"""
        print(f"📊 加载因子数据: {self.factor_name}")
        factor_df, price_df = self.load_factor_data()
        
        print(f"   因子数据: {len(factor_df):,} 条")
        
        print("📈 计算IC...")
        ic_result = self.compute_ic(factor_df, price_df)
        
        print("📊 计算分组收益...")
        group_result = self.compute_group_returns(factor_df, price_df)
        
        self.results = {
            'factor_name': self.factor_name,
            'ic': ic_result,
            'group': group_result
        }
        
        return self.results
    
    def generate_tear_sheet(self, output_path: str = None) -> go.Figure:
        """生成整合的 Tear Sheet"""
        
        ic = self.results['ic']
        group = self.results['group']
        
        # 创建大图 (3行2列)
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=(
                '分组累计收益曲线 (AlphaLens风格)',
                '分组年化收益',
                'IC时间序列',
                'IC分布',
            ),
            specs=[
                [{"colspan": 2}, None],
                [{}, {}],
                [{"colspan": 2}, None],
            ],
            vertical_spacing=0.08,
            horizontal_spacing=0.1
        )
        
        colors = {'Q1': '#d62728', 'Q2': '#ff7f0e', 'Q3': '#ffbb78', 
                  'Q4': '#98df8a', 'Q5': '#2ca02c'}
        
        # 1. 分组累计收益曲线 (跨两列)
        for q in ['Q1', 'Q2', 'Q3', 'Q4', 'Q5']:
            if q in group['cumulative'].columns:
                fig.add_trace(
                    go.Scatter(
                        x=group['cumulative'].index,
                        y=group['cumulative'][q] * 100,
                        mode='lines',
                        name=f'{q}',
                        line=dict(color=colors.get(q, 'gray'), width=2)
                    ),
                    row=1, col=1
                )
        
        # 多空组合
        fig.add_trace(
            go.Scatter(
                x=group['long_short'].index,
                y=group['long_short'] * 100,
                mode='lines',
                name='多空(Q5-Q1)',
                line=dict(color='black', width=3, dash='dash')
            ),
            row=1, col=1
        )
        
        fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5, row=1, col=1)
        
        # 2. 分组年化收益柱状图
        mean_ret = group['mean_returns']
        fig.add_trace(
            go.Bar(
                x=mean_ret.index,
                y=mean_ret.values * 100,
                marker_color=[colors.get(q, 'gray') for q in mean_ret.index],
                text=[f'{v*100:.1f}%' for v in mean_ret.values],
                textposition='outside',
                showlegend=False
            ),
            row=2, col=1
        )
        
        fig.add_hline(y=0, line_dash="dot", line_color="black", row=2, col=1)
        
        # 3. IC时间序列
        fig.add_trace(
            go.Scatter(
                x=ic['daily_ic']['date'],
                y=ic['daily_ic']['IC'],
                mode='lines',
                name='IC',
                line=dict(color='#1f77b4', width=1),
                showlegend=False
            ),
            row=2, col=2
        )
        
        fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5, row=2, col=2)
        fig.add_hline(y=0.02, line_dash="dot", line_color="blue", opacity=0.3, row=2, col=2)
        fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", opacity=0.3, row=2, col=2)
        
        # 4. IC分布 (直方图 + 箱线图合并显示)
        fig.add_trace(
            go.Histogram(
                x=ic['daily_ic']['IC'],
                opacity=0.7,
                histnorm='probability density',
                name='IC分布',
                showlegend=False
            ),
            row=3, col=1
        )
        
        # 添加统计指标文本
        summary_text = (
            f"<b>关键指标</b><br>"
            f"IC均值: {ic['ic_mean']:.4f}<br>"
            f"IC IR: {ic['ic_ir']:.2f}<br>"
            f"IC>0占比: {ic['ic_positive_ratio']*100:.1f}%<br>"
            f"多空收益: {group['mean_returns']['Q5']-group['mean_returns']['Q1']:.2%}<br>"
            f"样本数: {ic['samples']:,}"
        )
        
        fig.add_annotation(
            x=0.98, y=0.02,
            xref='paper', yref='paper',
            text=summary_text,
            showarrow=False,
            font=dict(size=12),
            align='left',
            bgcolor='rgba(255,255,255,0.9)',
            bordercolor='gray',
            borderwidth=1
        )
        
        # 更新布局
        fig.update_layout(
            title=dict(
                text=f"<b>因子分析 Tear Sheet - {self.factor_name}</b><br>"
                     f"<sup>数据范围: 2015-2024 | 样本数: {ic['samples']:,}</sup>",
                x=0.5
            ),
            height=900,
            showlegend=True,
            legend=dict(
                yanchor="top", y=0.98,
                xanchor="left", x=0.01,
                bgcolor='rgba(255,255,255,0.8)'
            ),
            template='plotly_white'
        )
        
        # 更新轴标签
        fig.update_xaxes(title_text="日期", row=1, col=1)
        fig.update_yaxes(title_text="累计收益 (%)", row=1, col=1)
        fig.update_xaxes(title_text="分组", row=2, col=1)
        fig.update_yaxes(title_text="年化收益 (%)", row=2, col=1)
        fig.update_xaxes(title_text="日期", row=2, col=2)
        fig.update_yaxes(title_text="IC", row=2, col=2)
        fig.update_xaxes(title_text="IC", row=3, col=1)
        fig.update_yaxes(title_text="密度", row=3, col=1)
        
        return fig
    
    def get_summary(self) -> str:
        """获取分析摘要"""
        ic = self.results['ic']
        group = self.results['group']
        
        ls_ret = group['mean_returns']['Q5'] - group['mean_returns']['Q1']
        
        summary = f"""
## {self.factor_name} 因子分析摘要

### IC分析
- IC均值: {ic['ic_mean']:.4f}
- IC IR: {ic['ic_ir']:.2f}
- IC > 0 占比: {ic['ic_positive_ratio']*100:.1f}%

### 分组收益
"""
        for q, r in group['mean_returns'].items():
            summary += f"- {q}: {r*100:.2f}%\n"
        
        summary += f"- **多空(Q5-Q1)**: {ls_ret*100:.2f}%\n"
        
        return summary


def main():
    print("="*60)
    print("🎯 生成因子分析 Tear Sheet")
    print("="*60)
    
    # 分析因子
    analyzer = FactorAnalyzer('intraday_momentum')
    results = analyzer.analyze()
    
    # 生成图表
    print("\n📊 生成整合 Tear Sheet...")
    fig = analyzer.generate_tear_sheet()
    
    # 保存
    output_path = f"{OUTPUT_DIR}/factor_tearsheet.png"
    fig.write_image(output_path, scale=2)
    
    print(f"\n✅ 已保存到: {output_path}")
    
    # 打印摘要
    print(analyzer.get_summary())
    
    return output_path


if __name__ == '__main__':
    main()
