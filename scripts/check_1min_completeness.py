#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查1分钟数据完整性
"""

import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import os
if 'RQDATAC_CONF' not in os.environ:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / '.env')

from data.storage import get_timescaledb
from datetime import datetime, timedelta
import pandas as pd

def check_data_completeness():
    """检查数据完整性"""
    
    print("=" * 60)
    print("1分钟数据完整性检查")
    print("=" * 60)
    
    db = get_timescaledb()
    
    with db.connection() as conn:
        cursor = conn.cursor()
        
        # 1. 获取所有交易日
        cursor.execute("""
            SELECT DISTINCT time::date as trading_date
            FROM price_1min
            ORDER BY trading_date
        """)
        trading_dates = [r[0] for r in cursor.fetchall()]
        
        print(f"\n📅 总交易日数: {len(trading_dates)}")
        print(f"   日期范围: {trading_dates[0]} ~ {trading_dates[-1]}")
        
        # 2. 获取每天的股票数量和记录数
        print("\n📊 每天数据统计 (抽样):")
        print("-" * 60)
        print(f"{'日期':<12} {'股票数':<10} {'记录数':<15} {'备注'}")
        print("-" * 60)
        
        # 抽样检查: 每月取一天
        sample_dates = []
        current_month = None
        for d in trading_dates:
            month_key = (d.year, d.month)
            if month_key != current_month:
                sample_dates.append(d)
                current_month = month_key
        
        # 也检查最近几天
        sample_dates.extend(trading_dates[-5:])
        
        for date in sorted(set(sample_dates)):
            cursor.execute("""
                SELECT COUNT(DISTINCT symbol), COUNT(*)
                FROM price_1min
                WHERE time::date = %s
            """, (date,))
            stock_count, record_count = cursor.fetchone()
            
            # 计算应该有的记录数 (每天4小时 = 240分钟)
            expected = stock_count * 240
            completeness = record_count / expected * 100 if expected > 0 else 0
            
            remark = ""
            if completeness < 95:
                remark = "⚠️ 数据不足"
            elif completeness < 100:
                remark = "⚡ 部分缺失"
            
            print(f"{date}    {stock_count:<10} {record_count:<15,} {remark}")
        
        # 3. 检查每年完整度
        print("\n📈 年度数据完整度:")
        print("-" * 60)
        
        for year in range(2015, 2027):
            cursor.execute("""
                SELECT COUNT(DISTINCT time::date) as days,
                       COUNT(DISTINCT symbol) as stocks,
                       COUNT(*) as records
                FROM price_1min
                WHERE EXTRACT(YEAR FROM time) = %s
            """, (year,))
            row = cursor.fetchone()
            
            if row[0]:  # 如果有数据
                # 估算一年应该有的交易日 (~250天)
                expected_days = 250
                # 估算每天平均股票数
                avg_stocks = row[2] / row[0] if row[0] > 0 else 0
                expected_records = avg_stocks * 240 * min(row[0], expected_days)
                
                completeness = row[2] / expected_records * 100 if expected_records > 0 else 0
                
                print(f"{year}: {row[0]}天, {row[1]}只股票, {row[2]:,}条记录 (完整度: {completeness:.1f}%)")
            else:
                print(f"{year}: 无数据")
        
        # 4. 检查最近30天每天的股票数
        print("\n📉 最近30个交易日详情:")
        print("-" * 60)
        
        cursor.execute("""
            SELECT time::date as d, COUNT(DISTINCT symbol) as stocks, COUNT(*) as records
            FROM price_1min
            WHERE time::date >= %s
            GROUP BY d
            ORDER BY d
        """, (trading_dates[-30],))
        
        for row in cursor.fetchall():
            date, stocks, records = row
            expected = stocks * 240
            pct = records / expected * 100 if expected > 0 else 0
            status = "✅" if pct >= 99 else ("⚡" if pct >= 95 else "❌")
            print(f"{date}: {stocks}只, {records:,}条 ({pct:.1f}%) {status}")

if __name__ == '__main__':
    check_data_completeness()
