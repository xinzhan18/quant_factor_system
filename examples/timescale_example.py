#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TimescaleDB 量化数据存储示例
Quant Data Storage with TimescaleDB

使用流程:
1. 启动 TimescaleDB (Docker)
2. 初始化数据库
3. 更新数据
4. 查询数据

安装 TimescaleDB:
    docker run -d --name timescaledb \
      -p 5432:5432 \
      -e POSTGRES_PASSWORD=quant123 \
      timescale/timescaledb:latest-pg14
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import importlib.util

sys.path.insert(0, '/Users/xinzhan/.openclaw/workspace/quant_factor_system')

# 直接导入模块
spec = importlib.util.spec_from_file_location('timescale', 'data/timescale_storage.py')
ts_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ts_module)

TimescaleDB = ts_module.TimescaleDB
QuantDataManager = ts_module.QuantDataManager
TIMESCALE_CONFIG = ts_module.TIMESCALE_CONFIG


def create_mock_data():
    """创建模拟数据"""
    symbols = ['SH600000', 'SH600001', 'SH600002', 'SH600003', 'SH600004']
    
    # 日线数据
    dates = pd.date_range(start='2024-01-01', end='2024-01-31', freq='B')
    daily_data = []
    
    for symbol in symbols:
        base_price = np.random.uniform(10, 50)
        for date in dates:
            change = np.random.uniform(-0.02, 0.025)
            close = base_price * (1 + change)
            base_price = close
            
            daily_data.append({
                'time': date,
                'symbol': symbol,
                'open': close * (1 + np.random.uniform(-0.01, 0.01)),
                'high': close * (1 + np.random.uniform(0, 0.02)),
                'low': close * (1 - np.random.uniform(0, 0.02)),
                'close': close,
                'volume': np.random.uniform(1000000, 10000000)
            })
    
    return pd.DataFrame(daily_data)


def create_minute_data():
    """创建1分钟模拟数据"""
    symbols = ['SH600000', 'SH600001']
    
    # 一天: 09:30 - 15:00 = 330分钟
    base_date = datetime(2024, 1, 2)
    times = [base_date + timedelta(minutes=i) for i in range(330)]
    
    minute_data = []
    
    for symbol in symbols:
        base_price = np.random.uniform(10, 50)
        for t in times:
            change = np.random.uniform(-0.001, 0.0015)
            close = base_price * (1 + change)
            base_price = close
            
            minute_data.append({
                'time': t,
                'symbol': symbol,
                'open': close * (1 + np.random.uniform(-0.001, 0.001)),
                'high': close * (1 + np.random.uniform(0, 0.002)),
                'low': close * (1 - np.random.uniform(0, 0.002)),
                'close': close,
                'volume': np.random.uniform(10000, 100000)
            })
    
    return pd.DataFrame(minute_data)


