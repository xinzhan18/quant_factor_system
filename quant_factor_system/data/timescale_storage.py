"""
TimescaleDB 量化数据存储模块
Quant Data Storage with TimescaleDB

功能:
- 自动分区 (按周/月)
- 自动压缩 (7天后)
- 增量更新
- 数据生命周期管理

安装:
    # 方式1: Docker (推荐)
    docker run -d --name timescaledb \
      -p 5432:5432 \
      -e POSTGRES_PASSWORD=quant123 \
      timescale/timescaledb:latest-pg14
    
    # 方式2: 本地安装
    # Ubuntu: sudo apt install timescaledb-2-postgresql-14
    # Mac: brew install timescaledb
    
    # Python驱动
    pip install psycopg2-binary
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from contextlib import contextmanager
import logging
import json
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)


# ==================== 配置 ====================

TIMESCALE_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'quant_data',
    'user': 'postgres',
    'password': 'quant123',
}

# 分区配置
CHUNK_CONFIG = {
    'price_1min': '1 week',      # 1分钟数据按周分区
    'price_5min': '1 month',     # 5分钟数据按月分区
    'price_daily': '1 year',     # 日线数据按年分区
}

# 压缩策略 (多少天前的数据自动压缩)
COMPRESSION_POLICY = {
    'price_1min': '7 days',      # 1分钟数据: 7天后压缩
    'price_5min': '1 month',     # 5分钟数据: 1月后压缩
    'price_daily': '1 year',     # 日线数据: 1年后压缩
}


# ==================== 数据库连接 ====================

class TimescaleDB:
    """
    TimescaleDB 数据库连接器
    
    使用示例:
        db = TimescaleDB()
        
        # 查询
        df = db.query_price(
            symbols=['SH600000'],
            start_date='2024-01-01',
            end_date='2024-01-31',
            table='price_1min'
        )
        
        # 插入
        db.insert_price(df, table='price_1min')
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化连接
        
        Args:
            config: 数据库配置 (可选，默认使用TIMESCALE_CONFIG)
        """
        self.config = config or TIMESCALE_CONFIG.copy()
        self._conn = None
        self._pool = None
        self._check_connection()
    
    def _check_connection(self):
        """检查连接是否可用"""
        try:
            import psycopg2
            from psycopg2 import pool
            
            # 只传递有效的连接参数
            valid_params = {
                'host': self.config.get('host', 'localhost'),
                'port': self.config.get('port', 5432),
                'database': self.config.get('database', 'quant_data'),
                'user': self.config.get('user', 'postgres'),
                'password': self.config.get('password', ''),
            }
            
            # 创建连接池
            self._pool = pool.SimpleConnectionPool(
                minconn=1,
                maxconn=20,
                **valid_params
            )
            self._conn = self._pool.getconn()
            self._conn.autocommit = False
            logger.info(f"✅ TimescaleDB 连接成功: {valid_params['database']}")
        except ImportError:
            logger.warning("⚠️ psycopg2 未安装，将使用模拟模式")
            self._pool = None
            self._conn = None
        except Exception as e:
            logger.warning(f"⚠️ TimescaleDB 连接失败: {e}")
            logger.warning("   将使用模拟模式进行测试")
            self._pool = None
            self._conn = None
    
    @contextmanager
    def connection(self):
        """获取数据库连接"""
        if self._pool is None:
            # 模拟模式
            yield None
            return
        
        conn = None
        try:
            conn = self._pool.getconn()
            conn.autocommit = False
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                self._pool.putconn(conn)
    
    def close(self):
        """关闭连接"""
        if self._pool:
            self._pool.closeall()
            logger.info("✅ TimescaleDB 连接已关闭")
            raise e
    
    def close(self):
        """关闭连接"""
        if self._conn:
            self._conn.close()
    
    # ==================== 表管理 ====================
    
    def create_hypertable(self, table: str, chunk_time: str = None):
        """
        创建超表 (Hypertable)
        
        Args:
            table: 表名
            chunk_time: 分区间隔 (如 '1 week', '1 month')
        """
        if self._conn is None:
            logger.warning(f"⚠️ 模拟模式: 跳过创建超表 {table}")
            return
        
        chunk = chunk_time or CHUNK_CONFIG.get(table, '1 week')
        
        with self.connection() as conn:
            cursor = conn.cursor()
            
            # 创建表
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {table} (
                    time TIMESTAMP NOT NULL,
                    symbol TEXT NOT NULL,
                    open DOUBLE PRECISION,
                    high DOUBLE PRECISION,
                    low DOUBLE PRECISION,
                    close DOUBLE PRECISION,
                    volume DOUBLE PRECISION,
                    amount DOUBLE PRECISION,
                    vwap DOUBLE PRECISION,
                    UNIQUE(time, symbol)
                );
            """)
            
            # 转换为超表
            try:
                cursor.execute(f"""
                    SELECT create_hypertable('{table}', 'time', 
                        chunk_time_interval => INTERVAL '{chunk}');
                """)
                logger.info(f"✅ 超表 {table} 创建成功 (chunk: {chunk})")
            except Exception as e:
                if 'already a hypertable' in str(e):
                    logger.info(f"ℹ️ {table} 已是超表")
                else:
                    raise e
            
            # 开启压缩
            self._enable_compression(table, cursor)
    
    def _enable_compression(self, table: str, cursor):
        """开启压缩"""
        try:
            cursor.execute(f"""
                ALTER TABLE {table} SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'symbol'
                );
            """)
            
            # 添加压缩策略
            policy_days = COMPRESSION_POLICY.get(table, '7 days')
            cursor.execute(f"""
                SELECT add_compression_policy('{table}', INTERVAL '{policy_days}');
            """)
            
            logger.info(f"✅ {table} 压缩已开启 ({policy_days}后压缩)")
        except Exception as e:
            if 'already compressed' in str(e):
                logger.info(f"ℹ️ {table} 已启用压缩")
            else:
                logger.warning(f"⚠️ {table} 压缩设置失败: {e}")
    
    def create_all_tables(self):
        """创建所有表"""
        tables = ['price_1min', 'price_5min', 'price_daily']
        
        for table in tables:
            self.create_hypertable(table)
    
    # ==================== 数据操作 ====================
    
    def insert_price(
        self,
        df: pd.DataFrame,
        table: str = 'price_1min',
        if_exists: str = 'append'
    ) -> int:
        """
        插入价格数据
        
        Args:
            df: 价格数据 (需包含: time, symbol, open, high, low, close, volume)
            table: 表名
            if_exists: append/replace
            
        Returns:
            插入的记录数
        """
        if df.empty:
            return 0
        
        if self._conn is None:
            logger.info(f"⚠️ 模拟模式: 跳过插入 {len(df)} 条数据")
            return len(df)
        
        df = df.copy()
        
        # 标准化列名
        if 'date' in df.columns and 'time' not in df.columns:
            df['time'] = pd.to_datetime(df['date'])
        if 'symbol' not in df.columns:
            df['symbol'] = 'UNKNOWN'
        
        # 确保数值类型
        for col in ['open', 'high', 'low', 'close', 'volume', 'amount', 'vwap']:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        with self.connection() as conn:
            cursor = conn.cursor()
            
            records = 0
            
            # 批量插入
            batch_size = 10000
            
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                
                args_str = ','.join(cursor.mogrify(
                    "(%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                    (
                        row['time'], row['symbol'],
                        row.get('open', 0), row.get('high', 0),
                        row.get('low', 0), row.get('close', 0),
                        row.get('volume', 0), row.get('amount', 0),
                        row.get('vwap', 0)
                    )
                ).decode() for _, row in batch.iterrows())
                
                if if_exists == 'replace':
                    cursor.execute(f"DELETE FROM {table} WHERE time >= %s AND symbol IN %s",
                        (batch['time'].min(), tuple(batch['symbol'].unique())))
                
                cursor.execute(f"""
                    INSERT INTO {table} 
                    (time, symbol, open, high, low, close, volume, amount, vwap)
                    VALUES {args_str}
                    ON CONFLICT (time, symbol) DO NOTHING
                """)
                
                records += len(batch)
        
        logger.info(f"✅ 插入 {table}: {records} 条")
        return records
    
    def query_price(
        self,
        symbols: List[str] = None,
        start_time: str = None,
        end_time: str = None,
        table: str = 'price_1min',
        columns: List[str] = None
    ) -> pd.DataFrame:
        """
        查询价格数据
        
        Args:
            symbols: 股票代码列表
            start_time: 开始时间
            end_time: 结束时间
            table: 表名
            columns: 返回的列
            
        Returns:
            价格数据 DataFrame
        """
        if self._conn is None:
            logger.warning("⚠️ 模拟模式: 返回空数据")
            return pd.DataFrame()
        
        cols = ', '.join(columns) if columns else '*'
        
        query = f"SELECT {cols} FROM {table} WHERE 1=1"
        params = []
        
        if symbols:
            placeholders = ','.join(['%s'] * len(symbols))
            query += f" AND symbol IN ({placeholders})"
            params.extend(symbols)
        
        if start_time:
            query += " AND time >= %s"
            params.append(start_time)
        
        if end_time:
            query += " AND time < %s"
            params.append(end_time)
        
        query += " ORDER BY time, symbol LIMIT 10000000"
        
        with self.connection() as conn:
            df = pd.read_sql(query, conn, params=params)
        
        if not df.empty:
            df = df.set_index(['time', 'symbol']).sort_index()
        
        return df
    
    def query_daily(
        self,
        symbols: List[str] = None,
        start_date: str = None,
        end_date: str = None,
        table: str = 'price_daily'
    ) -> pd.DataFrame:
        """
        查询日线数据
        
        Args:
            symbols: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            table: 表名
            
        Returns:
            日线数据
        """
        # 转换日期为时间范围
        start_time = f"{start_date} 00:00:00" if start_date else None
        end_time = f"{end_date} 23:59:59" if end_date else None
        
        return self.query_price(
            symbols=symbols,
            start_time=start_time,
            end_time=end_time,
            table=table
        )
    
    # ==================== 因子操作 ====================
    
    def create_factor_table(self, name: str):
        """创建因子表"""
        if self._conn is None:
            return
        
        with self.connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS factor_{name} (
                    time TIMESTAMP NOT NULL,
                    symbol TEXT NOT NULL,
                    value DOUBLE PRECISION,
                    UNIQUE(time, symbol)
                );
            """)
            
            cursor.execute(f"""
                SELECT create_hypertable('factor_{name}', 'time',
                    chunk_time_interval => INTERVAL '1 month');
            """)
            
            cursor.execute(f"""
                ALTER TABLE factor_{name} SET (
                    timescaledb.compress,
                    timescaledb.compress_segmentby = 'symbol'
                );
            """)
            
            cursor.execute(f"""
                SELECT add_compression_policy('factor_{name}', INTERVAL '1 month');
            """)
    
    def insert_factor(
        self,
        df: pd.DataFrame,
        name: str,
        value_col: str = 'value'
    ) -> int:
        """插入因子数据"""
        if df.empty:
            return 0
        
        if self._conn is None:
            return len(df)
        
        df = df.copy()
        
        if 'time' not in df.columns:
            df['time'] = pd.to_datetime(df.index.get_level_values('date'))
        
        with self.connection() as conn:
            cursor = conn.cursor()
            
            for _, row in df.iterrows():
                cursor.execute(f"""
                    INSERT INTO factor_{name} (time, symbol, value)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (time, symbol) DO UPDATE SET value = EXCLUDED.value
                """, (row['time'], row.name[1] if isinstance(row.name, tuple) else row['symbol'], row[value_col]))
        
        return len(df)
    
    def query_factor(
        self,
        name: str,
        symbols: List[str] = None,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """查询因子数据"""
        if self._conn is None:
            return pd.DataFrame()
        
        query = f"SELECT time, symbol, value FROM factor_{name} WHERE 1=1"
        params = []
        
        if symbols:
            placeholders = ','.join(['%s'] * len(symbols))
            query += f" AND symbol IN ({placeholders})"
            params.extend(symbols)
        
        if start_date:
            query += " AND time >= %s"
            params.append(f"{start_date} 00:00:00")
        
        if end_date:
            query += " AND time < %s"
            params.append(f"{end_date} 23:59:59")
        
        with self.connection() as conn:
            df = pd.read_sql(query, conn, params=params)
        
        if not df.empty:
            df = df.pivot(index='time', columns='symbol', values='value')
        
        return df
    
    # ==================== 统计信息 ====================
    
    def get_stats(self) -> Dict:
        """获取数据库统计"""
        if self._conn is None:
            return {'status': '模拟模式'}
        
        stats = {}
        
        with self.connection() as conn:
            # 表大小
            cursor = conn.cursor()
            cursor.execute("""
                SELECT table_name, pg_size_pretty(pg_total_relation_size(table_name)) as size
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            
            tables = {}
            for row in cursor.fetchall():
                tables[row[0]] = row[1]
            stats['tables'] = tables
            
            # 记录数
            cursor.execute("""
                SELECT table_name, pg_total_relation_size(table_name)
                FROM information_schema.tables
                WHERE table_schema = 'public'
            """)
            
            total_size = sum(row[1] for row in cursor.fetchall())
            stats['total_size'] = f"{total_size / 1024 / 1024 / 1024:.2f} GB"
        
        return stats


