#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
米筐1分钟数据拉取脚本
RiceQuant 1-Minute Data Puller

设计思路 (适应1GB/天限额):
1. 增量更新: 只拉取数据库中不存在的数据
2. 分批处理: 每天只拉取部分股票,轮询完成
3. 配额监控: 记录拉取量,接近限额时停止
4. 错误重试: 失败自动重试,跳过无效股票

使用:
    # 拉取今天的数据 (增量)
    python scripts/pull_1min_data.py --date today
    
    # 拉取特定日期
    python scripts/pull_1min_data.py --date 20260227
    
    # 强制全量拉取 (危险!)
    python scripts/pull_1min_data.py --date 20260227 --force
    
    # 补历史数据
    python scripts/pull_1min_data.py --start-date 20260101 --end-date 20260131
    
    # 只拉取指定股票
    python scripts/pull_1min_data.py --symbols SH600000,SZ000001
"""

import argparse
import logging
import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Set, Optional

import pandas as pd
import numpy as np

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from data.ricequant_source import RiceQuantSource
from data.storage.timescale_storage import TimescaleDB

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 配置 ====================

# 每日配额限制 (条数, 约1GB)
DAILY_QUOTA_LIMIT = 5_000_000  # 500万条/天

# 每批股票数量 (米筐单次请求限制)
BATCH_SIZE = 100

# 请求间隔 (秒) - 避免触发限流
REQUEST_INTERVAL = 0.5

# 重试次数
MAX_RETRIES = 3

# 1分钟数据表
TABLE_1MIN = 'price_1min'


# ==================== 主类 ====================

class MinuteDataPuller:
    """
    1分钟数据拉取器
    
    功能:
    - 增量拉取 (只拉取缺失数据)
    - 分批处理 (避免单次请求过大)
    - 配额监控 (1GB/天限制)
    - 断点续传 (记录拉取进度)
    """
    
    def __init__(
        self,
        date: str = None,
        db_config: dict = None
    ):
        """
        初始化
        
        Args:
            date: 拉取日期 (YYYYMMDD), 'today' 或 None
            db_config: 数据库配置
        """
        # 解析日期
        if date == 'today' or date is None:
            self.date = datetime.now().strftime('%Y%m%d')
        else:
            self.date = date.replace('-', '')
        
        self.date_formatted = f"{self.date[:4]}-{self.date[4:6]}-{self.date[6:]}"
        
        # 初始化数据源和数据库
        self.rq = RiceQuantSource()
        self.db = TimescaleDB(db_config)
        
        # 确保表存在
        self.db.create_hypertable(TABLE_1MIN, '1 week')
        
        # 统计
        self.stats = {
            'total_requested': 0,
            'total_inserted': 0,
            'skipped_existing': 0,
            'failed_symbols': [],
            'start_time': datetime.now(),
        }
        
        # 进度文件
        self.progress_file = PROJECT_ROOT / '.cache' / 'pull_1min_progress.json'
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        
        # 配额跟踪文件
        self.quota_file = PROJECT_ROOT / '.cache' / 'pull_1min_quota.json'
        self._load_quota()
    
    def _load_quota(self):
        """加载今日配额使用情况"""
        today = datetime.now().strftime('%Y%m%d')
        
        if self.quota_file.exists():
            import json
            with open(self.quota_file) as f:
                quota_data = json.load(f)
            
            # 检查是否是同一天
            if quota_data.get('date') == today:
                self.quota_used = quota_data.get('used', 0)
                logger.info(f"📊 今日已拉取 {self.quota_used:,} 条")
                return
        
        # 新的一天
        self.quota_used = 0
    
    def _save_quota(self):
        """保存配额使用情况"""
        import json
        
        quota_data = {
            'date': datetime.now().strftime('%Y%m%d'),
            'used': self.quota_used
        }
        
        with open(self.quota_file, 'w') as f:
            json.dump(quota_data, f)
    
    def _get_existing_symbols(self) -> Set[str]:
        """
        获取数据库中已存在的股票列表
        
        Returns:
            股票代码集合
        """
        query = f"""
            SELECT DISTINCT symbol FROM {TABLE_1MIN}
            WHERE time >= '{self.date_formatted} 00:00:00'
            AND time < '{self.date_formatted} 23:59:59'
        """
        
        try:
            with self.db.connection() as conn:
                df = pd.read_sql(query, conn)
            
            existing = set(df['symbol'].unique()) if not df.empty else set()
            logger.info(f"📊 数据库中已存在 {len(existing)} 只股票的数据")
            return existing
        except Exception as e:
            logger.warning(f"查询已存在数据失败: {e}")
            return set()
    
    def _get_all_symbols(self) -> List[str]:
        """获取全市场股票列表"""
        stocks = self.rq.get_all_stocks(self.date)
        
        if stocks is None or stocks.empty:
            logger.error("无法获取股票列表")
            return []
        
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
        
        logger.info(f"📊 全市场 {len(symbols)} 只股票")
        return symbols
    
    def _get_missing_symbols(
        self,
        all_symbols: List[str],
        existing_symbols: Set[str],
        force: bool = False
    ) -> List[str]:
        """
        计算需要拉取的股票列表
        
        Args:
            all_symbols: 全量股票列表
            existing_symbols: 已存在的股票
            force: 是否强制全量拉取
            
        Returns:
            需要拉取的股票列表
        """
        if force:
            logger.info("⚠️ 强制模式: 拉取全部股票")
            return all_symbols
        
        # 增量模式: 只拉取不存在的
        missing = [s for s in all_symbols if s not in existing_symbols]
        logger.info(f"📊 增量模式: {len(missing)} 只股票需要拉取")
        
        return missing
    
    def _check_quota(self, records: int) -> bool:
        """
        检查配额是否足够
        
        Args:
            records: 本次计划拉取的记录数
            
        Returns:
            是否可以继续
        """
        if self.quota_used + records > DAILY_QUOTA_LIMIT:
            remaining = DAILY_QUOTA_LIMIT - self.quota_used
            logger.warning(f"⚠️ 配额不足! 剩余可用: {remaining:,} 条")
            return False
        return True
    
    def _pull_batch(
        self,
        symbols: List[str],
        date: str = None
    ) -> pd.DataFrame:
        """
        拉取一批股票的数据
        
        Args:
            symbols: 股票列表
            date: 日期
            
        Returns:
            1分钟数据DataFrame
        """
        date = date or self.date
        
        for attempt in range(MAX_RETRIES):
            try:
                data = self.rq.get_minute_data(
                    symbols=symbols,
                    start_date=date,
                    end_date=date,
                    frequency='1min'
                )
                
                if data is None or data.empty:
                    logger.debug(f"⚠️ {symbols} 无数据")
                    return pd.DataFrame()
                
                # 标准化列名
                if 'date' in data.columns:
                    data['time'] = pd.to_datetime(data['date'])
                elif 'time' not in data.columns:
                    # 尝试从索引获取
                    if isinstance(data.index, pd.MultiIndex):
                        data = data.reset_index()
                
                # 确保必要字段
                required_cols = ['time', 'symbol', 'open', 'high', 'low', 'close', 'volume']
                for col in required_cols:
                    if col not in data.columns:
                        logger.warning(f"缺少字段: {col}")
                        return pd.DataFrame()
                
                return data
                
            except Exception as e:
                logger.warning(f"拉取失败 (尝试 {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(REQUEST_INTERVAL * (attempt + 1))
                else:
                    logger.error(f"股票 {symbols[0] if symbols else 'unknown'} 拉取失败")
                    return pd.DataFrame()
        
        return pd.DataFrame()
    
    def _save_progress(self, date: str, processed: int, total: int):
        """保存拉取进度"""
        import json
        
        progress = {
            'date': date,
            'processed': processed,
            'total': total,
            'timestamp': datetime.now().isoformat()
        }
        
        with open(self.progress_file, 'w') as f:
            json.dump(progress, f)
    
    def pull(
        self,
        symbols: List[str] = None,
        force: bool = False,
        dry_run: bool = False
    ) -> dict:
        """
        执行拉取
        
        Args:
            symbols: 指定股票列表 (None = 全市场)
            force: 强制全量拉取
            dry_run: 试运行 (不实际拉取)
            
        Returns:
            统计信息
        """
        logger.info(f"🚀 开始拉取 {self.date} 的1分钟数据")
        
        # 1. 获取全量股票列表
        if symbols:
            # 解析传入的股票列表
            all_symbols = symbols if isinstance(symbols, list) else symbols.split(',')
            all_symbols = [s.strip() for s in all_symbols]
        else:
            all_symbols = self._get_all_symbols()
        
        if not all_symbols:
            logger.error("无可拉取的股票")
            return self.stats
        
        # 2. 检查已存在数据
        existing_symbols = self._get_existing_symbols() if not force else set()
        
        # 3. 计算需要拉取的股票
        missing_symbols = self._get_missing_symbols(all_symbols, existing_symbols, force)
        
        if not missing_symbols:
            logger.info("✅ 所有股票数据已存在，无需拉取")
            return self.stats
        
        # 4. 试运行模式
        if dry_run:
            logger.info(f"📝 试运行: 将拉取 {len(missing_symbols)} 只股票")
            self.stats['total_requested'] = len(missing_symbols)
            return self.stats
        
        # 5. 分批拉取
        total_batches = (len(missing_symbols) + BATCH_SIZE - 1) // BATCH_SIZE
        
        logger.info(f"📊 总计 {len(missing_symbols)} 只股票, 分 {total_batches} 批拉取")
        
        for i in range(0, len(missing_symbols), BATCH_SIZE):
            batch = missing_symbols[i:i + BATCH_SIZE]
            batch_num = i // BATCH_SIZE + 1
            
            # 检查配额
            # 估算: 每只股票约480条/天 (240分钟 × 2市场)
            estimated_records = len(batch) * 500  # 保守估算
            
            if not self._check_quota(estimated_records):
                logger.warning("⚠️ 配额已用尽，停止拉取")
                break
            
            logger.info(f"📦 拉取第 {batch_num}/{total_batches} 批 ({len(batch)} 只股票)...")
            
            # 拉取数据
            data = self._pull_batch(batch, self.date)
            
            if data.empty:
                logger.debug(f"第 {batch_num} 批无数据")
                self.stats['skipped_existing'] += len(batch)
                continue
            
            # 插入数据库
            try:
                inserted = self.db.insert_price(data, table=TABLE_1MIN)
                self.stats['total_inserted'] += inserted
                self.quota_used += inserted
                self._save_quota()
                
            except Exception as e:
                logger.error(f"插入失败: {e}")
                self.stats['failed_symbols'].extend(batch)
            
            # 保存进度
            self._save_progress(self.date, batch_num, total_batches)
            
            # 请求间隔
            if i + BATCH_SIZE < len(missing_symbols):
                time.sleep(REQUEST_INTERVAL)
        
        # 6. 统计
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        
        logger.info("=" * 50)
        logger.info(f"✅ 拉取完成!")
        logger.info(f"   日期: {self.date}")
        logger.info(f"   请求股票: {len(missing_symbols)}")
        logger.info(f"   实际插入: {self.stats['total_inserted']:,} 条")
        logger.info(f"   跳过/已有: {self.stats['skipped_existing']}")
        logger.info(f"   失败: {len(self.stats['failed_symbols'])}")
        logger.info(f"   今日配额: {self.quota_used:,}/{DAILY_QUOTA_LIMIT:,}")
        logger.info(f"   耗时: {elapsed:.1f}秒")
        logger.info("=" * 50)
        
        return self.stats
    
    def pull_historical(
        self,
        start_date: str,
        end_date: str = None,
        symbols: List[str] = None
    ):
        """
        补历史数据
        
        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD), 默认start_date
            symbols: 指定股票列表
        """
        end_date = end_date or start_date
        
        # 解析日期范围
        start = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
        
        dates = pd.date_range(start, end, freq='B')  # 只交易日
        
        logger.info(f"📅 将拉取 {len(dates)} 个交易日")
        
        for date in dates:
            self.date = date.strftime('%Y%m%d')
            self.date_formatted = date.strftime('%Y-%m-%d')
            
            logger.info(f"\n{'='*50}")
            logger.info(f"处理日期: {self.date}")
            logger.info(f"{'='*50}")
            
            # 重置统计
            self.stats = {
                'total_requested': 0,
                'total_inserted': 0,
                'skipped_existing': 0,
                'failed_symbols': [],
                'start_time': datetime.now(),
            }
            
            # 拉取
            self.pull(symbols=symbols, force=False)
            
            # 每日间隔
            time.sleep(1)


# ==================== 命令行 ====================

def main():
    global DAILY_QUOTA_LIMIT  # noqa: E0602
    
    parser = argparse.ArgumentParser(
        description='米筐1分钟数据拉取脚本',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument(
        '--date',
        type=str,
        default='today',
        help='拉取日期 (YYYYMMDD, today, 默认为today)'
    )
    
    parser.add_argument(
        '--start-date',
        type=str,
        help='开始日期 (补历史数据用, YYYYMMDD)'
    )
    
    parser.add_argument(
        '--end-date',
        type=str,
        help='结束日期 (补历史数据用, YYYYMMDD)'
    )
    
    parser.add_argument(
        '--symbols',
        type=str,
        help='指定股票列表 (逗号分隔, 如 SH600000,SZ000001)'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='强制全量拉取 (忽略已存在数据)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='试运行模式 (只显示计划,不实际拉取)'
    )
    
    parser.add_argument(
        '--quota',
        type=int,
        default=DAILY_QUOTA_LIMIT,
        help=f'每日配额限制 (默认 {DAILY_QUOTA_LIMIT:,})'
    )
    
    args = parser.parse_args()
    
    # 全局配额设置
    DAILY_QUOTA_LIMIT = args.quota
    
    # 创建拉取器
    puller = MinuteDataPuller(date=args.date if not args.start_date else None)
    
    # 执行拉取
    if args.start_date:
        # 历史数据补录模式
        puller.pull_historical(
            start_date=args.start_date,
            end_date=args.end_date,
            symbols=args.symbols.split(',') if args.symbols else None
        )
    else:
        # 单日拉取模式
        puller.pull(
            symbols=args.symbols,
            force=args.force,
            dry_run=args.dry_run
        )


if __name__ == '__main__':
    main()
