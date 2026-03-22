#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速检查1分钟数据完整性
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

def quick_check():
    db = get_timescaledb()
    
    print("=" * 60)
    print("1分钟数据快速检查")
    print("=" * 60)
    
    with db.connection() as conn:
        cursor = conn.cursor()
        
        # 1. 总览
        cursor.execute("SELECT COUNT(*), MIN(time), MAX(time) FROM price_1min")
        total, min_date, max_date = cursor.fetchone()
        print(f"\n总记录: {total:,}")
        print(f"日期范围: {min_date} ~ {max_date}")
        
        # 2. 按年统计
        print("\n按年统计:")
        print("-" * 40)
        
        for year in range(2015, 2027):
            cursor.execute("""
                SELECT COUNT(DISTINCT time::date), COUNT(DISTINCT symbol)
                FROM price_1min
                WHERE time >= '%s-01-01' AND time < '%s-01-01'
            """ % (year, year+1))
            row = cursor.fetchone()
            if row[0]:
                print(f"{year}: {row[0]}天, {row[1]}只股票")
            else:
                # 试试用不同方式查
                cursor.execute("""
                    SELECT COUNT(DISTINCT time::date), COUNT(DISTINCT symbol)
                    FROM price_1min
                    WHERE EXTRACT(YEAR FROM time) = %s
                """, (year,))
                row = cursor.fetchone()
                if row[0]:
                    print(f"{year}: {row[0]}天, {row[1]}只股票")
                else:
                    print(f"{year}: 无数据")
        
        # 3. 检查最近几天每天的股票数
        print("\n最近几天详情:")
        print("-" * 40)
        
        cursor.execute("""
            SELECT time::date as d, COUNT(DISTINCT symbol) as stocks, COUNT(*) as records
            FROM price_1min
            GROUP BY d
            ORDER BY d
            DESC LIMIT 10
        """)
        
        for row in cursor.fetchall():
            d, stocks, records = row
            expected = stocks * 240
            pct = records / expected * 100 if expected > 0 else 0
            status = "✅" if pct >= 99 else ("⚡" if pct >= 95 else "❌")
            print(f"{d}: {stocks}只, {records:,}条 ({pct:.1f}%) {status}")

if __name__ == '__main__':
    quick_check()
