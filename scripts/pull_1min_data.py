#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
米筐1分钟数据拉取脚本
RiceQuant 1-Minute Data Puller

📊 米筐配额限制:
   - 每日限额: 1GB/天
   - 约等于: 1200万条/天 (约800MB)
   - 脚本会自动检测配额，接近80%时停止

设计思路:
1. 增量更新: 只拉取数据库中不存在的数据
2. 分批处理: 每天只拉取部分股票,轮询完成
3. 配额监控: 从米筐API获取配额，接近80%时停止
4. 错误重试: 失败自动重试,跳过无效股票

使用:
    # 检测缺失数据 (不拉取)
    python scripts/pull_1min_data.py --detect
    
    # 自动拉取缺失数据 (每天最多5天，受配额限制)
    python scripts/pull_1min_data.py --auto-pull
    
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

# 设置米筐配置 (从环境变量读取)
import os
if 'RQDATAC_CONF' not in os.environ:
    raise EnvironmentError(
        "请设置环境变量 RQDATAC_CONF，例如:\n"
        "  export RQDATAC_CONF='tcp://license:YOUR_KEY@rqdatad-pro.ricequant.com:16011'\n"
        "或在 .env 文件中配置"
    )

from data.ricequant_source import RiceQuantSource
from data.storage.timescale_storage import TimescaleDB

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ==================== 配置 ====================

# 米筐配额限制 (来自米筐API: 1GB/天)
# 脚本会自动从米筐API获取实际配额使用情况
# 超过80%阈值时自动停止，避免触发限流
DAILY_QUOTA_LIMIT_ROWS = 12_000_000  # 备用: 条数限制 (1200万条/天)
DAILY_QUOTA_LIMIT_BYTES = int(1024 * 1024 * 1024 * 0.8)  # 800MB (80% of 1GB)

# 每批股票数量 (米筐单次请求限制)
BATCH_SIZE = 500  # 每批500只股票

# 请求间隔 (秒) - 避免触发限流
REQUEST_INTERVAL = 1.0  # 每批间隔1秒

# 重试次数
MAX_RETRIES = 3

# 1分钟数据表
TABLE_1MIN = 'price_1min'

# 历史数据范围
HISTORICAL_START_DATE = '20150101'  # 从2015年开始


# ==================== 辅助函数 ====================

