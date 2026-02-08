#!/usr/bin/env python3
"""
米筐数据获取脚本

功能:
1. 获取全市场股票列表
2. 获取所有股票的日线数据
3. 保存到 SQLite 数据库

使用方式:
    python ricequant_downloader.py --api-token YOUR_TOKEN

依赖:
    pip install ricequant pandas numpy

注意:
    - 需要米筐 API token
    - 免费账户有数据限制
    - 建议分批获取数据
"""

import argparse
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import os
import sys

# 尝试导入 ricequant
try:
    import rqdatac
    RQ_AVAILABLE = True
except ImportError:
    RQ_AVAILABLE = False
    print("⚠️ 未安装 ricequant，请运行: pip install ricequant")


# ========== 配置 ==========

DEFAULT_DB_PATH = "storage/database/market_data.db"
DEFAULT_START_DATE = "2010-01-01"
DEFAULT_END_DATE = datetime.now().strftime("%Y-%m-%d")

# 股票状态
STOCK_STATUS = ['Listed', 'Suspended']


# ========== 数据库管理 ==========

class MarketDataDB:
    """
    市场数据数据库
    """
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """
        初始化
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 股票列表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stocks (
                code TEXT PRIMARY KEY,
                name TEXT,
                exchange TEXT,
                list_date TEXT,
                delist_date TEXT,
                status TEXT,
                last_updated TEXT
            )
        ''')
        
        # 日线数据
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                date TEXT,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                volume REAL,
                amount REAL,
                turn REAL,
                pct_chg REAL,
                pre_close REAL,
                adj_factor REAL,
                isST INTEGER DEFAULT 0,
                UNIQUE(code, date)
            )
        ''')
        
        # 复权因子
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS adj_factors (
                code TEXT,
                date TEXT,
                adj_factor REAL,
                dividend REAL,
                split_ratio REAL,
                PRIMARY KEY(code, date)
            )
        ''')
        
        # 交易日历
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS trading_days (
                date TEXT PRIMARY KEY,
                is_trading INTEGER DEFAULT 1,
                pretrade_date TEXT
            )
        ''')
        
        # 下载日志
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS download_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT,
                start_date TEXT,
                end_date TEXT,
                status TEXT,
                records INTEGER,
                error TEXT,
                downloaded_at TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def get_connection(self) -> sqlite3.Connection:
        """获取数据库连接"""
        return sqlite3.connect(self.db_path)
    
    def save_stocks(self, stocks: pd.DataFrame):
        """保存股票列表"""
        conn = self.get_connection()
        stocks.to_sql('stocks', conn, if_exists='replace', index=False)
        conn.close()
    
    def save_daily_data(self, data: pd.DataFrame):
        """保存日线数据"""
        conn = self.get_connection()
        data.to_sql('daily_data', conn, if_exists='append', index=False)
        conn.close()
    
    def get_downloaded_codes(self) -> List[str]:
        """获取已下载的股票代码"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT code FROM daily_data")
        codes = [r[0] for r in cursor.fetchall()]
        conn.close()
        return codes


# ========== 米筐数据获取 ==========

