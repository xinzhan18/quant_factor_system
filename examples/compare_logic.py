#!/usr/bin/env python3
"""
对比旧逻辑和新逻辑的计算差异
"""

import sys
sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace')

import os
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import timedelta
import warnings
warnings.filterwarnings('ignore')

import psycopg2
from scipy import stats

OUTPUT_DIR = '/Users/xinzhan/.openclaw/workspace/quant_factor_system/output'


def get_daily_data():
    """从数据库获取全量日线数据"""
    print("📊 获取全量日线数据 (2015-2024)...")
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='quant_data',
        user='postgres',
        password='quant123'
    )
    cursor = conn.cursor()
    
    cursor.execute("SELECT DISTINCT symbol FROM price_daily ORDER BY symbol")
    stocks = [row[0] for row in cursor.fetchall()]
    print(f"   股票数量: {len(stocks)}")
    
    cursor.execute("""
        SELECT symbol, time, open, high, low, close, volume
        FROM price_daily 
        WHERE time >= '2015-01-01' AND time <= '2024-12-31'
        ORDER BY symbol, time
    """)
    
    data = cursor.fetchall()
    print(f"   获取到 {len(data):,} 条数据")
    
    df = pd.DataFrame(data, columns=['symbol', 'time', 'open', 'high', 'low', 'close', 'volume'])
    df['time'] = pd.to_datetime(df['time'])
    
    conn.close()
    return df


def compute_intraday_momentum_factor(price_df: pd.DataFrame) -> tuple:
    """计算日内动量因子"""
    price_df = price_df.sort_values(['symbol', 'time']).reset_index(drop=True)
    
    high = price_df['high']
    low = price_df['low']
    close = price_df['close']
    
    range_ = high - low
    range_ = range_.replace(0, np.nan)
    
    intraday_pattern = ((close - low) - (high - close)) / range_
    delta_factor = intraday_pattern.groupby(price_df['symbol']).diff(1)
    result = -1 * delta_factor
    result = result.replace([np.inf, -np.inf], np.nan)
    
    factor_df = price_df[['symbol', 'time']].copy()
    factor_df['value'] = result.values
    
    price_factor_df = price_df[['symbol', 'time', 'close']].copy()
    
    return factor_df, price_factor_df


def compute_ic_old_logic(factor_df: pd.DataFrame, price_df: pd.DataFrame) -> dict:
    """
    旧逻辑：没有按股票分组的收益率计算
    错误方式：close.pct_change().shift(-1)
    """
    print("\n🔍 旧逻辑计算 (错误方式)...")
    
    merged = pd.merge(factor_df, price_df, on=['symbol', 'time'], how='inner')
    merged = merged.sort_values(['symbol', 'time'])
    
    # 旧逻辑：没有按股票分组！
    merged['future_return_wrong'] = merged['close'].pct_change().shift(-1)
    
    merged = merged.dropna(subset=['value', 'future_return_wrong'])
    merged = merged[merged['future_return_wrong'].abs() < 0.11]
    
    if len(merged) < 100:
        return {'error': '数据不足'}
    
    # IC (错误方式)
    ic_wrong = merged['value'].corr(merged['future_return_wrong'])
    
    print(f"   旧逻辑 IC: {ic_wrong:.4f}")
    
    return {
        'ic_wrong': ic_wrong,
        'samples': len(merged)
    }


