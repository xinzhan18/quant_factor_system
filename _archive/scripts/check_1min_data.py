#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
1分钟数据完整性检测脚本
检测数据库中1分钟数据的覆盖情况
"""

import os
import psycopg2
from datetime import datetime, timedelta
import pandas as pd

# 数据库连接 (从环境变量读取)
DB_CONFIG = {
    'host': os.environ.get('TIMESCALE_HOST', 'localhost'),
    'port': int(os.environ.get('TIMESCALE_PORT', 5432)),
    'database': os.environ.get('TIMESCALE_DB', 'quant_data'),
    'user': os.environ.get('TIMESCALE_USER', 'postgres'),
    'password': os.environ.get('TIMESCALE_PASSWORD', ''),
}

def get_trading_days(start_date, end_date):
    """生成交易日历（简化的，只排除周末）"""
    days = []
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # 0-4 是周一到周五
            days.append(current)
        current += timedelta(days=1)
    return days

def check_1min_data():
    """检测1分钟数据完整性"""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    # 获取数据库中已有的日期
    print("🔍 查询数据库中已有的1分钟数据...")
    cur.execute("""
        SELECT DISTINCT DATE(time) as trade_date
        FROM price_1min
        ORDER BY trade_date
    """)
    db_dates = set(row[0] for row in cur.fetchall())
    
    if not db_dates:
        print("❌ 数据库中没有1分钟数据！")
        conn.close()
        return
    
    print(f"📊 数据库中已有 {len(db_dates)} 天的1分钟数据")
    
    # 计算2015年至今的交易日
    start_date = datetime(2015, 1, 1).date()
    end_date = datetime.today().date()
    all_trading_days = set(get_trading_days(start_date, end_date))
    
    print(f"📅 2015-01-01 至今应有 {len(all_trading_days)} 个交易日")
    
    # 缺失的日期
    missing_dates = all_trading_days - db_dates
    
    print(f"\n✅ 已有数据: {len(db_dates)} 天")
    print(f"❌ 缺失数据: {len(missing_dates)} 天")
    print(f"📈 完整率: {len(db_dates) / len(all_trading_days) * 100:.2f}%")
    
    # 显示最近的数据
    print("\n📋 最近30天数据:")
    cur.execute("""
        SELECT 
            DATE(time) as trade_date,
            COUNT(*) as record_count,
            COUNT(DISTINCT symbol) as stock_count
        FROM price_1min
        GROUP BY DATE(time)
        ORDER BY trade_date DESC
        LIMIT 30
    """)
    
    print(f"{'日期':<12} {'记录数':>15} {'股票数':>10}")
    print("-" * 40)
    for row in cur.fetchall():
        print(f"{str(row[0]):<12} {row[1]:>15,} {row[2]:>10,}")
    
    # 统计总记录数
    cur.execute("SELECT SUM(chunks.row_count) FROM (SELECT COUNT(*) as row_count FROM price_1min GROUP BY DATE(time)) as chunks")
    total = cur.fetchone()[0]
    print(f"\n📊 总记录数: {total:,}")
    
    # 缺失的日期（最近的部分）
    sorted_missing = sorted(missing_dates)
    print(f"\n❌ 缺失数据 - 最近30天:")
    recent_missing = [d for d in sorted_missing if d >= datetime(2025, 1, 1).date()][-30:]
    for d in recent_missing:
        print(f"  {d}")
    
    conn.close()
    
    return {
        'db_dates': db_dates,
        'missing_dates': missing_dates,
        'total_days': len(all_trading_days),
        'has_days': len(db_dates)
    }

if __name__ == '__main__':
    check_1min_data()
