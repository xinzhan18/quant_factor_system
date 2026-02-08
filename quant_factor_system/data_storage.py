"""
因子数据持久化模块
Factor Data Storage Module

功能：
- SQLite 数据存储
- 自动增量更新
- 数据版本管理
"""

import sqlite3
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import os
import json
import hashlib
import logging
from contextlib import contextmanager
from quant_factor_system.data_source import MultiSourceDataManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SQLiteDB:
    """
    SQLite 数据库管理器
    """
    
    def __init__(self, db_path: str = "./data/factor_data.db"):
        """
        初始化数据库
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._ensure_dir()
        self._init_db()
    
    def _ensure_dir(self):
        """确保数据库目录存在"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    @contextmanager
    def connection(self):
        """获取数据库连接"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def _init_db(self):
        """初始化数据库表"""
        with self.connection() as conn:
            # 价格数据表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS price_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume REAL,
                    amount REAL,
                    adj_close REAL,
                    UNIQUE(symbol, date)
                )
            """)
            
            # 财务数据表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fundamental_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    pe REAL,
                    pb REAL,
                    ps REAL,
                    roe REAL,
                    roa REAL,
                    net_profit REAL,
                    revenue REAL,
                    market_cap REAL,
                    enterprise_value REAL,
                    UNIQUE(symbol, date)
                )
            """)
            
            # 因子数据表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS factor_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    date DATE NOT NULL,
                    factor_name TEXT NOT NULL,
                    factor_value REAL,
                    UNIQUE(symbol, date, factor_name)
                )
            """)
            
            # 因子绩效表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS factor_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    factor_name TEXT NOT NULL,
                    calculation_date DATE NOT NULL,
                    ic REAL,
                    ic_ir REAL,
                    ic_sign_ratio REAL,
                    turnover REAL,
                    group_return_q1 REAL,
                    group_return_q5 REAL,
                    spread_return REAL,
                    sharpe_q1 REAL,
                    sharpe_q5 REAL
                )
            """)
            
            # 系统状态表
            conn.execute("""
                CREATE TABLE IF NOT EXISTS system_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    update_type TEXT NOT NULL,
                    last_update DATETIME,
                    status TEXT,
                    records_updated INTEGER,
                    error_message TEXT
                )
            """)
            
            # 创建索引
            conn.execute("CREATE INDEX IF NOT EXISTS idx_price_symbol_date ON price_data(symbol, date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_fund_symbol_date ON fundamental_data(symbol, date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_factor_symbol_date ON factor_data(symbol, date)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_factor_perf_name ON factor_performance(factor_name)")
            
            conn.commit()
            logger.info("数据库初始化完成")


class DataRepository:
    """
    数据仓库
    统一管理数据读写
    """
    
    def __init__(self, db_path: str = "./data/factor_data.db"):
        """
        初始化数据仓库
        
        Args:
            db_path: 数据库路径
        """
        self.db = SQLiteDB(db_path)
        self.data_source = MultiSourceDataManager()
    
    # ========== 价格数据操作 ==========
    
    def save_price_data(self, data: pd.DataFrame) -> int:
        """
        保存价格数据（增量更新）
        
        Args:
            data: 价格数据 DataFrame
            
        Returns:
            插入/更新的记录数
        """
        if data.empty:
            return 0
        
        records = 0
        
        with self.db.connection() as conn:
            for _, row in data.iterrows():
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO price_data 
                        (symbol, date, open, high, low, close, volume, amount, adj_close)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('symbol', ''),
                        row.get('date', datetime.now()).strftime('%Y-%m-%d') if isinstance(row.get('date'), pd.Timestamp) else str(row.get('date', '')),
                        row.get('open'),
                        row.get('high'),
                        row.get('low'),
                        row.get('close'),
                        row.get('volume'),
                        row.get('amount'),
                        row.get('adj_close', row.get('close'))
                    ))
                    records += 1
                except Exception as e:
                    logger.debug(f"保存价格数据失败: {e}")
        
        return records
    
    def get_price_data(self, symbols: List[str], 
                       start_date: str, 
                       end_date: str) -> pd.DataFrame:
        """
        获取价格数据
        
        Args:
            symbols: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            价格数据
        """
        with self.db.connection() as conn:
            placeholders = ','.join(['?' for _ in symbols])
            query = f"""
                SELECT symbol, date, open, high, low, close, volume, amount
                FROM price_data
                WHERE symbol IN ({placeholders})
                AND date BETWEEN ? AND ?
                ORDER BY symbol, date
            """
            
            params = symbols + [start_date, end_date]
            df = pd.read_sql(query, conn, params=params)
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index(['symbol', 'date'])
            
            return df
    
    def get_latest_trade_date(self) -> str:
        """获取最新的交易日期"""
        with self.db.connection() as conn:
            result = conn.execute("SELECT MAX(date) FROM price_data").fetchone()
            return result[0] if result[0] else None
    
    def get_price_update_range(self, symbols: List[str]) -> tuple:
        """
        获取需要更新的数据范围
        
        Returns:
            (start_date, end_date)
        """
        latest = self.get_latest_trade_date()
        
        if latest:
            start_date = latest
        else:
            # 默认获取过去2年数据
            start_date = (datetime.now() - timedelta(days=730)).strftime('%Y-%m-%d')
        
        end_date = datetime.now().strftime('%Y-%m-%d')
        
        return start_date, end_date
    
    # ========== 财务数据操作 ==========
    
    def save_fundamental_data(self, data: pd.DataFrame) -> int:
        """保存财务数据"""
        if data.empty:
            return 0
        
        records = 0
        
        with self.db.connection() as conn:
            for _, row in data.iterrows():
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO fundamental_data 
                        (symbol, date, pe, pb, ps, roe, roa, net_profit, revenue, market_cap, enterprise_value)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row.get('symbol', ''),
                        row.get('date', ''),
                        row.get('pe'),
                        row.get('pb'),
                        row.get('ps'),
                        row.get('roe'),
                        row.get('roa'),
                        row.get('net_profit'),
                        row.get('revenue'),
                        row.get('market_cap'),
                        row.get('enterprise_value')
                    ))
                    records += 1
                except Exception as e:
                    logger.debug(f"保存财务数据失败: {e}")
        
        return records
    
    def get_fundamental_data(self, symbols: List[str], 
                             date: str) -> pd.DataFrame:
        """
        获取某一天的财务数据
        
        Args:
            symbols: 股票代码列表
            date: 日期
            
        Returns:
            财务数据
        """
        with self.db.connection() as conn:
            placeholders = ','.join(['?' for _ in symbols])
            query = f"""
                SELECT * FROM fundamental_data
                WHERE symbol IN ({placeholders})
                AND date = ?
            """
            
            params = symbols + [date]
            df = pd.read_sql(query, conn, params=params)
            
            return df
    
    # ========== 因子数据操作 ==========
    
    def save_factor_data(self, symbol: str, date: str, 
                        factors: Dict[str, float]) -> int:
        """
        保存单只股票的因子数据
        
        Args:
            symbol: 股票代码
            date: 日期
            factors: 因子字典 {因子名: 因子值}
            
        Returns:
            保存的因子数量
        """
        records = 0
        
        with self.db.connection() as conn:
            for name, value in factors.items():
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO factor_data 
                        (symbol, date, factor_name, factor_value)
                        VALUES (?, ?, ?, ?)
                    """, (symbol, date, name, value))
                    records += 1
                except Exception as e:
                    logger.debug(f"保存因子数据失败: {e}")
        
        return records
    
    def get_factor_data(self, symbols: List[str], date: str) -> pd.DataFrame:
        """
        获取某一天的因子数据
        
        Args:
            symbols: 股票代码列表
            date: 日期
            
        Returns:
            因子数据 DataFrame
        """
        with self.db.connection() as conn:
            if not symbols:
                query = "SELECT * FROM factor_data WHERE date = ?"
                params = [date]
            else:
                placeholders = ','.join(['?' for _ in symbols])
                query = f"""
                    SELECT * FROM factor_data
                    WHERE symbol IN ({placeholders})
                    AND date = ?
                """
                params = symbols + [date]
            
            df = pd.read_sql(query, conn, params=params)
            
            if not df.empty:
                df = df.pivot(index='symbol', columns='factor_name', values='factor_value')
            
            return df
    
    def get_factor_time_series(self, symbol: str, factor_name: str,
                               start_date: str, end_date: str) -> pd.Series:
        """
        获取因子时间序列
        
        Args:
            symbol: 股票代码
            factor_name: 因子名称
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            因子时间序列
        """
        with self.db.connection() as conn:
            query = """
                SELECT date, factor_value FROM factor_data
                WHERE symbol = ? AND factor_name = ?
                AND date BETWEEN ? AND ?
                ORDER BY date
            """
            
            df = pd.read_sql(query, conn, params=[symbol, factor_name, start_date, end_date])
            
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')['factor_value']
            
            return df
    
    # ========== 因子绩效操作 ==========
    
    def save_factor_performance(self, perf_data: Dict[str, Any]) -> int:
        """
        保存因子绩效数据
        
        Args:
            perf_data: 绩效数据字典
        """
        with self.db.connection() as conn:
            conn.execute("""
                INSERT INTO factor_performance 
                (factor_name, calculation_date, ic, ic_ir, ic_sign_ratio, 
                 turnover, group_return_q1, group_return_q5, spread_return,
                 sharpe_q1, sharpe_q5)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                perf_data['factor_name'],
                perf_data['calculation_date'],
                perf_data['ic'],
                perf_data['ic_ir'],
                perf_data['ic_sign_ratio'],
                perf_data['turnover'],
                perf_data['group_return_q1'],
                perf_data['group_return_q5'],
                perf_data['spread_return'],
                perf_data['sharpe_q1'],
                perf_data['sharpe_q5']
            ))
            conn.commit()
        
        return 1
    
    def get_factor_performance_history(self, factor_name: str, 
                                       days: int = 30) -> pd.DataFrame:
        """
        获取因子绩效历史
        
        Args:
            factor_name: 因子名称
            days: 天数
            
        Returns:
            绩效历史数据
        """
        with self.db.connection() as conn:
            query = """
                SELECT * FROM factor_performance
                WHERE factor_name = ?
                ORDER BY calculation_date DESC
                LIMIT ?
            """
            
            df = pd.read_sql(query, conn, params=[factor_name, days])
            
            if not df.empty:
                df['calculation_date'] = pd.to_datetime(df['calculation_date'])
            
            return df
    
    # ========== 系统状态操作 ==========
    
    def update_system_status(self, update_type: str, status: str,
                            records: int = 0, error: str = None):
        """
        更新系统状态
        
        Args:
            update_type: 更新类型 (price, fundamental, factor, backtest)
            status: 状态 (success, failed, running)
            records: 更新的记录数
            error: 错误信息
        """
        with self.db.connection() as conn:
            conn.execute("""
                INSERT INTO system_status (update_type, last_update, status, records_updated, error_message)
                VALUES (?, ?, ?, ?, ?)
            """, (
                update_type,
                datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                status,
                records,
                error
            ))
            conn.commit()
    
    def get_last_update_status(self, update_type: str) -> Dict:
        """
        获取上次更新状态
        """
        with self.db.connection() as conn:
            result = conn.execute("""
                SELECT * FROM system_status
                WHERE update_type = ?
                ORDER BY id DESC LIMIT 1
            """, [update_type]).fetchone()
            
            if result:
                return {
                    'update_type': result[1],
                    'last_update': result[2],
                    'status': result[3],
                    'records_updated': result[4],
                    'error_message': result[5]
                }
            
            return None


class AutoDataUpdater:
    """
    自动数据更新器
    
    功能：
    - 每日自动拉取最新数据
    - 增量更新
    - 更新状态追踪
    """
    
    def __init__(self, repo: DataRepository = None):
        """
        初始化
        
        Args:
            repo: 数据仓库实例
        """
        self.repo = repo or DataRepository()
        self.data_source = MultiSourceDataManager()
    
    def update_price_data(self, symbols: List[str] = None) -> Dict:
        """
        更新价格数据
        
        Args:
            symbols: 股票代码列表，如果为None则更新所有
            
        Returns:
            更新结果
        """
        logger.info("开始更新价格数据...")
        
        result = {
            'status': 'running',
            'records_updated': 0,
            'error': None
        }
        
        try:
            # 确定更新范围
            if symbols is None:
                # 获取所有已有股票
                with self.repo.db.connection() as conn:
                    symbols = [s[0] for s in conn.execute("SELECT DISTINCT symbol FROM price_data").fetchall()]
            
            if not symbols:
                logger.warning("没有股票代码，跳过价格更新")
                result['status'] = 'skipped'
                return result
            
            # 获取需要更新的日期范围
            start_date, end_date = self.repo.get_price_update_range(symbols)
            
            logger.info(f"更新范围: {start_date} ~ {end_date}, 股票数: {len(symbols)}")
            
            # 获取新数据
            total_records = 0
            
            for symbol in symbols:
                try:
                    if 'akshare' in self.repo.data_source.sources:
                        data = self.repo.data_source.sources['akshare'].get_price(
                            [symbol], start_date, end_date, 'qfq'
                        )
                        
                        if not data.empty:
                            records = self.repo.save_price_data(data)
                            total_records += records
                            
                except Exception as e:
                    logger.debug(f"获取 {symbol} 数据失败: {e}")
                    continue
            
            result['status'] = 'success'
            result['records_updated'] = total_records
            result['date_range'] = f"{start_date} ~ {end_date}"
            
            logger.info(f"价格数据更新完成: {total_records} 条记录")
            
        except Exception as e:
            logger.error(f"更新价格数据失败: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
        
        # 更新状态
        self.repo.update_system_status('price', result['status'], 
                                       result['records_updated'], result['error'])
        
        return result
    
    def update_fundamental_data(self, symbols: List[str] = None) -> Dict:
        """
        更新财务数据
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            更新结果
        """
        logger.info("开始更新财务数据...")
        
        result = {
            'status': 'running',
            'records_updated': 0,
            'error': None
        }
        
        try:
            if symbols is None:
                with self.repo.db.connection() as conn:
                    symbols = [s[0] for s in conn.execute("SELECT DISTINCT symbol FROM price_data").fetchall()]
            
            if not symbols:
                result['status'] = 'skipped'
                return result
            
            # 财务数据通常是季度更新，使用最新日期
            latest_date = self.repo.get_latest_trade_date()
            
            if not latest_date:
                result['status'] = 'skipped'
                return result
            
            # 获取最新财务数据
            if 'akshare' in self.repo.data_source.sources:
                data = self.repo.data_source.sources['akshare'].get_fundamental(
                    symbols, ['all'], latest_date, latest_date
                )
                
                if not data.empty:
                    records = self.repo.save_fundamental_data(data)
                    result['records_updated'] = records
            
            result['status'] = 'success'
            logger.info(f"财务数据更新完成: {result['records_updated']} 条记录")
            
        except Exception as e:
            logger.error(f"更新财务数据失败: {e}")
            result['status'] = 'failed'
            result['error'] = str(e)
        
        self.repo.update_system_status('fundamental', result['status'],
                                       result['records_updated'], result['error'])
        
        return result
    
    def run_full_update(self, symbols: List[str] = None) -> Dict:
        """
        运行完整数据更新流程
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            更新结果汇总
        """
        logger.info("="*50)
        logger.info("开始完整数据更新流程")
        logger.info("="*50)
        
        results = {
            'price': self.update_price_data(symbols),
            'fundamental': self.update_fundamental_data(symbols)
        }
        
        # 检查整体状态
        all_success = all(r['status'] == 'success' for r in results.values())
        
        logger.info("="*50)
        logger.info(f"数据更新完成，整体状态: {'成功' if all_success else '部分失败'}")
        logger.info("="*50)
        
        return results
    
    def get_update_summary(self) -> Dict:
        """
        获取更新状态汇总
        """
        return {
            'price': self.repo.get_last_update_status('price'),
            'fundamental': self.repo.get_last_update_status('fundamental'),
            'factor': self.repo.get_last_update_status('factor'),
            'backtest': self.repo.get_last_update_status('backtest')
        }


if __name__ == "__main__":
    print("🧪 测试数据持久化模块...")
    
    # 创建仓库
    repo = DataRepository("./data/factor_data.db")
    
    # 测试更新
    updater = AutoDataUpdater(repo)
    
    # 查看更新状态
    summary = updater.get_update_summary()
    print("\n📊 更新状态:")
    for key, status in summary.items():
        if status:
            print(f"  {key}: {status['status']} - {status.get('last_update', 'N/A')}")
        else:
            print(f"  {key}: 暂无更新记录")
    
    print("\n💡 运行完整更新:")
    print("  updater.run_full_update(['000001', '600000'])")
