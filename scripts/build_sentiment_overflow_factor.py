#!/usr/bin/env python3
"""
情绪溢出因子 - 完整版
"""

import sys
sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace')

import pandas as pd
import numpy as np
import psycopg2
from scipy import stats
import warnings
warnings.filterwarnings('ignore')

N_NEIGHBORS = 10
T_DAYS = 10  # 5-20天

OUTPUT_DIR = '/Users/xinzhan/.openclaw/workspace/quant_factor_system/output'


def get_data():
    """获取数据"""
    print("📊 获取数据 (2023-2024)...")
    
    conn = psycopg2.connect(
        host='localhost', port=5432, database='quant_data',
        user='postgres', password='quant123'
    )
    cursor = conn.cursor()
    
    # 使用log换手率
    cursor.execute("""
        SELECT symbol, time, 
               LN(NULLIF(volume::float, 0)) as log_turnover
        FROM price_daily
        WHERE time >= '2023-01-01' AND time <= '2024-12-31'
        AND volume IS NOT NULL AND volume > 0
        ORDER BY symbol, time
    """)
    
    data = cursor.fetchall()
    df = pd.DataFrame(data, columns=['symbol', 'time', 'log_turnover'])
    df['time'] = pd.to_datetime(df['time'])
    
    print(f"   获取 {len(data):,} 条")
    print(f"   股票数: {df['symbol'].nunique():,}")
    
    conn.close()
    return df


def compute_factor(df: pd.DataFrame, n: int = N_NEIGHBORS, T: int = T_DAYS):
    """计算因子"""
    print(f"📊 计算因子 (n={n}, T={T})...")
    
    # 股票排序
    symbols = sorted(df['symbol'].unique())
    symbol_to_idx = {s: i for i, s in enumerate(symbols)}
    idx_to_symbol = {i: s for i, s in enumerate(symbols)}
    
    # 计算T日均值
    print("   计算换手率均值...")
    df = df.sort_values(['symbol', 'time'])
    df['turnover_ma'] = df.groupby('symbol')['log_turnover'].transform(
        lambda x: x.rolling(T, min_periods=1).mean()
    )
    
    # 按时间分组计算
    print("   计算邻居因子...")
    results = []
    
    dates = sorted(df['time'].unique())
    total_dates = len(dates)
    
    for i, date in enumerate(dates):
        if i % 100 == 0:
            print(f"   进度: {i}/{total_dates}")
        
        day_df = df[df['time'] == date].copy()
        
        if len(day_df) < 100:
            continue
        
        for symbol in symbols:
            idx = symbol_to_idx.get(symbol)
            if idx is None:
                continue
            
            # 邻居
            start = max(0, idx - n)
            end = min(len(symbols), idx + n + 1)
            neighbor_indices = [j for j in range(start, end) if j != idx]
            neighbor_symbols = [idx_to_symbol[j] for j in neighbor_indices if j in idx_to_symbol]
            
            # 自身
            own_vals = day_df[day_df['symbol'] == symbol]['turnover_ma']
            if len(own_vals) == 0:
                continue
            own = own_vals.values[0]
            
            # 邻居均值
            nbr_vals = day_df[day_df['symbol'].isin(neighbor_symbols)]['turnover_ma']
            if len(nbr_vals) == 0:
                continue
            nbr = nbr_vals.mean()
            
            if not np.isnan(own) and not np.isnan(nbr):
                results.append({
                    'symbol': symbol,
                    'time': date,
                    'own': own,
                    'nbr': nbr
                })
    
    if not results:
        return pd.DataFrame()
    
    result_df = pd.DataFrame(results)
    print(f"   初步结果: {len(result_df):,} 条")
    
    # 截面回归
    print("   截面回归...")
    
    factors = []
    for date in result_df['time'].unique():
        day_data = result_df[result_df['time'] == date].dropna()
        
        if len(day_data) < 100:
            continue
        
        x = day_data['own'].values
        y = day_data['nbr'].values
        
        try:
            slope, intercept, _, _, _ = stats.linregress(x, y)
            residuals = y - (slope * x + intercept)
            day_data = day_data.copy()
            day_data['factor'] = residuals
            factors.append(day_data[['symbol', 'time', 'factor']])
        except:
            continue
    
    if factors:
        factor_df = pd.concat(factors, ignore_index=True)
    else:
        factor_df = pd.DataFrame()
    
    print(f"   最终: {len(factor_df):,} 条")
    return factor_df


def main():
    print("="*60)
    print("🎯 情绪溢出因子")
    print("="*60)
    
    df = get_data()
    factor_df = compute_factor(df)
    
    if len(factor_df) > 0:
        # 保存
        output_path = f"{OUTPUT_DIR}/sentiment_overflow_factor.csv"
        factor_df.to_csv(output_path, index=False)
        print(f"\n✅ 保存到: {output_path}")
        
        # 统计
        print(f"\n因子统计:")
        print(f"   均值: {factor_df['factor'].mean():.6f}")
        print(f"   标准差: {factor_df['factor'].std():.6f}")
    else:
        print("\n❌ 未能生成因子数据")


if __name__ == '__main__':
    main()
