#!/usr/bin/env python
"""
重新计算所有因子数据
- 训练集: 2015-01-01 ~ 2021-12-31
- 测试集: 2022-01-01 ~ 2024-12-31
"""

import os
import sys

# 设置环境变量
os.environ['RQDATAC_CONF'] = 'eyJ1c2VyX2lkIjoiNDc1NjA5NzMiLCJzZWNyZXkiOiJ6WFBMcVN6S3dGaDZQZFRDbjV3PT0iLCJyb2xlIjoicmVhZG9ubHkiLCJ1c2VybmFtZSI6InhpbnpoYW5AMTYzLmNvbSJ9'

sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace')

from quant_factor_system.data import TimescaleDB
from quant_factor_system.factors.basic.return_factors import (
    Return1dFactor, Return5dFactor, Return20dFactor, Return60dFactor,
    DistMA10Factor, DistMA20Factor, DistMA60Factor
)
from quant_factor_system.factors.basic.factors import MomentumFactor, VolatilityFactor


def compute_all_factors():
    """计算所有因子"""
    
    db = TimescaleDB()
    
    # 定义所有因子
    factors = [
        ('return_1d', Return1dFactor, {}),
        ('return_5d', Return5dFactor, {}),
        ('return_20d', Return20dFactor, {}),
        ('return_60d', Return60dFactor, {}),
        ('momentum_20', MomentumFactor, {'period': 20}),
        ('momentum_60', MomentumFactor, {'period': 60}),
        ('dist_ma10', DistMA10Factor, {}),
        ('dist_ma20', DistMA20Factor, {}),
        ('dist_ma60', DistMA60Factor, {}),
        ('volatility_20', VolatilityFactor, {'period': 20}),
    ]
    
    # 时间划分
    train_start = '2015-01-01'
    train_end = '2021-12-31'
    test_start = '2022-01-01'
    test_end = '2024-12-31'
    
    print("=" * 70)
    print("因子计算任务")
    print("=" * 70)
    print(f"训练集: {train_start} ~ {train_end}")
    print(f"测试集: {test_start} ~ {test_end}")
    print("=" * 70)
    
    # 获取股票列表
    with db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT symbol 
            FROM price_daily 
            WHERE time >= %s AND time <= %s
            ORDER BY symbol
        """, (train_start, train_end))
        symbols = [s[0] for s in cursor.fetchall()]
    
    print(f"\n股票数量: {len(symbols):,}")
    
    # 计算每个因子
    for name, factor_class, params in factors:
        table_name = f"factor_{name}"
        
        print(f"\n{'=' * 70}")
        print(f"计算因子: {name}")
        print(f"表名: {table_name}")
        print("=" * 70)
        
        # 删除旧表
        try:
            with db.connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
                conn.commit()
                print(f"已删除旧表: {table_name}")
        except Exception as e:
            print(f"删除表失败: {e}")
        
        # 创建新表
        db.create_factor_table(name)
        
        # 分批计算
        batch_size = 100
        total_train = 0
        total_test = 0
        
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i+batch_size]
            
            # 计算训练集
            data_train = db.query_daily(
                symbols=batch_symbols,
                start_date=train_start,
                end_date=train_end
            )
            
            if not data_train.empty:
                factor = factor_class(**params)
                factor.calculate(data_train)
                factor_values = factor.values
                
                if factor_values is not None and not factor_values.empty:
                    # 因子值在 'close' 列中 (这是因子值的列名)
                    df_train = factor_values.reset_index()
                    df_train = df_train.rename(columns={'close': 'value'})
                    df_train = df_train[['time', 'symbol', 'value']].dropna()
                    
                    if not df_train.empty:
                        db.insert_factor(df_train, name)
                        total_train += len(df_train)
            
            # 计算测试集
            data_test = db.query_daily(
                symbols=batch_symbols,
                start_date=test_start,
                end_date=test_end
            )
            
            if not data_test.empty:
                factor = factor_class(**params)
                factor.calculate(data_test)
                factor_values = factor.values
                
                if factor_values is not None and not factor_values.empty:
                    df_test = factor_values.reset_index()
                    df_test = df_test.rename(columns={'close': 'value'})
                    df_test = df_test[['time', 'symbol', 'value']].dropna()
                    
                    if not df_test.empty:
                        db.insert_factor(df_test, name)
                        total_test += len(df_test)
            
            progress = min(i + batch_size, len(symbols)) / len(symbols) * 100
            print(f"\r  进度: {progress:.1f}% | 训练集: {total_train:,} | 测试集: {total_test:,}", end='', flush=True)
        
        print(f"\n  完成: 训练集 {total_train:,} | 测试集 {total_test:,}")
    
    print("\n" + "=" * 70)
    print("所有因子计算完成!")
    print("=" * 70)


if __name__ == "__main__":
    compute_all_factors()