# ==================== 数据管理 ====================

class QuantDataManager:
    """
    量化数据管理器
    
    整合米筐数据源 + TimescaleDB存储
    
    使用:
        manager = QuantDataManager()
        
        # 更新日线数据
        manager.update_daily()
        
        # 更新分钟数据
        manager.update_minute()
        
        # 查询
        df = manager.get_price('SH600000', '2024-01-01', '2024-01-31')
    """
    
    def __init__(self, db: TimescaleDB = None):
        """
        初始化
        
        Args:
            db: TimescaleDB实例
        """
        self.db = db or TimescaleDB()
    
    def initialize(self):
        """初始化数据库表"""
        logger.info("🔧 初始化数据库表...")
        
        # 创建价格表
        for table in ['price_1min', 'price_5min', 'price_daily']:
            self.db.create_hypertable(table)
        
        logger.info("✅ 数据库初始化完成")
    
    def update_daily(
        self,
        symbols: List[str] = None,
        start_date: str = None,
        end_date: str = None
    ) -> Dict:
        """
        更新日线数据
        
        Args:
            symbols: 股票列表 (None=全部)
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            更新统计
        """
        from quant_factor_system.data.ricequant_source import RiceQuantSource
        
        source = RiceQuantSource()
        
        # 获取日期范围
        if not start_date:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        # 获取全部股票
        if not symbols:
            symbols = source.get_all_symbols()
        
        logger.info(f"📥 获取日线数据: {len(symbols)} 只股票, {start_date} ~ {end_date}")
        
        # 获取数据
        data = source.get_daily_data(
            symbols=symbols[:100],  # 限制数量
            start_date=start_date,
            end_date=end_date
        )
        
        if data.empty:
            logger.warning("⚠️ 无数据返回")
            return {'status': 'no_data'}
        
        # 保存
        count = self.db.insert_price(data, table='price_daily')
        
        return {
            'status': 'success',
            'symbols': len(symbols),
            'records': count,
            'date_range': f"{start_date} ~ {end_date}"
        }
    
    def update_minute(
        self,
        symbols: List[str] = None,
        start_date: str = None,
        end_date: str = None,
        frequency: str = '1min'
    ) -> Dict:
        """
        更新分钟数据
        
        Args:
            symbols: 股票列表
            start_date: 开始日期
            end_date: 结束日期
            frequency: 频率 (1min/5min/15min)
        """
        from quant_factor_system.data.ricequant_source import RiceQuantSource
        
        source = RiceQuantSource()
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        if not symbols:
            symbols = source.get_all_symbols()[:100]
        
        logger.info(f"📥 获取{frequency}数据: {len(symbols)} 只股票")
        
        table_map = {
            '1min': 'price_1min',
            '5min': 'price_5min',
            '15min': 'price_5min'
        }
        
        data = source.get_minute_data(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency
        )
        
        if data.empty:
            return {'status': 'no_data'}
        
        count = self.db.insert_price(data, table=table_map.get(frequency, 'price_1min'))
        
        return {
            'status': 'success',
            'records': count,
            'frequency': frequency
        }
    
    def get_price(
        self,
        symbols: List[str] = None,
        start_date: str = None,
        end_date: str = None,
        frequency: str = 'daily'
    ) -> pd.DataFrame:
        """获取价格数据"""
        table_map = {
            'daily': 'price_daily',
            '1min': 'price_1min',
            '5min': 'price_5min'
        }
        
        return self.db.query_daily(
            symbols=symbols,
            start_date=start_date,
            end_date=end_date,
            table=table_map.get(frequency, 'price_daily')
        )
    
    def run_full_update(self):
        """运行完整更新"""
        logger.info("🚀 开始完整数据更新...")
        
        results = {
            'daily': self.update_daily(),
            'minute_1min': self.update_minute(frequency='1min'),
            'minute_5min': self.update_minute(frequency='5min')
        }
        
        stats = self.db.get_stats()
        logger.info(f"📊 数据库统计: {stats}")
        
        return results


# ==================== 便捷函数 ====================

def get_timescaledb(config: Dict = None) -> TimescaleDB:
    """获取TimescaleDB实例"""
    return TimescaleDB(config)


def init_quant_db(config: Dict = None) -> QuantDataManager:
    """初始化量化数据库"""
    manager = QuantDataManager(TimescaleDB(config))
    manager.initialize()
    return manager


# ==================== 导出 ====================

__all__ = [
    'TimescaleDB',
    'QuantDataManager',
    'TIMESCALE_CONFIG',
    'CHUNK_CONFIG',
    'COMPRESSION_POLICY',
    'get_timescaledb',
    'init_quant_db',
]
