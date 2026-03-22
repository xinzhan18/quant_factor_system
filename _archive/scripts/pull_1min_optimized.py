#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
优化的1分钟数据拉取脚本

功能:
1. 高效检测缺失的日期
2. 批量拉取缺失数据
3. 每天自动运行

使用:
    # 检测缺失
    python scripts/pull_1min_optimized.py --check
    
    # 拉取2017年
    python scripts/pull_1min_optimized.py --year 2017
    
    # 自动拉取缺失年份 (cronjob使用)
    python scripts/pull_1min_optimized.py
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 加载环境变量
if 'RQDATAC_CONF' not in os.environ:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / '.env')

from data.ricequant_source import RiceQuantSource
from data.storage.timescale_storage import TimescaleDB

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TABLE_1MIN = 'price_1min'
DAILY_QUOTA = 12_000_000


def get_existing_dates(db):
    """获取数据库中已存在的日期"""
    query = f"""
        SELECT DISTINCT time::date as d
        FROM {TABLE_1MIN}
        ORDER BY d
    """
    
    with db.connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        dates = [r[0] for r in cursor.fetchall()]
    
    return set(dates)


def get_trading_dates(year):
    """获取一年的所有交易日"""
    dates = pd.date_range(f'{year}-01-01', f'{year}-12-31', freq='B')
    return set(dates.date)


def check_missing_years(db, start_year=2015, end_year=None):
    """检查缺失的年份"""
    end_year = end_year or datetime.now().year
    
    existing_dates = get_existing_dates(db)
    
    missing_years = []
    for year in range(start_year, end_year + 1):
        year_dates = get_trading_dates(year)
        existing_in_year = year_dates & existing_dates
        
        if len(existing_in_year) == 0:
            missing_years.append(year)
        elif len(existing_in_year) < len(year_dates) * 0.5:
            # 不足50%算缺失
            missing_years.append(year)
    
    return missing_years


def pull_year_data(year, db, rq, quota_remaining):
    """拉取一年的数据"""
    logger.info(f"\n{'='*50}")
    logger.info(f"处理年份: {year}")
    logger.info(f"{'='*50}")
    
    # 获取已有的日期
    existing_dates = get_existing_dates(db)
    target_dates = get_trading_dates(year)
    missing_dates = target_dates - existing_dates
    
    if not missing_dates:
        logger.info(f"{year}年数据已完整")
        return quota_remaining
    
    logger.info(f"{year}年缺失 {len(missing_dates)} / {len(target_dates)} 个交易日")
    
    # 获取股票列表 (只获取一次)
    logger.info("获取股票列表...")
    try:
        stocks = rq.get_all_stocks(f'{year}0101')
        if stocks is None or stocks.empty:
            logger.error("无法获取股票列表")
            return quota_remaining
        
        # 转换symbol格式
        symbols = []
        for _, row in stocks.iterrows():
            oid = row['order_book_id']
            if oid.endswith('.SH'):
                symbol = f"SH{oid.split('.')[0]}"
            elif oid.endswith('.XSHE'):
                symbol = f"SZ{oid.split('.')[0]}"
            else:
                symbol = oid
            symbols.append(symbol)
        
        logger.info(f"股票数: {len(symbols)}")
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        return quota_remaining
    
    # 按日期拉取
    sorted_dates = sorted(missing_dates)
    
    for i, date in enumerate(sorted_dates):
        if quota_remaining <= 0:
            logger.warning("配额用尽，停止拉取")
            break
        
        date_str = date.strftime('%Y%m%d')
        date_display = date.strftime('%Y-%m-%d')
        
        logger.info(f"[{i+1}/{len(sorted_dates)}] {date_display}...")
        
        # 分批拉取
        batch_size = 500
        for j in range(0, len(symbols), batch_size):
            batch = symbols[j:j+batch_size]
            
            try:
                data = rq.get_minute_data(
                    symbols=batch,
                    start_date=date_str,
                    end_date=date_str,
                    frequency='1min'
                )
                
                if data is not None and not data.empty:
                    data = data.reset_index()
                    
                    # 标准化
                    if 'order_book_id' in data.columns:
                        data['symbol'] = data['order_book_id'].apply(
                            lambda x: f"SH{x.split('.')[0]}" if x.endswith('.SH') 
                            else f"SZ{x.split('.')[0]}" if x.endswith('.XSHE') 
                            else x
                        )
                    
                    if 'date' in data.columns:
                        data['time'] = pd.to_datetime(data['date'])
                    elif 'datetime' in data.columns:
                        data['time'] = pd.to_datetime(data['datetime'])
                    
                    # 只插入有time和symbol的记录
                    if 'time' in data.columns and 'symbol' in data.columns:
                        try:
                            inserted = db.insert_price(data, table=TABLE_1MIN)
                            quota_remaining -= inserted
                        except Exception as e:
                            logger.error(f"插入失败: {e}")
            
            except Exception as e:
                logger.error(f"拉取失败: {e}")
            
            time.sleep(0.5)  # 请求间隔
    
    return quota_remaining


def main():
    parser = argparse.ArgumentParser(description='优化的1分钟数据拉取')
    parser.add_argument('--check', action='store_true', help='仅检测')
    parser.add_argument('--year', type=int, help='拉取年份')
    args = parser.parse_args()
    
    # 初始化
    logger.info("初始化...")
    db = TimescaleDB()
    rq = RiceQuantSource()
    
    if args.check:
        # 仅检测
        missing = check_missing_years(db)
        logger.info(f"缺失年份: {missing}")
        return
    
    if args.year:
        # 拉取特定年份
        quota = DAILY_QUOTA
        quota = pull_year_data(args.year, db, rq, quota)
        logger.info(f"剩余配额: {quota}")
        return
    
    # 自动模式: 检查并拉取缺失年份
    missing = check_missing_years(db)
    
    if not missing:
        logger.info("✅ 所有年份数据完整")
        return
    
    logger.info(f"将拉取缺失年份: {missing}")
    
    quota = DAILY_QUOTA
    for year in missing:
        if quota <= 0:
            logger.warning("配额用尽")
            break
        quota = pull_year_data(year, db, rq, quota)


if __name__ == '__main__':
    main()