def get_trading_dates(start_date: str, end_date: str = None) -> List[str]:
    """
    获取交易日列表 (排除周末)
    
    Args:
        start_date: 开始日期 YYYYMMDD
        end_date: 结束日期 YYYYMMDD, 默认今天
        
    Returns:
        交易日列表
    """
    end_date = end_date or datetime.now().strftime('%Y%m%d')
    
    start = pd.to_datetime(start_date, format='%Y%m%d')
    end = pd.to_datetime(end_date, format='%Y%m%d')
    
    # 使用业务日生成器 (排除周末)
    bday = pd.tseries.offsets.CustomBusinessDay(weekmask='Mon Tue Wed Thu Fri')
    dates = pd.date_range(start, end, freq=bday)
    
    return [d.strftime('%Y%m%d') for d in dates]


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
    
    def get_existing_dates(self) -> Set[str]:
        """
        获取数据库中已有数据的日期列表
        
        Returns:
            日期集合 (YYYYMMDD格式)
        """
        query = f"""
            SELECT DISTINCT time::date as date FROM {TABLE_1MIN}
            ORDER BY date
        """
        
        try:
            with self.db.connection() as conn:
                df = pd.read_sql(query, conn)
            
            if df.empty:
                return set()
            
            # 转换为 YYYYMMDD 格式
            dates = set(pd.to_datetime(df['date']).dt.strftime('%Y%m%d'))
            logger.info(f"📊 数据库中已有 {len(dates)} 个交易日的数据")
            return dates
        except Exception as e:
            logger.warning(f"查询已有日期失败: {e}")
            return set()
    
    def detect_missing_dates(
        self,
        start_date: str = None,
        end_date: str = None,
        check_recent_only: bool = True
    ) -> List[str]:
        """
        检测缺失的交易日
        
        Args:
            start_date: 开始日期 (默认看 check_recent_only)
            end_date: 结束日期 (默认今天)
            check_recent_only: 是否只检查最近90天 (避免全表扫描)
            
        Returns:
            缺失的交易日列表
        """
        end_date = end_date or datetime.now().strftime('%Y%m%d')
        
        # 优化: 默认只检查最近90天，避免全表扫描
        if check_recent_only and start_date is None:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
        else:
            start_date = start_date or HISTORICAL_START_DATE
        
        # 获取应有交易日
        expected_dates = set(get_trading_dates(start_date, end_date))
        
        # 获取已有日期 (优化: 使用 time_bucket 加速)
        try:
            query = f"""
                SELECT DISTINCT time_bucket('1 day', time)::date as day
                FROM {TABLE_1MIN}
                WHERE time >= '{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}'
                AND time <= '{end_date[:4]}-{end_date[4:6]}-{end_date[6:]} 23:59:59'
            """
            with self.db.connection() as conn:
                df = pd.read_sql(query, conn)
            existing_dates = set(pd.to_datetime(df['day']).dt.strftime('%Y%m%d')) if not df.empty else set()
        except Exception as e:
            logger.warning(f"快速检测失败: {e}, 尝试全量检测...")
            existing_dates = self.get_existing_dates()
        
        # 计算缺失
        missing_dates = sorted(expected_dates - existing_dates)
        
        logger.info(f"📊 检查范围: {start_date} ~ {end_date}")
        logger.info(f"📊 应有交易日: {len(expected_dates)}")
        logger.info(f"📊 已有交易日: {len(existing_dates)}")
        logger.info(f"📊 缺失交易日: {len(missing_dates)}")
        
        # 如果最近90天没有缺失，检查更早的日期
        if check_recent_only and not missing_dates:
            logger.info("📊 最近90天无缺失，检查更早日期...")
            return self.detect_missing_dates(
                start_date=HISTORICAL_START_DATE,
                end_date=end_date,
                check_recent_only=False
            )
        
        return missing_dates
    
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
    
    def _get_quota_from_api(self) -> dict:
        """从米筐API获取当前配额使用情况"""
        try:
            from rqdatac import user
            quota = user.get_quota()
            return {
                'bytes_used': quota.get('bytes_used', 0),
                'bytes_limit': quota.get('bytes_limit', 0),
            }
        except Exception as e:
            logger.warning(f"获取配额失败: {e}")
            return {'bytes_used': 0, 'bytes_limit': 0}
    
    def _check_quota(self, records: int, data_size_bytes: int = 0) -> bool:
        """
        检查配额是否足够
        
        Args:
            records: 本次计划拉取的记录数
            data_size_bytes: 本次数据大小(字节)
            
        Returns:
            是否可以继续
        """
        # 主要方法: 检查API返回的字节配额 (更准确)
        if data_size_bytes > 0:
            quota_info = self._get_quota_from_api()
            bytes_limit = quota_info.get('bytes_limit', 1024*1024*1024)  # 默认1GB
            bytes_used = quota_info.get('bytes_used', 0)
            
            # 80% 阈值
            safe_limit = int(bytes_limit * 0.8)
            
            # 估算本次使用后的总量
            estimated_total = bytes_used + data_size_bytes
            
            if estimated_total > safe_limit:
                remaining_bytes = safe_limit - bytes_used
                logger.warning(f"⚠️ 配额不足! 剩余可用: {remaining_bytes/1024/1024:.1f} MB (80%阈值)")
                return False
            else:
                # 显示当前使用情况
                logger.info(f"📊 配额: {bytes_used/1024/1024:.1f}/{bytes_limit/1024/1024:.1f} MB ({bytes_used/bytes_limit*100:.1f}%)")
                return True
        
        # 备用方法: 检查条数限制
        if self.quota_used + records > DAILY_QUOTA_LIMIT_ROWS:
            remaining = DAILY_QUOTA_LIMIT_ROWS - self.quota_used
            logger.warning(f"⚠️ 条数配额不足! 剩余可用: {remaining:,} 条")
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
                data = data.reset_index()  # 确保把索引变成列
                
                if 'date' in data.columns:
                    data['time'] = pd.to_datetime(data['date'])
                elif 'datetime' in data.columns:
                    data['time'] = pd.to_datetime(data['datetime'])
                elif 'time' not in data.columns and isinstance(data.index, pd.MultiIndex):
                    # 从索引获取时间
                    data = data.reset_index()
                    if 'time' in data.columns:
                        data['time'] = pd.to_datetime(data['time'])
                
                # 转换symbol格式
                if 'order_book_id' in data.columns:
                    data['symbol'] = data['order_book_id'].apply(
                        lambda x: f"SH{x.split('.')[0]}" if x.endswith('.SH') 
                        else f"SZ{x.split('.')[0]}" if x.endswith('.XSHE') 
                        else x
                    )
                
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
            
            logger.info(f"📦 拉取第 {batch_num}/{total_batches} 批 ({len(batch)} 只股票)...")
            
            # 拉取数据
            data = self._pull_batch(batch, self.date)
            
            if data.empty:
                logger.debug(f"第 {batch_num} 批无数据")
                self.stats['skipped_existing'] += len(batch)
                continue
            
            # 计算数据大小
            data_size_bytes = data.memory_usage(deep=True).sum()
            
            # 检查配额 (基于实际数据大小)
            if not self._check_quota(len(data), data_size_bytes):
                logger.warning("⚠️ 配额已用尽，停止拉取")
                break
            
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
        logger.info(f"   今日配额: {self.quota_used:,}/{DAILY_QUOTA_LIMIT_ROWS:,}")
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
    
    def auto_pull_historical(
        self,
        max_dates_per_run: int = 5,
        max_quota_per_day: int = None
    ):
        """
        自动补历史数据 (每天定时任务)
        
        检测缺失数据，按配额限制逐天拉取
        
        Args:
            max_dates_per_run: 每次运行最多拉取天数
            max_quota_per_day: 每天配额限制 (默认 DAILY_QUOTA_LIMIT_ROWS)
        """
        max_quota_per_day = max_quota_per_day or DAILY_QUOTA_LIMIT_ROWS
        
        logger.info("🔍 开始检测缺失数据...")
        
        # 检测缺失日期
        missing_dates = self.detect_missing_dates()
        
        if not missing_dates:
            logger.info("✅ 没有缺失数据，无需拉取")
            return
        
        # 限制每次拉取数量
        dates_to_pull = missing_dates[:max_dates_per_run]
        
        logger.info(f"📅 本次将拉取 {len(dates_to_pull)} 个交易日: {dates_to_pull}")
        
        # 逐天拉取
        for date in dates_to_pull:
            self.date = date
            self.date_formatted = f"{date[:4]}-{date[4:6]}-{date[6:]}"
            
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
            
            # 检查配额
            if self.quota_used >= max_quota_per_day:
                logger.warning("⚠️ 今日配额已用尽，停止拉取")
                break
            
            # 拉取
            self.pull(force=False)
            
            # 每日间隔 (避免请求过快)
            time.sleep(2)
        
        logger.info("✅ 自动拉取完成")


