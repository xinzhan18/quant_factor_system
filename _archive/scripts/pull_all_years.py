#!/usr/bin/env python
"""
拉取2015-2025年全市场日线数据
"""

import os

# 设置米筐配置
os.environ['RQDATAC_CONF'] = 'tcp://license:HZ9KQ7fUrGDbo_F2vppomXjs3-VpXzGY5anDDKDL5Te49kbTtDLmsTneaTvNNkDMMnQ9uUVeTHWkfwSMPaTt8CVZGZkaywfraeEUVOMXz1W6bGnuXoOTJ1qHVm5sfOGzMG-3drD1uYKCGNWfAAyIJbF0lnfJlzl9l0YElhWdUUk=DG_OVcg3wFeBRyuAjywrddEqJomlNjGY3EmKFLp-2KYeKg6hY7qwf4jxFxy_36gZSsvaAhhClwjLCZEJCW3RRGGFLoID28nZq4xkVjBF7p0-u-GyOqcnuxnio7eWJ5HklkwpInBUIY2x7sgIVvf-jgw3OlUZMKcv5KBilmi0DKE=@rqdatad-pro.ricequant.com:16011'

from quant_factor_system.data import RiceQuantSource, TimescaleDB
import psycopg2

print('='*70, flush=True)
print('拉取 2015-2025 全市场日线数据（每年独立拉取）', flush=True)
print('='*70, flush=True)

# 初始化
source = RiceQuantSource()
db = TimescaleDB()

# 检查当前数据量
conn = psycopg2.connect(host='localhost', port=5432, database='quant_data', user='postgres', password='quant123')
cur = conn.cursor()
cur.execute('SELECT COUNT(*) FROM price_daily')
existing = cur.fetchone()[0]
print(f'当前已有数据: {existing:,} 条\n', flush=True)
cur.close()
conn.close()

# 年份列表
years = list(range(2015, 2026))
total_records = 0

for year in years:
    start = f'{year}0101'
    end = f'{year}1231'
    
    print(f'📅 拉取 {year} 年数据...', flush=True)
    
    # 获取当年股票列表
    stocks = source.get_all_stocks(date=f'{year}1231')
    symbols = stocks['order_book_id'].tolist()
    print(f'   股票数: {len(symbols)}', flush=True)
    
    # 分批拉取
    batch_size = 100
    year_records = 0
    total_batches = (len(symbols) + batch_size - 1) // batch_size
    
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i:i+batch_size]
        data = source.get_daily_data(symbols=batch, start_date=start, end_date=end)
        
        if not data.empty:
            db.insert_price(data, table='price_daily')
            year_records += len(data)
        
        print(f'   [{year}] 批次 {i//batch_size + 1}/{total_batches}: +{len(data)}', flush=True)
    
    print(f'   ✅ {year}年完成: {year_records:,} 条\n', flush=True)
    total_records += year_records

print('='*70, flush=True)
print(f'🎉 全部完成! 新增 {total_records:,} 条记录', flush=True)
print('='*70, flush=True)