class RiceQuantDownloader:
    """
    米筐数据下载器
    """
    
    def __init__(self, token: str, db_path: str = DEFAULT_DB_PATH):
        """
        初始化
        
        Args:
            token: 米筐 API token
            db_path: 数据库路径
        """
        self.token = token
        self.db = MarketDataDB(db_path)
        
        if RQ_AVAILABLE:
            rqdatac.set_token(token)
            self.conn = rqdatac
        else:
            self.conn = None
    
    def test_connection(self) -> bool:
        """测试连接"""
        if not RQ_AVAILABLE:
            return False
        
        try:
            # 测试获取一只股票
            df = self.conn.get_price('000001.XSHE', 
                                   start_date='2024-01-01',
                                   end_date='2024-01-01')
            return len(df) > 0
        except Exception as e:
            print(f"❌ 连接测试失败: {e}")
            return False
    
    def get_all_stocks(self, date: str = None) -> pd.DataFrame:
        """
        获取全市场股票列表
        
        Args:
            date: 指定日期的股票列表，为空则获取所有
            
        Returns:
            股票列表 DataFrame
        """
        if not RQ_AVAILABLE:
            print("❌ ricequant 未安装")
            return pd.DataFrame()
        
        try:
            if date:
                stocks = self.conn.get_all_securities(date=date)
            else:
                stocks = self.conn.get_all_securities()
            
            # 转换为标准格式
            stocks = stocks.reset_index()
            stocks.columns = ['code', 'name', 'exchange', 'type', 'status', 'list_date', 'delist_date']
            
            print(f"✅ 获取股票列表: {len(stocks)} 只")
            return stocks
            
        except Exception as e:
            print(f"❌ 获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def get_daily_data(self, 
                      codes: List[str],
                      start_date: str = DEFAULT_START_DATE,
                      end_date: str = DEFAULT_END_DATE,
                      adjust_type: str = 'pre',
                      fields: List[str] = None) -> pd.DataFrame:
        """
        获取日线数据
        
        Args:
            codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            adjust_type: 复权类型 ('pre' 前复权, 'none' 不复权, 'post' 后复权)
            fields: 指定字段
            
        Returns:
            日线数据 DataFrame
        """
        if not RQ_AVAILABLE:
            print("❌ ricequant 未安装")
            return pd.DataFrame()
        
        if fields is None:
            fields = ['open', 'high', 'low', 'close', 'volume', 
                      'amount', 'turn', 'pct_chg', 'pre_close', 'isST']
        
        all_data = []
        batch_size = 50  # 每次请求50只股票
        
        total = len(codes)
        success = 0
        failed = 0
        
        print(f"📥 开始下载日线数据: {start_date} ~ {end_date}")
        print(f"   股票数量: {total}")
        print(f"   复权类型: {adjust_type}")
        
        for i in range(0, total, batch_size):
            batch_codes = codes[i:i+batch_size]
            
            try:
                # 获取批量数据
                df = self.conn.get_price(batch_codes,
                                       start_date=start_date,
                                       end_date=end_date,
                                       adjust_type=adjust_type,
                                       fields=fields)
                
                if df is not None and len(df) > 0:
                    all_data.append(df)
                    success += len(df['code'].unique())
                
                # 避免请求过快
                time.sleep(0.5)
                
                # 进度
                progress = min(i + batch_size, total)
                print(f"\r   进度: {progress}/{total} ({progress*100/total:.1f}%)", end='', flush=True)
                
            except Exception as e:
                failed += len(batch_codes)
                print(f"\n   ⚠️ 批次 {i//batch_size + 1} 失败: {e}")
                continue
        
        print(f"\n✅ 下载完成: {success} 条, 失败: {failed} 条")
        
        if all_data:
            return pd.concat(all_data, ignore_index=True)
        return pd.DataFrame()
    
    def get_single_stock_daily(self, 
                              code: str,
                              start_date: str = DEFAULT_START_DATE,
                              end_date: str = DEFAULT_END_DATE) -> pd.DataFrame:
        """
        获取单只股票的日线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            日线数据
        """
        if not RQ_AVAILABLE:
            return pd.DataFrame()
        
        try:
            df = self.conn.get_price(code,
                                   start_date=start_date,
                                   end_date=end_date)
            return df
        except Exception as e:
            print(f"❌ 获取 {code} 数据失败: {e}")
            return pd.DataFrame()
    
    def get_adj_factors(self,
                       codes: List[str],
                       start_date: str = DEFAULT_START_DATE,
                       end_date: str = DEFAULT_END_DATE) -> pd.DataFrame:
        """
        获取复权因子
        
        Args:
            codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            复权因子 DataFrame
        """
        if not RQ_AVAILABLE:
            return pd.DataFrame()
        
        try:
            df = self.conn.get_dividend(
                codes,
                start_date=start_date,
                end_date=end_date,
                fields=['code', 'ex_date', 'adj_factor', 'dividends', 'split_ratio']
            )
            return df
        except Exception as e:
            print(f"❌ 获取复权因子失败: {e}")
            return pd.DataFrame()
    
    def get_trading_days(self,
                        start_date: str = DEFAULT_START_DATE,
                        end_date: str = DEFAULT_END_DATE) -> pd.DataFrame:
        """
        获取交易日历
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            交易日 DataFrame
        """
        if not RQ_AVAILABLE:
            return pd.DataFrame()
        
        try:
            df = self.conn.get_trading_days(
                start_date=start_date,
                end_date=end_date
            )
            return df
        except Exception as e:
            print(f"❌ 获取交易日历失败: {e}")
            return pd.DataFrame()
    
    def download_all(self,
                   start_date: str = DEFAULT_START_DATE,
                   end_date: str = DEFAULT_END_DATE,
                   adjust_type: str = 'pre',
                   incremental: bool = True):
        """
        下载所有数据
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            adjust_type: 复权类型
            incremental: 是否增量下载
        """
        print("=" * 60)
        print("🚀 开始全市场数据下载")
        print("=" * 60)
        
        # 1. 测试连接
        if not self.test_connection():
            print("❌ 连接米筐失败，请检查 API token")
            return
        
        # 2. 获取股票列表
        print("\n📋 Step 1: 获取股票列表")
        stocks = self.get_all_stocks()
        if stocks.empty:
            return
        
        self.db.save_stocks(stocks)
        
        # 3. 确定要下载的股票
        codes = stocks['code'].tolist()
        
        if incremental:
            downloaded = self.db.get_downloaded_codes()
            codes_to_download = [c for c in codes if c not in downloaded]
            print(f"\n📊 已下载: {len(downloaded)} 只")
            print(f"   待下载: {len(codes_to_download)} 只")
        else:
            codes_to_download = codes
        
        if not codes_to_download:
            print("\n✅ 暂无新数据需要下载")
            return
        
        # 4. 下载日线数据
        print(f"\n📈 Step 2: 下载日线数据")
        daily_data = self.get_daily_data(
            codes_to_download,
            start_date,
            end_date,
            adjust_type
        )
        
        if not daily_data.empty:
            self.db.save_daily_data(daily_data)
            print(f"\n💾 保存数据: {len(daily_data)} 条")
        
        # 5. 获取交易日历
        print(f"\n📅 Step 3: 获取交易日历")
        trading_days = self.get_trading_days(start_date, end_date)
        
        if not trading_days.empty:
            conn = self.db.get_connection()
            trading_days.to_sql('trading_days', conn, if_exists='replace', index=False)
            conn.close()
            print(f"   保存交易日: {len(trading_days)} 天")
        
        print("\n" + "=" * 60)
        print("✅ 全市场数据下载完成!")
        print("=" * 60)


