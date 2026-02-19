#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
从米筐获取数据并保存到 TimescaleDB
RiceQuant to TimescaleDB Pipeline Example

使用流程:
1. 启动 TimescaleDB (Docker)
2. 初始化数据库
3. 从米筐获取数据
4. 保存到 TimescaleDB
5. 计算因子
6. 选股
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os
import logging
import importlib.util

sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace/quant_factor_system')

# 直接导入模块
spec = importlib.util.spec_from_file_location('timescale', 'data/timescale_storage.py')
ts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ts_module)

TimescaleDB = ts_module.TimescaleDB
QuantDataManager = ts_module.QuantDataManager
TIMESCALE_CONFIG = ts_module.TIMESCALE_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_mock_data():
    """创建模拟数据"""
    dates = pd.date_range(start='2024-01-02', end='2024-01-31', freq='B')
    symbols = ['SH600000', 'SH600001', 'SH600002', 'SH600003']
    
    data = []
    for symbol in symbols:
        base_price = np.random.uniform(10, 50)
        for date in dates:
            change = np.random.uniform(-0.02, 0.025)
            close = base_price * (1 + change)
            base_price = close
            
            data.append({
                'time': date,
                'symbol': symbol,
                'open': close * (1 + np.random.uniform(-0.01, 0.01)),
                'high': close * (1 + np.random.uniform(0, 0.02)),
                'low': close * (1 - np.random.uniform(0, 0.02)),
                'close': close,
                'volume': np.random.uniform(1000000, 10000000)
            })
    
    return pd.DataFrame(data)


def calculate_ret20(price_df):
    """计算20日收益率因子"""
    
    if isinstance(price_df.index, pd.MultiIndex):
        price_df = price_df.reset_index()
        price_df['time'] = pd.to_datetime(price_df['time'])
        price_df = price_df.set_index(['symbol', 'time'])
    
    factor_data = []
    
    for symbol in price_df.index.get_level_values('symbol').unique():
        stock_data = price_df.loc[symbol].sort_index()
        
        lookback = min(20, len(stock_data))
        
        for i in range(lookback - 1, len(stock_data)):
            current_close = stock_data['close'].iloc[i]
            past_close = stock_data['close'].iloc[i - lookback + 1]
            ret = (current_close - past_close) / past_close
            
            time = stock_data.index[i]
            
            factor_data.append({
                'symbol': symbol,
                'time': time,
                'factor_name': 'ret20',
                'value': ret
            })
    
    return pd.DataFrame(factor_data)


def main():
    print("\n" + "🚀" * 15)
    print("米筐 → TimescaleDB → 选股 完整流程")
    print("🚀" * 15 + "\n")
    
    # ========== 步骤1: 连接数据库 ==========
    print("步骤1: 连接 TimescaleDB")
    print("-" * 40)
    
    db = TimescaleDB(TIMESCALE_CONFIG)
    
    if db._conn is None:
        print("❌ TimescaleDB 未运行!")
        print("\n请先启动:")
        print("  docker run -d --name timescaledb \\")
        print("    -p 5432:5432 \\")
        print("    -e POSTGRES_PASSWORD=quant123 \\")
        print("    timescale/timescaledb:latest-pg14")
        return
    
    print(f"✅ 连接成功: {TIMESCALE_CONFIG['database']}")
    
    # ========== 步骤2: 创建表 ==========
    print("\n\n步骤2: 创建数据库表")
    print("-" * 40)
    
    db.create_all_tables()
    print("✅ 表创建完成")
    print("  • price_daily (日线)")
    print("  • price_1min (1分钟)")
    print("  • price_5min (5分钟)")
    
    # ========== 步骤3: 获取/生成数据 ==========
    print("\n\n步骤3: 获取数据 (模拟)")
    print("-" * 40)
    print("说明: 使用 rqdatac SDK 获取真实数据")
    print("      如果未安装，使用模拟数据")
    
    daily_data = create_mock_data()
    print(f"生成: {len(daily_data)} 条日线数据")
    print(daily_data.head())
    
    # ========== 步骤4: 保存数据 ==========
    print("\n\n步骤4: 保存到 TimescaleDB")
    print("-" * 40)
    
    count = db.insert_price(daily_data, table='price_daily')
    print(f"✅ 保存: {count} 条")
    
    # ========== 步骤5: 计算因子 ==========
    print("\n\n步骤5: 计算因子 (ret20)")
    print("-" * 40)
    
    price_df = db.query_daily(
        symbols=['SH600000', 'SH600001', 'SH600002', 'SH600003'],
        start_date='2024-01-02',
        end_date='2024-01-31'
    )
    print(f"读取: {len(price_df)} 条价格数据")
    
    factor_df = calculate_ret20(price_df)
    print(f"计算: {len(factor_df)} 条因子数据")
    
    # ========== 步骤6: 保存因子 ==========
    print("\n\n步骤6: 保存因子 (APPEND ONLY)")
    print("-" * 40)
    
    db.create_factor_table('ret20')
    db.insert_factor(factor_df, 'ret20', value_col='value')
    print("✅ 因子保存完成")
    
    # ========== 步骤7: 选股 ==========
    print("\n\n步骤7: 选股")
    print("-" * 40)
    
    # 读取最新因子
    factor_result = db.query_factor(
        name='ret20',
        start_date='2024-01-01',
        end_date='2024-01-31'
    )
    
    if not factor_result.empty:
        latest_date = factor_result.index[-1]
        print(f"最新日期: {latest_date}")
        
        top3 = factor_result.loc[latest_date].sort_values(ascending=False).head(3)
        
        print(f"\n🎯 Top 3 股票 (ret20 因子):")
        for symbol, value in top3.items():
            print(f"   {symbol}: {value:.4f}")
    
    # ========== 统计 ==========
    print("\n" + "=" * 40)
    print("统计")
    print("=" * 40)
    
    stats = db.get_stats()
    print(f"数据库: {TIMESCALE_CONFIG['database']}")
    print(f"表大小: {stats}")
    
    print("\n" + "=" * 40)
    print("✅ 完整流程完成!")
    print("=" * 40)


if __name__ == "__main__":
    main()
