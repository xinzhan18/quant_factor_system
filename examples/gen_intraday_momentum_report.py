#!/usr/bin/env python3
"""
生成日内动量因子的完整分析报告
包含 AlphaLens 风格的分组累计收益曲线
"""

import sys
sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace')

import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

import psycopg2

# 设置输出目录
OUTPUT_DIR = '/Users/xinzhan/.openclaw/workspace/quant_factor_system/output'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_daily_data(n_stocks: int = 200, n_days: int = 500):
    """从数据库获取日线数据"""
    print("📊 从数据库获取日线数据...")
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='quant_data',
        user='postgres',
        password='quant123'
    )
    cursor = conn.cursor()
    
    try:
        # 获取股票列表
        cursor.execute("""
            SELECT DISTINCT symbol 
            FROM price_daily 
            ORDER BY symbol 
            LIMIT %s
        """, (n_stocks,))
        stocks = [row[0] for row in cursor.fetchall()]
        print(f"   获取到 {len(stocks)} 只股票")
        
        # 获取日期范围
        cursor.execute("SELECT MAX(time) FROM price_daily")
        end_date = cursor.fetchone()[0]
        start_date = end_date - timedelta(days=n_days)
        
        # 获取日线数据
        cursor.execute("""
            SELECT symbol, time, open, high, low, close, volume
            FROM price_daily 
            WHERE symbol IN %s 
            AND time >= %s 
            AND time <= %s
            ORDER BY symbol, time
        """, (tuple(stocks), start_date, end_date))
        
        data = cursor.fetchall()
        print(f"   获取到 {len(data):,} 条日线数据")
        
        # 转换为 DataFrame
        df = pd.DataFrame(data, columns=['symbol', 'time', 'open', 'high', 'low', 'close', 'volume'])
        df['time'] = pd.to_datetime(df['time'])
        
        return df
        
    finally:
        conn.close()


def compute_intraday_momentum_factor(price_df: pd.DataFrame) -> tuple:
    """
    计算日内动量变化因子
    
    公式: -1 * delta((((close-low)-(high-close))/(high-low)), 1)
    
    这个因子使用日线的 high/low/close 来近似日内形态
    """
    print("📊 计算日内动量因子...")
    
    # 按股票排序
    price_df = price_df.sort_values(['symbol', 'time']).reset_index(drop=True)
    
    # 计算因子
    high = price_df['high']
    low = price_df['low']
    close = price_df['close']
    
    # (close-low)-(high-close) / (high-low)
    range_ = high - low
    range_ = range_.replace(0, np.nan)
    
    intraday_pattern = ((close - low) - (high - close)) / range_
    
    # 1日变化率 (按股票分组)
    delta_factor = intraday_pattern.groupby(price_df['symbol']).diff(1)
    
    # 取负值
    result = -1 * delta_factor
    result = result.replace([np.inf, -np.inf], np.nan)
    
    # 构建因子 DataFrame
    factor_df = price_df[['symbol', 'time']].copy()
    factor_df['value'] = result.values
    
    # 价格 DataFrame
    price_factor_df = price_df[['symbol', 'time', 'close']].copy()
    
    print(f"   因子数据: {len(factor_df):,} 条")
    
    return factor_df, price_factor_df


