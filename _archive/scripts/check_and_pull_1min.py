#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
1分钟数据完整性检测和自动拉取脚本

功能:
1. 检测缺失的年份/月份
2. 每天自动拉取缺失的历史数据
3. 优先拉取 older 数据

使用:
    # 检测缺失数据
    python scripts/check_and_pull_1min.py --check-only
    
    # 检测并拉取 (每天运行)
    python scripts/check_and_pull_1min.py
    
    # 拉取特定年份
    python scripts/check_and_pull_1min.py --year 2017
    
    # 强制拉取所有历史 (危险!)
    python scripts/check_and_pull_1min.py --force-all
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from typing import List, Set, Dict, Tuple

import pandas as pd

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 设置米筐配置
import os
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


# ==================== 配置 ====================

TABLE_1MIN = 'price_1min'
DAILY_QUOTA_LIMIT_ROWS = 12_000_000  # 1200万条/天


class DataCompletenessChecker:
    """数据完整性检测器"""
    
    def __init__(self):
        self.db = TimescaleDB()
        self.rq = RiceQuantSource()
        
    def get_existing_dates(self) -> Dict[int, Set[int]]:
        """
        获取数据库中已存在的年份和月份
        
        Returns:
            {year: {month, ...}, ...}
        """
        query = f"""
            SELECT DISTINCT 
                EXTRACT(YEAR FROM time)::int as year,
                EXTRACT(MONTH FROM time)::int as month
            FROM {TABLE_1MIN}
            ORDER BY year, month
        """
        
        with self.db.connection() as conn:
            df = pd.read_sql(query, conn)
        
        result = defaultdict(set)
        for _, row in df.iterrows():
            result[row['year']].add(int(row['month']))
        
        return dict(result)
    
    def get_missing_years(self) -> List[int]:
        """获取缺失的年份"""
        existing = self.get_existing_dates()
        
        all_years = set(range(2015, datetime.now().year + 1))
        existing_years = set(existing.keys())
        
        missing = sorted(all_years - existing_years)
        logger.info(f"缺失年份: {missing}")
        return missing
    
    def get_year_completeness(self) -> Dict[int, Dict]:
        """
        获取每年的数据完整度
        
        Returns:
            {year: {'months': {month: days}, 'stocks': count, 'records': count}}
        """
        existing = self.get_existing_dates()
        
        # 估算每年应该有的月份数 (12个月)
        # 每年约250个交易日
        
        result = {}
        
        for year in sorted(existing.keys()):
            query = f"""
                SELECT 
                    EXTRACT(MONTH FROM time)::int as month,
                    COUNT(DISTINCT time::date) as trading_days,
                    COUNT(DISTINCT symbol) as stocks,
                    COUNT(*) as records
                FROM {TABLE_1MIN}
                WHERE EXTRACT(YEAR FROM time) = {year}
                GROUP BY month
                ORDER BY month
            """
            
            with self.db.connection() as conn:
                df = pd.read_sql(query, conn)
            
            result[year] = {
                'months': set(df['month'].tolist()),
                'trading_days': df['trading_days'].sum(),
                'stocks': df['stocks'].max(),
                'records': df['records'].sum()
            }
        
        return result
    
    def check_date(self, date_str: str) -> Tuple[bool, int, int]:
        """
        检查特定日期的数据完整度
        
        Args:
            date_str: 日期 (YYYY-MM-DD)
            
        Returns:
            (是否有数据, 股票数, 记录数)
        """
        query = f"""
            SELECT COUNT(DISTINCT symbol), COUNT(*)
            FROM {TABLE_1MIN}
            WHERE time >= '{date_str} 00:00:00'
            AND time < '{date_str} 23:59:59'
        """
        
        with self.db.connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            row = cursor.fetchone()
        
        return row[0] > 0, row[0], row[1]
    
    def generate_report(self) -> str:
        """生成完整性报告"""
        existing = self.get_existing_dates()
        
        report = []
        report.append("=" * 60)
        report.append("1分钟数据完整性报告")
        report.append("=" * 60)
        
        # 每年统计
        report.append("\n按年份统计:")
        report.append("-" * 40)
        
        for year in range(2015, datetime.now().year + 1):
            if year in existing:
                months = sorted(existing[year])
                report.append(f"{year}: ✅ {len(months)}个月 ({months})")
            else:
                report.append(f"{year}: ❌ 无数据")
        
        # 缺失年份
        missing = self.get_missing_years()
        if missing:
            report.append(f"\n⚠️ 缺失年份: {missing}")
        
        return "\n".join(report)


