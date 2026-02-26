#!/usr/bin/env python3
"""
保存日内动量因子数据到数据库
"""

import sys
sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace')

import pandas as pd
import numpy as np
import psycopg2
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

BATCH_SIZE = 50000


def get_daily_data():
    """获取全量日线数据"""
    print("📊 获取全量日线数据...")
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='quant_data',
        user='postgres',
        password='quant123'
    )
    cursor = conn.cursor()
    
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


def compute_factor(price_df: pd.DataFrame) -> pd.DataFrame:
    """计算日内动量因子"""
    print("📊 计算因子...")
    
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
    factor_df = factor_df.dropna(subset=['value'])
    
    print(f"   因子数据: {len(factor_df):,} 条")
    
    return factor_df


def save_to_db(factor_df: pd.DataFrame, batch_size: int = BATCH_SIZE):
    """保存因子数据到数据库"""
    print("💾 保存因子数据到数据库...")
    
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='quant_data',
        user='postgres',
        password='quant123'
    )
    cursor = conn.cursor()
    
    total = len(factor_df)
    saved = 0
    
    for i in range(0, total, batch_size):
        batch = factor_df.iloc[i:i+batch_size]
        
        # 使用 upsert
        for _, row in batch.iterrows():
            cursor.execute('''
                INSERT INTO factor_intraday_momentum (symbol, time, value)
                VALUES (%s, %s, %s)
                ON CONFLICT (symbol, time) DO UPDATE SET value = EXCLUDED.value
            ''', (row['symbol'], row['time'], row['value']))
        
        conn.commit()
        saved += len(batch)
        print(f"   已保存 {saved:,}/{total:,} ({saved*100//total}%)")
    
    # 验证
    cursor.execute('SELECT COUNT(*) FROM factor_intraday_momentum')
    count = cursor.fetchone()[0]
    print(f"   ✅ 数据库中共 {count:,} 条因子数据")
    
    conn.close()


def main():
    print("="*60)
    print("💾 保存日内动量因子到数据库")
    print("="*60)
    
    # 1. 获取数据
    price_df = get_daily_data()
    
    # 2. 计算因子
    factor_df = compute_factor(price_df)
    
    # 3. 保存到数据库
    save_to_db(factor_df)
    
    print("\n" + "="*60)
    print("✅ 完成！因子已保存到数据库")
    print("="*60)


if __name__ == '__main__':
    main()