def compute_group_returns(factor_df: pd.DataFrame, price_df: pd.DataFrame, n_groups: int = 5) -> dict:
    """计算分组收益"""
    print("\n📊 计算分组收益...")
    
    # 合并数据
    merged = pd.merge(factor_df, price_df, on=['symbol', 'time'], how='inner')
    
    if len(merged) < 100:
        return {'error': '数据量不足'}
    
    # 计算未来收益率 (T+1)
    merged = merged.sort_values(['symbol', 'time'])
    merged['future_return'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
    merged = merged.dropna(subset=['value', 'future_return'])
    merged = merged[merged['future_return'].abs() < 0.11]  # 去除涨跌停
    
    if len(merged) < 100:
        return {'error': '合并后数据不足'}
    
    print(f"   有效样本: {len(merged):,} 条")
    
    # 分组
    labels = [f'Q{i+1}' for i in range(n_groups)]
    merged['group'] = pd.qcut(merged['value'], q=n_groups, labels=labels, duplicates='drop')
    
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
    
    return {
        'group_returns_pivot': group_returns_pivot,
        'cumulative_returns': cumulative_returns,
        'mean_returns': mean_returns,
        'std_returns': std_returns,
        'sharpe': sharpe,
        'n_groups': n_groups,
        'samples': len(merged)
    }


def compute_ic(factor_df: pd.DataFrame, price_df: pd.DataFrame) -> dict:
    """计算IC"""
    print("\n📊 计算IC...")
    
    # 合并数据
    merged = pd.merge(factor_df, price_df, on=['symbol', 'time'], how='inner')
    
    # 计算未来收益率
    merged = merged.sort_values(['symbol', 'time'])
    merged['future_return'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
    merged = merged.dropna(subset=['value', 'future_return'])
    merged = merged[merged['future_return'].abs() < 0.11]
    
    if len(merged) < 100:
        return {'error': '数据不足'}
    
    # 整体IC (Spearman)
    from scipy import stats
    ic_all, p_value = stats.spearmanr(merged['value'], merged['future_return'])
    
    # 每日IC
    daily_ic = merged.groupby('time').apply(
        lambda x: stats.spearmanr(x['value'], x['future_return'])[0]
        if x['future_return'].std() > 0 else 0
    ).reset_index()
    daily_ic.columns = ['date', 'IC']
    
    print(f"   整体IC: {ic_all:.4f}")
    print(f"   有效样本: {len(merged):,}")
    
    return {
        'ic_all': ic_all,
        'p_value': p_value,
        'samples': len(merged),
        'rolling_ic': daily_ic
    }


def plot_quantile_cumulative_returns_alpha_style(
    cumulative_returns: pd.DataFrame,
    title: str = "分组累计收益曲线"
) -> go.Figure:
    """
    AlphaLens 风格的分组累计收益曲线
    显示每个分组的独立曲线
    """
    # 颜色映射：Q1(红色) -> Q5(绿色)
    colors = {
        'Q1': '#d62728',  # 红色
        'Q2': '#ff7f0e',  # 橙色
        'Q3': '#ffbb78',  # 浅橙
        'Q4': '#98df8a',  # 浅绿
        'Q5': '#2ca02c',  # 绿色
    }
    
    fig = go.Figure()
    
    # 添加每个分组的曲线
    for group in cumulative_returns.columns:
        fig.add_trace(go.Scatter(
            x=cumulative_returns.index,
            y=cumulative_returns[group] * 100,  # 转为百分比
            mode='lines',
            name=group,
            line=dict(color=colors.get(group, 'gray'), width=2),
            opacity=0.9
        ))
    
    # 添加多空组合 (Q5 - Q1)
    if 'Q5' in cumulative_returns.columns and 'Q1' in cumulative_returns.columns:
        long_short = (cumulative_returns['Q5'] - cumulative_returns['Q1']) * 100
        fig.add_trace(go.Scatter(
            x=long_short.index,
            y=long_short,
            mode='lines',
            name='多空(Q5-Q1)',
            line=dict(color='black', width=3, dash='dash'),
            opacity=0.8
        ))
    
    # 添加零线
    fig.add_hline(y=0, line_dash="dot", line_color="gray", opacity=0.5)
    
    fig.update_layout(
        title=title,
        template='plotly_white',
        height=500,
        xaxis_title='日期',
        yaxis_title='累计收益 (%)',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor='rgba(255,255,255,0.8)'
        ),
        hovermode='x unified'
    )
    
    return fig


def plot_quantile_returns_bar(mean_returns: pd.Series, title: str = "分组年化收益") -> go.Figure:
    """分组年化收益柱状图"""
    colors = ['#d62728', '#ff7f0e', '#ffbb78', '#98df8a', '#2ca02c'][:len(mean_returns)]
    
    fig = px.bar(
        x=mean_returns.index,
        y=mean_returns.values * 100,
        title=title,
        labels={'x': '分组', 'y': '年化收益率 (%)'},
        color=mean_returns.values * 100,
        color_continuous_scale='RdYlGn'
    )
    
    fig.add_hline(y=0, line_dash="dot", line_color="black")
    
    # 添加数值标签
    for i, (idx, val) in enumerate(mean_returns.items()):
        fig.add_annotation(
            x=idx,
            y=val * 100,
            text=f"{val*100:.2f}%",
            showarrow=False,
            yshift=10,
            font=dict(size=12)
        )
    
    fig.update_layout(
        template='plotly_white',
        height=400,
        coloraxis_colorbar=dict(title="收益率 (%)")
    )
    
    return fig


def plot_ic_timeseries(rolling_ic: pd.DataFrame, title: str = "IC时间序列") -> go.Figure:
    """IC时间序列图"""
    fig = px.line(
        rolling_ic,
        x='date',
        y='IC',
        title=title,
        color_discrete_sequence=['#1f77b4']
    )
    
    fig.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.5)
    fig.add_hline(y=0.02, line_dash="dot", line_color="blue", opacity=0.3)
    fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", opacity=0.3)
    
    fig.update_layout(
        template='plotly_white',
        height=400,
        xaxis_title='日期',
        yaxis_title='IC'
    )
    
    return fig


