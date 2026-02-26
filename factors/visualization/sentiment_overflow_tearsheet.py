#!/usr/bin/env python3
"""
情绪溢出因子 Tear Sheet
"""

import sys
sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace')

import pandas as pd
import numpy as np
import psycopg2
from scipy import stats
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

OUTPUT_DIR = '/Users/xinzhan/.openclaw/workspace/quant_factor_system/output'


def load_factor_and_price():
    """加载因子和价格数据"""
    print("📊 加载数据...")
    
    # 加载因子
    factor_df = pd.read_csv(f"{OUTPUT_DIR}/sentiment_overflow_factor.csv")
    factor_df['time'] = pd.to_datetime(factor_df['time'])
    factor_df = factor_df.rename(columns={'factor': 'value'})
    
    print(f"   因子数据: {len(factor_df):,} 条")
    
    # 加载价格
    conn = psycopg2.connect(
        host='localhost', port=5432, database='quant_data',
        user='postgres', password='quant123'
    )
    cursor = conn.cursor()
    
    # 取因子对应时间段的价格
    start_date = factor_df['time'].min()
    end_date = factor_df['time'].max()
    
    cursor.execute(f"""
        SELECT symbol, time, close
        FROM price_daily
        WHERE time >= '{start_date}' AND time <= '{end_date}'
        ORDER BY symbol, time
    """)
    
    price_data = cursor.fetchall()
    price_df = pd.DataFrame(price_data, columns=['symbol', 'time', 'close'])
    price_df['time'] = pd.to_datetime(price_df['time'])
    
    conn.close()
    
    print(f"   价格数据: {len(price_df):,} 条")
    
    return factor_df, price_df