def compute_ic_new_logic(factor_df: pd.DataFrame, price_df: pd.DataFrame) -> dict:
    """
    新逻辑：按股票分组的T+1收益率计算
    正确方式：groupby('symbol').pct_change().shift(-1)
    """
    print("\n✅ 新逻辑计算 (正确方式)...")
    
    merged = pd.merge(factor_df, price_df, on=['symbol', 'time'], how='inner')
    merged = merged.sort_values(['symbol', 'time'])
    
    # 新逻辑：按股票分组
    merged['future_return_correct'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
    
    merged = merged.dropna(subset=['value', 'future_return_correct'])
    merged = merged[merged['future_return_correct'].abs() < 0.11]
    
    if len(merged) < 100:
        return {'error': '数据不足'}
    
    # IC (正确方式)
    ic_correct = stats.spearmanr(merged['value'], merged['future_return_correct'])[0]
    
    print(f"   新逻辑 IC (Spearman): {ic_correct:.4f}")
    
    # 每日IC
    daily_ic = merged.groupby('time').apply(
        lambda x: stats.spearmanr(x['value'], x['future_return_correct'])[0]
        if x['future_return_correct'].std() > 0 else 0
    ).reset_index()
    daily_ic.columns = ['date', 'IC']
    
    print(f"   IC均值: {daily_ic['IC'].mean():.4f}")
    print(f"   IC > 0 占比: {(daily_ic['IC'] > 0).mean()*100:.1f}%")
    
    return {
        'ic_correct': ic_correct,
        'samples': len(merged),
        'daily_ic': daily_ic
    }


def compute_group_returns_new_logic(factor_df: pd.DataFrame, price_df: pd.DataFrame) -> dict:
    """用新逻辑计算分组收益"""
    print("\n📊 新逻辑分组收益计算...")
    
    merged = pd.merge(factor_df, price_df, on=['symbol', 'time'], how='inner')
    merged = merged.sort_values(['symbol', 'time'])
    
    # 正确的T+1收益
    merged['future_return'] = merged.groupby('symbol')['close'].pct_change().shift(-1)
    merged = merged.dropna(subset=['value', 'future_return'])
    merged = merged[merged['future_return'].abs() < 0.11]
    
    print(f"   有效样本: {len(merged):,}")
    
    # 分组
    merged['group'] = pd.qcut(merged['value'], 5, labels=['Q1','Q2','Q3','Q4','Q5'], duplicates='drop')
    
    # 分组收益
    group_returns = merged.groupby(['time', 'group'])['future_return'].mean().reset_index()
    group_pivot = group_returns.pivot(index='time', columns='group', values='future_return')
    cumulative = (1 + group_pivot).cumprod() - 1
    
    mean_returns = group_pivot.mean() * 252
    
    print("\n分组年化收益 (新逻辑):")
    for g, r in mean_returns.items():
        print(f"   {g}: {r*100:.2f}%")
    
    ls = mean_returns['Q5'] - mean_returns['Q1']
    print(f"   多空(Q5-Q1): {ls*100:.2f}%")
    
    return {
        'cumulative_returns': cumulative,
        'mean_returns': mean_returns
    }


def compute_group_returns_old_logic(factor_df: pd.DataFrame, price_df: pd.DataFrame) -> dict:
    """用旧逻辑计算分组收益"""
    print("\n📊 旧逻辑分组收益计算...")
    
    merged = pd.merge(factor_df, price_df, on=['symbol', 'time'], how='inner')
    merged = merged.sort_values(['symbol', 'time'])
    
    # 错误的当日收益
    merged['future_return_wrong'] = merged['close'].pct_change().shift(-1)
    merged = merged.dropna(subset=['value', 'future_return_wrong'])
    merged = merged[merged['future_return_wrong'].abs() < 0.11]
    
    print(f"   有效样本: {len(merged):,}")
    
    # 分组
    merged['group'] = pd.qcut(merged['value'], 5, labels=['Q1','Q2','Q3','Q4','Q5'], duplicates='drop')
    
    # 分组收益
    group_returns = merged.groupby(['time', 'group'])['future_return_wrong'].mean().reset_index()
    group_pivot = group_returns.pivot(index='time', columns='group', values='future_return_wrong')
    cumulative = (1 + group_pivot).cumprod() - 1
    
    mean_returns = group_pivot.mean() * 252
    
    print("\n分组年化收益 (旧逻辑):")
    for g, r in mean_returns.items():
        print(f"   {g}: {r*100:.2f}%")
    
    ls = mean_returns['Q5'] - mean_returns['Q1']
    print(f"   多空(Q5-Q1): {ls*100:.2f}%")
    
    return {
        'cumulative_returns': cumulative,
        'mean_returns': mean_returns
    }


def main():
    print("="*60)
    print("🔍 因子计算逻辑差异分析")
    print("="*60)
    
    # 获取数据
    price_df = get_daily_data()
    
    # 计算因子
    factor_df, price_factor_df = compute_intraday_momentum_factor(price_df)
    
    # 对比两种逻辑
    old_result = compute_ic_old_logic(factor_df, price_factor_df)
    new_result = compute_ic_new_logic(factor_df, price_factor_df)
    
    old_group = compute_group_returns_old_logic(factor_df, price_factor_df)
    new_group = compute_group_returns_new_logic(factor_df, price_factor_df)
    
    # 绘制对比图
    print("\n📊 生成对比图...")
    
    fig = go.Figure()
    
    # 旧逻辑
    for group in old_group['cumulative_returns'].columns:
        fig.add_trace(go.Scatter(
            x=old_group['cumulative_returns'].index,
            y=old_group['cumulative_returns'][group] * 100,
            mode='lines',
            name=f'{group} (旧)',
            line=dict(width=2, dash='dot')
        ))
    
    # 新逻辑
    for group in new_group['cumulative_returns'].columns:
        fig.add_trace(go.Scatter(
            x=new_group['cumulative_returns'].index,
            y=new_group['cumulative_returns'][group] * 100,
            mode='lines',
            name=f'{group} (新)',
            line=dict(width=2)
        ))
    
    fig.update_layout(
        title='旧逻辑 vs 新逻辑 - 分组累计收益对比',
        template='plotly_white',
        height=500,
        xaxis_title='日期',
        yaxis_title='累计收益 (%)'
    )
    
    fig.write_image(f"{OUTPUT_DIR}/logic_comparison.png", scale=2)
    
    print("\n" + "="*60)
    print("📈 结论")
    print("="*60)
    print(f"旧逻辑 IC: {old_result['ic_wrong']:.4f}")
    print(f"新逻辑 IC: {new_result['ic_correct']:.4f}")
    print(f"\n差异: {old_result['ic_wrong'] - new_result['ic_correct']:.4f}")
    print("="*60)


if __name__ == '__main__':
    main()