def plot_ic_distribution(rolling_ic: pd.DataFrame, title: str = "IC分布") -> go.Figure:
    """IC分布图"""
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=['IC分布直方图', 'IC箱线图'],
        specs=[[{"type": "histogram"}, {"type": "box"}]]
    )
    
    # 直方图
    fig.add_trace(
        go.Histogram(
            x=rolling_ic['IC'],
            opacity=0.7,
            histnorm='probability density',
            name='IC分布'
        ),
        row=1, col=1
    )
    
    # 箱线图
    fig.add_trace(
        go.Box(
            y=rolling_ic['IC'],
            boxpoints='outliers',
            name='IC'
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


def compute_and_analyze():
    """执行完整分析"""
    print("="*60)
    print("🎯 日内动量因子分析")
    print("="*60)
    
    # 1. 获取数据
    price_df = get_daily_data(n_stocks=200, n_days=500)
    
    # 2. 计算因子
    factor_df, price_factor_df = compute_intraday_momentum_factor(price_df)
    
    # 3. 分组收益分析
    result = compute_group_returns(factor_df, price_factor_df, n_groups=5)
    
    # 4. IC分析
    ic_result = compute_ic(factor_df, price_factor_df)
    
    # 5. 生成图表
    print("\n📊 生成图表...")
    
    # 分组累计收益曲线 (AlphaLens风格)
    fig1 = plot_quantile_cumulative_returns_alpha_style(
        result['cumulative_returns'],
        "日内动量因子 - 分组累计收益曲线"
    )
    
    # 分组年化收益柱状图
    fig2 = plot_quantile_returns_bar(
        result['mean_returns'],
        "日内动量因子 - 分组年化收益"
    )
    
    # IC时间序列
    fig3 = plot_ic_timeseries(
        ic_result['rolling_ic'],
        "日内动量因子 - IC时间序列"
    )
    
    # IC分布
    fig4 = plot_ic_distribution(
        ic_result['rolling_ic'],
        "日内动量因子 - IC分布"
    )
    
    # 6. 保存图表
    print("\n💾 保存图表...")
    
    fig1.write_image(f"{OUTPUT_DIR}/intraday_momentum_quantile_returns.png", scale=2)
    fig2.write_image(f"{OUTPUT_DIR}/intraday_momentum_group_returns.png", scale=2)
    fig3.write_image(f"{OUTPUT_DIR}/intraday_momentum_ic.png", scale=2)
    fig4.write_image(f"{OUTPUT_DIR}/intraday_momentum_ic_distribution.png", scale=2)
    
    # 7. 生成统计摘要
    print("\n" + "="*60)
    print("📈 分析结果摘要")
    print("="*60)
    
    print("\n分组收益 (年化):")
    for group, ret in result['mean_returns'].items():
        print(f"   {group}: {ret*100:.2f}%")
    
    ls_ret = result['mean_returns']['Q5'] - result['mean_returns']['Q1']
    print(f"   多空(Q5-Q1): {ls_ret*100:.2f}%")
    
    print(f"\nIC分析:")
    print(f"   整体IC: {ic_result.get('ic_all', 0):.4f}")
    print(f"   IC均值: {ic_result['rolling_ic']['IC'].mean():.4f}")
    print(f"   IC标准差: {ic_result['rolling_ic']['IC'].std():.4f}")
    print(f"   IC > 0 占比: {(ic_result['rolling_ic']['IC'] > 0).mean()*100:.1f}%")
    
    print("\n" + "="*60)
    print(f"✅ 图表已保存到 {OUTPUT_DIR}/")
    print("="*60)
    
    # 返回文件列表
    return {
        'quantile_returns': f"{OUTPUT_DIR}/intraday_momentum_quantile_returns.png",
        'group_returns': f"{OUTPUT_DIR}/intraday_momentum_group_returns.png",
        'ic': f"{OUTPUT_DIR}/intraday_momentum_ic.png",
        'ic_distribution': f"{OUTPUT_DIR}/intraday_momentum_ic_distribution.png"
    }


if __name__ == '__main__':
    files = compute_and_analyze()
    print("\n生成的文件:")
    for name, path in files.items():
        print(f"   {name}: {path}")
