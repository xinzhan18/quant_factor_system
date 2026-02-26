#!/usr/bin/env python3
"""
模糊金额比因子 Tear Sheet
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

OUTPUT_DIR = '/Users/xinzhan/.openclaw/workspace/quant_factor_system/data'


def load_factor_and_price():
    """加载因子和价格数据"""
    print("📊 加载数据...")
    
    # 加载因子
    factor_df = pd.read_csv(f"{OUTPUT_DIR}/ambiguous_amount_ratio.csv")
    factor_df['month'] = pd.to_datetime(factor_df['month'])
    
    # 重命名value列
    if 'ambiguous_ratio_monthly' in factor_df.columns:
        factor_df = factor_df.rename(columns={'ambiguous_ratio_monthly': 'value'})
    
    # 创建period列
    factor_df['period'] = factor_df['month'].dt.to_period('M')
    
    print(f"   因子数据: {len(factor_df):,} 条")
    print(f"   因子时间范围: {factor_df['month'].min()} ~ {factor_df['month'].max()}")
    print(f"   股票数: {factor_df['symbol'].nunique()}")
    
    # 加载价格 - 日线数据
    conn = psycopg2.connect(
        host='localhost', port=5432, database='quant_data',
        user='postgres', password='quant123'
    )
    cursor = conn.cursor()
    
    # 获取因子中的股票列表，用于限制查询
    factor_symbols = factor_df['symbol'].str.replace('.SH', '.XSHG').unique().tolist()
    
    # 限制查询的股票数量（取前50只）
    query_symbols = factor_symbols[:50]
    
    # 取因子对应时间段的日线价格（扩展到包含下月收益）
    start_date = factor_df['month'].min() - pd.offsets.MonthBegin(1)
    end_date = factor_df['month'].max() + pd.offsets.MonthEnd(2)  # 多取一个月用于计算next_return
    
    symbols_str = ','.join([f"'{s}'" for s in query_symbols])
    cursor.execute(f"""
        SELECT symbol, time, close
        FROM price_daily
        WHERE time >= '{start_date}' AND time <= '{end_date}'
        AND symbol IN ({symbols_str})
        ORDER BY symbol, time
    """)
    
    price_data = cursor.fetchall()
    price_df = pd.DataFrame(price_data, columns=['symbol', 'time', 'close'])
    price_df['time'] = pd.to_datetime(price_df['time'])
    price_df = price_df.sort_values(['symbol', 'time'])
    
    # 计算日收益率
    price_df['daily_return'] = price_df.groupby('symbol')['close'].pct_change()
    
    # 计算月度收益 (当月收益)
    price_df['period'] = price_df['time'].dt.to_period('M')
    monthly_price = price_df.groupby(['symbol', 'period']).agg({
        'close': 'last',
        'daily_return': lambda x: (1 + x).prod() - 1  # 月度累积收益
    }).reset_index()
    monthly_price = monthly_price.rename(columns={'daily_return': 'monthly_return'})
    
    # 计算下月收益 (T+1)
    monthly_price = monthly_price.sort_values(['symbol', 'period'])
    monthly_price['next_return'] = monthly_price.groupby('symbol')['monthly_return'].shift(-1)
    
    conn.close()
    
    print(f"   月度价格数据: {len(monthly_price):,} 条")
    print(f"   价格时间范围: {monthly_price['period'].min()} ~ {monthly_price['period'].max()}")
    
    return factor_df, monthly_price


def compute_analysis(factor_df, monthly_price):
    """计算分析"""
    print("📈 计算IC和分组收益...")
    
    # 统一symbol格式 - 处理后缀差异
    # 因子: 000001.XSHE, 600000.SH
    # 价格: 000001.XSHE, 600000.XSHG
    factor_df = factor_df.copy()
    factor_df['symbol_for_merge'] = factor_df['symbol'].str.replace('.SH', '.XSHG')
    monthly_price = monthly_price.copy()
    monthly_price['symbol_for_merge'] = monthly_price['symbol']
    
    # 合并
    merged = pd.merge(factor_df, monthly_price, on=['symbol_for_merge', 'period'], how='inner')
    merged = merged.sort_values(['symbol_x', 'period'])
    merged['symbol'] = merged['symbol_x']  # 使用factor的symbol
    
    print(f"   合并后: {len(merged)} 条")
    
    # 下月收益
    merged = merged.dropna(subset=['value', 'next_return'])
    merged = merged[merged['next_return'].abs() < 0.50]  # 月度涨跌幅过滤
    
    print(f"   有效样本: {len(merged):,}")
    
    if len(merged) < 20:
        print("⚠️ 数据量不足，无法进行可靠分析")
        print(f"   需要至少20条记录，当前只有 {len(merged)} 条")
        return None
    
    # IC (Spearman)
    ic_all, _ = stats.spearmanr(merged['value'], merged['next_return'])
    
    # 每日/月IC
    daily_ic = merged.groupby('period').apply(
        lambda x: stats.spearmanr(x['value'], x['next_return'])[0]
    )
    daily_ic = daily_ic.dropna()
    
    ic_mean = daily_ic.mean()
    ic_std = daily_ic.std()
    ic_ir = ic_mean / ic_std if ic_std > 0 else 0
    ic_positive_ratio = (daily_ic > 0).sum() / len(daily_ic) * 100
    
    print(f"   IC均值: {ic_mean:.4f}")
    print(f"   IC IR: {ic_ir:.4f}")
    print(f"   IC > 0 占比: {ic_positive_ratio:.2f}%")
    
    # 分组收益
    merged['group'] = pd.qcut(merged['value'], 5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'])
    
    # 每组收益
    group_returns = merged.groupby('group')['next_return'].mean() * 100
    
    # 多空组合
    long_short = group_returns['Q5'] - group_returns['Q1']
    
    # 累计收益
    group_cum = merged.groupby(['period', 'group'])['next_return'].mean().unstack()
    group_cum = (1 + group_cum).cumprod()
    
    print(f"   多空年化: {long_short * 12:.2f}%")
    
    return {
        'ic_mean': ic_mean,
        'ic_std': ic_std,
        'ic_ir': ic_ir,
        'ic_positive_ratio': ic_positive_ratio,
        'ic_all': ic_all,
        'group_returns': group_returns,
        'long_short': long_short,
        'group_cum': group_cum,
        'daily_ic': daily_ic,
        'merged': merged
    }


def create_tearsheet(results, output_path):
    """生成Tear Sheet"""
    print("📊 生成Tear Sheet...")
    
    merged = results['merged']
    daily_ic = results['daily_ic']
    group_returns = results['group_returns']
    group_cum = results['group_cum']
    
    # 转换period为字符串（避免JSON序列化问题）
    if hasattr(group_cum.index, 'dtype'):
        if group_cum.index.dtype == 'period[M]':
            group_cum.index = group_cum.index.astype(str)
    if hasattr(daily_ic.index, 'dtype'):
        if daily_ic.index.dtype == 'period[M]':
            daily_ic.index = daily_ic.index.astype(str)
    
    # 创建图表
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '分组累计收益', 'IC时间序列',
            '分组收益柱状图', 'IC分布'
        ),
        specs=[[{"type": "scatter"}, {"type": "scatter"}],
               [{"type": "bar"}, {"type": "histogram"}]]
    )
    
    # 1. 分组累计收益
    colors = ['#ff6b6b', '#feca57', '#48dbfb', '#1dd1a1', '#5f27cd']
    for i, col in enumerate(['Q1', 'Q2', 'Q3', 'Q4', 'Q5']):
        if col in group_cum.columns:
            fig.add_trace(
                go.Scatter(
                    x=group_cum.index,
                    y=group_cum[col],
                    name=f'{col} ({"低" if i < 2 else "高"}因子)',
                    line=dict(color=colors[i], width=2)
                ),
                row=1, col=1
            )
    
    # 2. IC时间序列
    fig.add_trace(
        go.Scatter(
            x=daily_ic.index,
            y=daily_ic.values,
            name='IC',
            line=dict(color='#00d2d3', width=1.5),
            mode='lines'
        ),
        row=1, col=2
    )
    fig.add_hline(y=0, line_dash="dash", line_color="gray", row=1, col=2)
    
    # 3. 分组收益柱状图
    fig.add_trace(
        go.Bar(
            x=group_returns.index,
            y=group_returns.values,
            name='月均收益(%)',
            marker_color=['#ff6b6b', '#feca57', '#48dbfb', '#1dd1a1', '#5f27cd']
        ),
        row=2, col=1
    )
    
    # 4. IC分布
    fig.add_trace(
        go.Histogram(
            x=daily_ic.values,
            name='IC分布',
            nbinsx=20,
            marker_color='#00d2d3'
        ),
        row=2, col=2
    )
    fig.add_vline(x=0, line_dash="dash", line_color="gray", row=2, col=2)
    
    # 更新布局
    fig.update_layout(
        title=dict(
            text='模糊金额比因子 Tear Sheet',
            font=dict(size=20)
        ),
        height=700,
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02),
        template='plotly_white'
    )
    
    # 保存
    fig.write_html(output_path)
    print(f"   已保存: {output_path}")
    
    return fig


def main():
    """主函数"""
    print("=" * 70)
    print("模糊金额比因子分析")
    print("=" * 70)
    
    # 加载数据
    factor_df, price_df = load_factor_and_price()
    
    # 计算分析
    results = compute_analysis(factor_df, price_df)
    
    if results is None:
        print("❌ 分析失败")
        return
    
    # 生成报告
    output_path = f"{OUTPUT_DIR}/ambiguous_amount_ratio_tearsheet.html"
    create_tearsheet(results, output_path)
    
    # 打印摘要
    print("\n" + "=" * 70)
    print("📋 分析摘要")
    print("=" * 70)
    print(f"IC均值: {results['ic_mean']:.4f}")
    print(f"IC IR: {results['ic_ir']:.4f}")
    print(f"IC > 0 占比: {results['ic_positive_ratio']:.2f}%")
    print(f"多空月均: {results['long_short']*100:.2f}%")
    print(f"多空年化: {results['long_short']*12*100:.2f}%")
    print("\n分组收益:")
    for g, r in results['group_returns'].items():
        print(f"  {g}: {r:.2f}%")
    print("=" * 70)


if __name__ == "__main__":
    main()