def main():
    print("=" * 70)
    print("TimescaleDB 量化数据存储示例")
    print("=" * 70)
    
    # ========== 步骤1: 连接数据库 ==========
    print("\n📦 步骤1: 连接 TimescaleDB")
    print("-" * 50)
    
    # 检查是否可用
    db = TimescaleDB(TIMESCALE_CONFIG)
    
    if db._conn is None:
        print("❌ TimescaleDB 未运行!")
        print("\n请先启动 TimescaleDB:")
        print("  docker run -d --name timescaledb \\")
        print("    -p 5432:5432 \\")
        print("    -e POSTGRES_PASSWORD=quant123 \\")
        print("    timescale/timescaledb:latest-pg14")
        
        # 创建模拟数据用于演示
        print("\n\n创建模拟数据用于演示...")
        daily_df = create_mock_data()
        minute_df = create_minute_data()
        
        print("\n📊 模拟日线数据:")
        print(f"  {len(daily_df)} 条")
        print(daily_df.head())
        
        print("\n📊 模拟分钟数据:")
        print(f"  {len(minute_df)} 条")
        print(minute_df.head())
        
        print("\n\n✅ 连接到 TimescaleDB 后，运行以下代码:")
        print("""
from quant_factor_system.data import QuantDataManager

manager = QuantDataManager()
manager.initialize()

# 更新日线数据
manager.update_daily(symbols=['SH600000', 'SH600001'])

# 查询
df = manager.get_price(
    symbols=['SH600000'],
    start_date='2024-01-01',
    end_date='2024-01-31',
    frequency='daily'
)
print(df)
""")
        return
    
    print(f"✅ 连接成功: {TIMESCALE_CONFIG['database']}")
    
    # ========== 步骤2: 创建表 ==========
    print("\n\n📋 步骤2: 创建超表 (Hypertable)")
    print("-" * 50)
    
    print("创建以下表:")
    print("  • price_1min   - 1分钟数据 (按周分区, 7天后压缩)")
    print("  • price_5min   - 5分钟数据 (按月分区, 1月后压缩)")
    print("  • price_daily  - 日线数据 (按年分区, 1年后压缩)")
    
    db.create_all_tables()
    print("\n✅ 所有表创建完成")
    
    # ========== 步骤3: 插入数据 ==========
    print("\n\n💾 步骤3: 插入数据")
    print("-" * 50)
    
    # 日线数据
    print("生成日线数据...")
    daily_df = create_mock_data()
    print(f"  日线: {len(daily_df)} 条")
    
    # 分钟数据
    print("生成1分钟数据...")
    minute_df = create_minute_data()
    print(f"  1分钟: {len(minute_df)} 条")
    
    db.insert_price(daily_df, table='price_daily')
    db.insert_price(minute_df, table='price_1min')
    print("\n✅ 数据插入完成")
    
    # ========== 步骤4: 查询数据 ==========
    print("\n\n🔍 步骤4: 查询数据")
    print("-" * 50)
    
    # 查询日线
    print("查询日线数据...")
    df = db.query_daily(
        symbols=['SH600000'],
        start_date='2024-01-02',
        end_date='2024-01-31',
        table='price_daily'
    )
    print(f"  结果: {len(df)} 条")
    print(df.head())
    
    # 查询分钟
    print("\n查询1分钟数据...")
    minute_result = db.query_price(
        symbols=['SH600000'],
        start_time='2024-01-02 09:30:00',
        end_time='2024-01-02 10:00:00',
        table='price_1min'
    )
    print(f"  结果: {len(minute_result)} 条")
    print(minute_result.head())
    
    # ========== 步骤5: 数据库统计 ==========
    print("\n\n📊 步骤5: 数据库统计")
    print("-" * 50)
    
    stats = db.get_stats()
    print(f"数据库状态: {stats}")
    
    # ========== 完整更新流程 ==========
    print("\n\n🔄 完整更新流程")
    print("-" * 50)
    print("""
# 创建管理器
manager = QuantDataManager()

# 初始化数据库 (创建表)
manager.initialize()

# 更新日线数据
manager.update_daily(
    symbols=['SH600000', 'SH600001'],
    start_date='20240101',
    end_date='20240131'
)

# 更新分钟数据
manager.update_minute(
    symbols=['SH600000'],
    start_date='20240101',
    end_date='20240131',
    frequency='1min'
)

# 查询
df = manager.get_price(
    symbols=['SH600000'],
    start_date='2024-01-01',
    end_date='2024-01-31',
    frequency='daily'
)
""")
    
    # ========== 总结 ==========
    print("\n" + "=" * 70)
    print("✅ TimescaleDB 架构总结")
    print("=" * 70)
    
    print("""
┌────────────────────────────────────────────────────────────────────┐
│                      TimescaleDB 存储架构                            │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  热数据 (0-7天) - SSD                                       │   │
│  │  • price_1min: 原始1分钟数据                                │   │
│  │  • 未压缩: 快速读取                                         │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  温数据 (7天-1年) - HDD                                    │   │
│  │  • price_1min, price_5min: 自动压缩                        │   │
│  │  • 压缩率: 10x-20x                                         │   │
│  │  • 查询时自动解压缩                                         │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │  冷数据 (1年以上) - HDD/云存储                              │   │
│  │  • price_daily: 日线数据                                   │   │
│  │  • 深度压缩                                               │   │
│  └────────────────────────────────────────────────────────────┘   │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘

启动 TimescaleDB:
    docker run -d --name timescaledb \\
      -p 5432:5432 \\
      -e POSTGRES_PASSWORD=quant123 \\
      timescale/timescaledb:latest-pg14
""")


if __name__ == "__main__":
    main()