class IncrementalPuller:
    """增量拉取器"""
    
    def __init__(self):
        self.db = TimescaleDB()
        self.rq = RiceQuantSource()
        self.quota_used = 0
        
    def pull_year(self, year: int, month: int = None):
        """
        拉取特定年份/月份的数据
        
        Args:
            year: 年份
            month: 月份 (None = 全年)
        """
        if month:
            dates = pd.date_range(f'{year}-{month:02d}-01', periods=1, freq='B')
        else:
            # 全年交易日
            dates = pd.date_range(f'{year}-01-01', f'{year}-12-31', freq='B')
        
        logger.info(f"将拉取 {year}年{'%02d' % month if month else ''} {len(dates)} 个交易日")
        
        for i, date in enumerate(dates):
            if self.quota_used >= DAILY_QUOTA_LIMIT_ROWS:
                logger.warning("⚠️ 配额已用尽，停止拉取")
                break
            
            date_str = date.strftime('%Y-%m-%d')
            date_int = date.strftime('%Y%m%d')
            
            # 检查是否已有数据
            checker = DataCompletenessChecker()
            has_data, stocks, records = checker.check_date(date_str)
            
            if has_data:
                logger.debug(f"{date_str}: 已存在 ({stocks}只, {records}条)")
                continue
            
            logger.info(f"[{i+1}/{len(dates)}] 拉取 {date_str}...")
            
            # 拉取数据
            try:
                self._pull_date(date_int)
            except Exception as e:
                logger.error(f"拉取 {date_str} 失败: {e}")
            
            time.sleep(0.5)  # 避免请求过快
    
    def _pull_date(self, date: str):
        """拉取单日数据"""
        from data.storage import TimescaleDB as TS
        
        db = TS()
        
        # 获取全市场股票
        stocks = self.rq.get_all_stocks(date)
        if stocks is None or stocks.empty:
            logger.warning(f"无法获取股票列表: {date}")
            return
        
        # 转换为 symbol 格式
        symbols = []
        for _, row in stocks.iterrows():
            order_book_id = row['order_book_id']
            if order_book_id.endswith('.SH'):
                symbol = f"SH{order_book_id.split('.')[0]}"
            elif order_book_id.endswith('.XSHE'):
                symbol = f"SZ{order_book_id.split('.')[0]}"
            else:
                symbol = order_book_id
            symbols.append(symbol)
        
        # 分批拉取
        batch_size = 500
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]
            
            try:
                data = self.rq.get_minute_data(
                    symbols=batch,
                    start_date=date,
                    end_date=date,
                    frequency='1min'
                )
                
                if data is not None and not data.empty:
                    # 标准化
                    data = data.reset_index()
                    if 'order_book_id' in data.columns:
                        data['symbol'] = data['order_book_id'].apply(
                            lambda x: f"SH{x.split('.')[0]}" if x.endswith('.SH') 
                            else f"SZ{x.split('.')[0]}" if x.endswith('.XSHE') 
                            else x
                        )
                    
                    # 确保有时间列
                    if 'date' in data.columns:
                        data['time'] = pd.to_datetime(data['date'])
                    elif 'datetime' in data.columns:
                        data['time'] = pd.to_datetime(data['datetime'])
                    
                    # 插入数据库
                    if 'time' in data.columns and 'symbol' in data.columns:
                        db.insert_price(data, table=TABLE_1MIN)
                        self.quota_used += len(data)
                        logger.info(f"  插入 {len(data):,} 条")
            
            except Exception as e:
                logger.error(f"批次拉取失败: {e}")
            
            time.sleep(1)  # 请求间隔


def main():
    parser = argparse.ArgumentParser(description='1分钟数据完整性检测和拉取')
    
    parser.add_argument('--check-only', action='store_true', help='仅检测不拉取')
    parser.add_argument('--year', type=int, help='拉取特定年份')
    parser.add_argument('--month', type=int, help='拉取特定月份')
    parser.add_argument('--force-all', action='store_true', help='强制拉取所有历史')
    
    args = parser.parse_args()
    
    checker = DataCompletenessChecker()
    
    if args.check_only:
        # 只检测
        print(checker.generate_report())
        return
    
    if args.year:
        # 拉取特定年份
        puller = IncrementalPuller()
        puller.pull_year(args.year, args.month)
        return
    
    if args.force_all:
        # 强制拉取所有缺失年份
        missing = checker.get_missing_years()
        logger.info(f"将强制拉取缺失年份: {missing}")
        
        puller = IncrementalPuller()
        for year in missing:
            puller.pull_year(year)
    else:
        # 增量拉取模式: 每天自动运行
        print(checker.generate_report())
        
        # 拉取缺失年份
        missing = checker.get_missing_years()
        if missing:
            puller = IncrementalPuller()
            for year in missing:
                logger.info(f"\n开始拉取 {year} 年数据...")
                puller.pull_year(year)
        else:
            logger.info("✅ 所有年份数据完整")


if __name__ == '__main__':
    main()