# ==================== 命令行 ====================

def main():
    global DAILY_QUOTA_LIMIT_ROWS  # noqa: E0602
    
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
        default=DAILY_QUOTA_LIMIT_ROWS,
        help=f'每日配额限制 (默认 {DAILY_QUOTA_LIMIT_ROWS:,})'
    )
    
    parser.add_argument(
        '--detect',
        action='store_true',
        help='检测缺失数据 (不拉取)'
    )
    
    parser.add_argument(
        '--auto-pull',
        action='store_true',
        help='自动补历史数据 (检测缺失后拉取)'
    )
    
    parser.add_argument(
        '--max-dates',
        type=int,
        default=5,
        help='每次自动拉取的最大天数 (默认5)'
    )
    
    args = parser.parse_args()
    
    # 全局配额设置
    DAILY_QUOTA_LIMIT_ROWS = args.quota
    
    # 创建拉取器
    puller = MinuteDataPuller(date=args.date if not args.start_date else None)
    
    # 执行拉取
    if args.detect:
        # 检测模式
        missing = puller.detect_missing_dates()
        if missing:
            print(f"\n缺失 {len(missing)} 个交易日:")
            # 按年份分组显示
            from collections import defaultdict
            by_year = defaultdict(list)
            for d in missing:
                by_year[d[:4]].append(d)
            for year in sorted(by_year.keys()):
                dates = by_year[year]
                print(f"  {year}: {len(dates)} 天 ({dates[0]} ~ {dates[-1]})")
        else:
            print("✅ 没有缺失数据")
        sys.exit(0)
    
    if args.auto_pull:
        # 自动拉取模式
        puller.auto_pull_historical(max_dates_per_run=args.max_dates)
        sys.exit(0)
    
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