# ========== 数据查询工具 ==========

class DataQuerier:
    """
    数据查询工具
    """
    
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        """
        初始化
        
        Args:
            db_path: 数据库路径
        """
        self.db_path = db_path
        self.db = MarketDataDB(db_path)
    
    def query_stocks(self, 
                    exchange: str = None,
                    status: str = None) -> pd.DataFrame:
        """
        查询股票列表
        
        Args:
            exchange: 交易所 (SSE, SZSE)
            status: 状态
            
        Returns:
            股票列表
        """
        conn = self.db.get_connection()
        
        query = "SELECT * FROM stocks WHERE 1=1"
        params = []
        
        if exchange:
            query += " AND exchange = ?"
            params.append(exchange)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return df
    
    def query_daily(self,
                   code: str = None,
                   start_date: str = None,
                   end_date: str = None,
                   fields: List[str] = None) -> pd.DataFrame:
        """
        查询日线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            fields: 指定字段
            
        Returns:
            日线数据
        """
        conn = self.db.get_connection()
        
        default_fields = ['code', 'date', 'open', 'high', 'low', 'close', 
                         'volume', 'amount', 'turn', 'pct_chg', 'pre_close']
        if fields is None:
            fields = default_fields
        
        # 过滤可用字段
        available = [f for f in fields if f in ['code', 'date', 'open', 'high', 
                     'low', 'close', 'volume', 'amount', 'turn', 'pct_chg', 
                     'pre_close', 'adj_factor', 'isST']]
        if not available:
            available = default_fields
        
        query = f"SELECT {', '.join(available)} FROM daily_data WHERE 1=1"
        params = []
        
        if code:
            query += " AND code = ?"
            params.append(code)
        
        if start_date:
            query += " AND date >= ?"
            params.append(start_date)
        
        if end_date:
            query += " AND date <= ?"
            params.append(end_date)
        
        query += " ORDER BY code, date"
        
        df = pd.read_sql(query, conn, params=params)
        conn.close()
        return df
    
    def get_stock_count(self) -> int:
        """获取股票数量"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM stocks")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    
    def get_data_stats(self) -> Dict:
        """
        获取数据统计
        
        Returns:
            统计信息
        """
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # 股票数量
        cursor.execute("SELECT COUNT(*) FROM stocks")
        stats['stocks'] = cursor.fetchone()[0]
        
        # 日线数据量
        cursor.execute("SELECT COUNT(*) FROM daily_data")
        stats['daily_records'] = cursor.fetchone()[0]
        
        # 日期范围
        cursor.execute("SELECT MIN(date), MAX(date) FROM daily_data")
        dates = cursor.fetchone()
        stats['start_date'] = dates[0]
        stats['end_date'] = dates[1]
        
        conn.close()
        return stats


# ========== 主程序 ==========

def main():
    parser = argparse.ArgumentParser(
        description='米筐数据下载工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 测试连接
  python ricequant_downloader.py --token YOUR_TOKEN --test

  # 下载所有日线数据
  python ricequant_downloader.py --token YOUR_TOKEN

  # 指定日期范围
  python ricequant_downloader.py --token YOUR_TOKEN --start 2023-01-01 --end 2024-01-01

  # 查询数据
  python ricequant_downloader.py --query stocks
  python ricequant_downloader.py --query daily --code 000001.XSHE --start 2024-01-01

  # 查看统计
  python ricequant_downloader.py --stats
        '''
    )
    
    parser.add_argument('--token', '-t', type=str, help='米筐 API token')
    parser.add_argument('--test', action='store_true', help='测试连接')
    parser.add_argument('--start', '-s', type=str, 
                       default=DEFAULT_START_DATE, help='开始日期')
    parser.add_argument('--end', '-e', type=str,
                       default=DEFAULT_END_DATE, help='结束日期')
    parser.add_argument('--adjust', '-a', type=str, default='pre',
                       choices=['pre', 'none', 'post'],
                       help='复权类型 (pre/none/post)')
    parser.add_argument('--db', type=str, default=DEFAULT_DB_PATH,
                       help='数据库路径')
    parser.add_argument('--query', type=str, choices=['stocks', 'daily', 'stats'],
                       help='查询模式')
    parser.add_argument('--code', type=str, help='股票代码')
    parser.add_argument('--full', action='store_true', help='全量下载（不增量）')
    
    args = parser.parse_args()
    
    # 如果没有 token 且不是查询，退出
    if not args.token and not args.query:
        parser.print_help()
        print("\n❌ 请提供 API token: --token YOUR_TOKEN")
        return
    
    # 初始化
    downloader = None
    if args.token:
        downloader = RiceQuantDownloader(args.token, args.db)
    
    querier = DataQuerier(args.db)
    
    # 测试连接
    if args.test:
        if downloader and downloader.test_connection():
            print("✅ 连接成功!")
        else:
            print("❌ 连接失败!")
        return
    
    # 查询模式
    if args.query == 'stocks':
        df = querier.query_stocks()
        print(f"\n📋 股票列表: {len(df)} 只")
        print(df.head(10))
        
    elif args.query == 'daily':
        df = querier.query_daily(
            code=args.code,
            start_date=args.start,
            end_date=args.end
        )
        print(f"\n📈 日线数据: {len(df)} 条")
        if not df.empty:
            print(df.head(10))
        
    elif args.query == 'stats':
        stats = querier.get_data_stats()
        print("\n📊 数据统计:")
        print(f"   股票数量: {stats.get('stocks', 0)}")
        print(f"   日线记录: {stats.get('daily_records', 0)}")
        print(f"   日期范围: {stats.get('start_date')} ~ {stats.get('end_date')}")
    
    # 下载模式
    elif args.token:
        downloader.download_all(
            start_date=args.start,
            end_date=args.end,
            adjust_type=args.adjust,
            incremental=not args.full
        )
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