def compute_analysis(factor_df, price_df):
    """计算分析"""
    print("📈 计算IC和分组收益...")
    
    # 合并
    merged = pd.merge(factor_df, price_df, on=['symbol', 'time'], how='inner')
    merged = merged.sort_values(['symbol', 'time'])
    
    # T+1收益
    merged['return_1d'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
    merged = merged.dropna(subset=['value', 'return_1d'])
    merged = merged[merged['return_1d'].abs() < 0.11]
    
    print(f"   有效样本: {len(merged):,}")
    
    # IC
    ic_all, _ = stats.spearmanr(merged['value'], merged['return_1d'])
    
    daily_ic = merged.groupby('time').apply(
        lambda x: stats.spearmanr(x['value'], x['return_1d'])[0]
        if x['return_1d'].std() > 0 else 0
    ).reset_index()
    daily_ic.columns = ['date', 'IC']
    
    ic_mean = daily_ic['IC'].mean()
    ic_std = daily_ic['IC'].std()
    ic_ir = ic_mean / ic_std if ic_std > 0 else 0
    ic_pos_ratio = (daily_ic['IC'] > 0).mean()
    
    # 分组收益
    merged['group'] = pd.qcut(merged['value'], 5, labels=['Q1','Q2','Q3','Q4','Q5'], duplicates='drop')
    
    group_ret = merged.groupby(['time', 'group'])['return_1d'].mean()
    group_pivot = group_ret.unstack(level='group')
    cumulative = (1 + group_pivot).cumprod() - 1
    
    mean_ret = group_pivot.mean() * 252
    
    return {
        'ic_all': ic_all,
        'ic_mean': ic_mean,
        'ic_ir': ic_ir,
        'ic_pos_ratio': ic_pos_ratio,
        'daily_ic': daily_ic,
        'cumulative': cumulative,
        'mean_ret': mean_ret,
        'samples': len(merged)
    }


def generate_tear_sheet(result):
    """生成Tear Sheet"""
    print("📊 生成图表...")
    
    ic = result
    cumulative = result['cumulative']
    mean_ret = result['mean_ret']
    
    # 创建图
    fig = make_subplots(
        rows=3, cols=2,
        subplot_titles=(
            '分组累计收益曲线',
            '分组年化收益',
            'IC时间序列',
            'IC分布',
        ),
        specs=[
            [{"colspan": 2}, None],
            [{}, {}],
            [{"colspan": 2}, None],
        ],
        vertical_spacing=0.08
    )
    
    colors = {'Q1': '#d62728', 'Q2': '#ff7f0e', 'Q3': '#ffbb78', 
              'Q4': '#98df8a', 'Q5': '#2ca02c'}
    
    # 分组累计收益
    for q in ['Q1','Q2','Q3','Q4','Q5']:
        if q in cumulative.columns:
            fig.add_trace(
                go.Scatter(x=cumulative.index, y=cumulative[q]*100, 
                          mode='lines', name=q, 
                          line=dict(color=colors.get(q,'gray'), width=2)),
                row=1, col=1
            )
    
    # 多空
    if 'Q5' in cumulative.columns and 'Q1' in cumulative.columns:
        ls = cumulative['Q5'] - cumulative['Q1']
        fig.add_trace(
            go.Scatter(x=ls.index, y=ls*100, mode='lines', 
                      name='多空(Q5-Q1)', line=dict(color='black', width=3, dash='dash')),
            row=1, col=1
        )
    
    fig.add_hline(y=0, line_dash="dot", row=1, col=1)
    
    # 分组收益柱状图
    fig.add_trace(
        go.Bar(x=mean_ret.index, y=mean_ret.values*100,
              marker_color=[colors.get(q,'gray') for q in mean_ret.index],
              text=[f'{v*100:.1f}%' for v in mean_ret.values],
              textposition='outside', showlegend=False),
        row=2, col=1
    )
    fig.add_hline(y=0, row=2, col=1)
    
    # IC时间序列
    fig.add_trace(
        go.Scatter(x=result['daily_ic']['date'], y=result['daily_ic']['IC'],
                  mode='lines', name='IC', line=dict(color='#1f77b4', width=1), showlegend=False),
        row=2, col=2
    )
    fig.add_hline(y=0, row=2, col=2)
    fig.add_hline(y=0.02, line_dash="dot", opacity=0.3, row=2, col=2)
    fig.add_hline(y=-0.02, line_dash="dot", opacity=0.3, row=2, col=2)
    
    # IC分布
    fig.add_trace(
        go.Histogram(x=result['daily_ic']['IC'], opacity=0.7,
                    histnorm='probability density', showlegend=False),
        row=3, col=1
    )
    
    # 摘要
    summary = f"<b>关键指标</b><br>" \
              f"IC均值: {result['ic_mean']:.4f}<br>" \
              f"IC IR: {result['ic_ir']:.2f}<br>" \
              f"IC>0占比: {result['ic_pos_ratio']*100:.1f}%<br>" \
              f"样本数: {result['samples']:,}"
    
    fig.add_annotation(x=0.98, y=0.02, xref='paper', yref='paper',
                      text=summary, showarrow=False, font=dict(size=12),
                      align='left', bgcolor='rgba(255,255,255,0.9)')
    
    fig.update_layout(
        title=dict(text=f"<b>情绪溢出因子分析 Tear Sheet</b><br><sup>数据: 2024年 | 样本: {result['samples']:,}</sup>", x=0.5),
        height=900, template='plotly_white'
    )
    
    return fig


def main():
    print("="*60)
    print("🎯 情绪溢出因子分析")
    print("="*60)
    
    factor_df, price_df = load_factor_and_price()
    result = compute_analysis(factor_df, price_df)
    fig = generate_tear_sheet(result)
    
    output_path = f"{OUTPUT_DIR}/sentiment_overflow_tearsheet.png"
    fig.write_image(output_path, scale=2)
    
    print(f"\n✅ 已保存到: {output_path}")
    
    print("\n" + "="*50)
    print("📈 分析结果")
    print("="*50)
    print(f"IC均值: {result['ic_mean']:.4f}")
    print(f"IC IR: {result['ic_ir']:.2f}")
    print(f"IC>0占比: {result['ic_pos_ratio']*100:.1f}%")
    print("\n分组收益:")
    for q, r in result['mean_ret'].items():
        print(f"   {q}: {r*100:.2f}%")
    ls = result['mean_ret']['Q5'] - result['mean_ret']['Q1']
    print(f"   多空: {ls*100:.2f}%")
    
    return output_path


if __name__ == '__main__':
    main()
