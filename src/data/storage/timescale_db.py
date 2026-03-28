"""
TimescaleDB 量化因子数据存储
============================

基于 TimescaleDB 的统一时序数据库:
1. 所有频率数据存在统一表
2. TimescaleDB 自动分区和压缩
3. Continuous Aggregates 自动维护聚合视图
4. 按需查询原始数据或聚合数据

安装:
    # Docker 启动
    docker run -d \
      --name timescaledb \
      -p 5432:5432 \
      -e POSTGRES_PASSWORD=postgres \
      timescale/timescaledb:latest-pg16
    
    # 创建数据库
    psql -U postgres -c "CREATE DATABASE quant;"

依赖:
    pip install sqlalchemy psycopg2-binary pandas numpy
"""

import pandas as pd
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, 
    Index, CheckConstraint, UniqueConstraint, text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
import logging

logger = logging.getLogger(__name__)
Base = declarative_base()


# ==================== 支持的频率 ====================

class Frequency:
    """频率常量"""
    TICK = 'tick'
    MINUTE_1 = '1min'
    MINUTE_5 = '5min'
    MINUTE_15 = '15min'
    MINUTE_30 = '30min'
    HOUR_1 = '1hour'
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    
    # 可聚合的频率 (从1min聚合)
    AGGREGATABLE = [MINUTE_5, MINUTE_15, MINUTE_30, HOUR_1, DAILY, WEEKLY, MONTHLY]


# ==================== 数据模型 ====================

class UnifiedPriceData(Base):
    """
    统一价格数据表
    
    特点:
    - 所有频率数据存在一个表
    - TimescaleDB 自动按时间分区
    - 支持压缩
    """
    
    __tablename__ = 'unified_price_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False, comment="股票代码")
    timestamp = Column(DateTime, nullable=False, comment="时间戳")
    frequency = Column(String(20), nullable=False, comment="频率")
    
    # OHLCV
    open_price = Column(Float, comment="开盘价")
    high_price = Column(Float, comment="最高价")
    low_price = Column(Float, comment="最低价")
    close_price = Column(Float, nullable=False, comment="收盘价")
    volume = Column(Float, comment="成交量")
    amount = Column(Float, comment="成交额")
    
    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', 'frequency', 
                        name='uix_price_symbol_timestamp_freq'),
        Index('ix_price_freq_time', 'frequency', 'timestamp'),
        Index('ix_price_symbol_freq', 'symbol', 'frequency'),
        CheckConstraint(
            "frequency IN ('tick', '1min', '5min', '15min', '30min', '1hour', 'daily', 'weekly', 'monthly')",
            name='ck_price_frequency'
        ),
        {'schema': 'public'}
    )


class UnifiedFactorData(Base):
    """统一因子数据表"""
    
    __tablename__ = 'unified_factor_data'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    frequency = Column(String(20), nullable=False)
    factor_name = Column(String(50), nullable=False)
    factor_value = Column(Float)
    
    __table_args__ = (
        UniqueConstraint('symbol', 'timestamp', 'frequency', 'factor_name',
                        name='uix_factor_symbol_timestamp_freq_name'),
        Index('ix_factor_freq_time', 'frequency', 'timestamp'),
        {'schema': 'public'}
    )


# ==================== 连接管理 ====================

class TimescaleDB:
    """
    TimescaleDB 管理器
    
    功能:
    - 连接池管理
    - 初始化数据库
    - 创建自动聚合视图
    - 数据读写
    """
    
    _instance = None
    _engine = None
    
    def __new__(cls, connection_string: str = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, connection_string: str = None):
        if self._initialized:
            return
        
        # 默认连接
        if connection_string is None:
            connection_string = (
                "postgresql://postgres:quant123@localhost:5432/quant_data"
            )
        
        self.connection_string = connection_string
        
        # 引擎
        self._engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
            echo=False,
            pool_pre_ping=True
        )
        
        self._session_factory = scoped_session(
            sessionmaker(bind=self._engine)
        )
        
        self._initialized = True
        logger.info(f"TimescaleDB: {connection_string.split('@')[1]}")
    
    # ==================== 连接管理 ====================
    
    @contextmanager
    def session(self):
        """获取数据库会话"""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def check(self) -> Dict[str, Any]:
        """检查连接"""
        try:
            with self.session() as s:
                version = s.execute(text("SELECT version()")).fetchone()[0]
                ts = s.execute(text(
                    "SELECT extname FROM pg_extension WHERE extname = 'timescaledb'"
                )).fetchone()
                
                return {
                    'connected': True,
                    'version': version[:50],
                    'timescaledb': ts is not None,
                    'message': 'OK' if ts else 'TimescaleDB未安装'
                }
        except Exception as e:
            return {
                'connected': False, 
                'timescaledb': False,
                'message': str(e)
            }
    
    def close(self):
        """关闭连接"""
        if self._session_factory:
            self._session_factory.remove()
        if self._engine:
            self._engine.dispose()
    
    # ==================== 初始化 ====================
    
    def init(self):
        """初始化数据库"""
        logger.info("初始化数据库...")
        
        try:
            with self.session() as s:
                # 检查是否有 TimescaleDB 扩展
                ts = s.execute(text(
                    "SELECT extname FROM pg_extension WHERE extname = 'timescaledb'"
                )).fetchone()
                
                if ts:
                    # TimescaleDB 扩展存在，创建 Hypertable
                    s.execute(text("CREATE EXTENSION IF NOT EXISTS timescaledb"))
                    s.commit()
                    
                    # 表
                    Base.metadata.create_all(self._engine)
                    logger.info("✅ 表创建完成 (TimescaleDB)")
                    
                    # Hypertable
                    self._convert_to_hypertable()
                else:
                    # 普通 PostgreSQL，只创建普通表
                    logger.info("⚠️  TimescaleDB 未安装，创建普通表")
                    
                    # 移除 TimescaleDB 特定的表参数
                    for table in [UnifiedPriceData, UnifiedFactorData]:
                        table.__table_args__ = tuple(
                            ta for ta in table.__table_args__ 
                            if not isinstance(ta, dict) or 'schema' not in ta
                        )
                    
                    # 移除 CheckConstraint（因为频率检查可能不兼容）
                    Base.metadata.create_all(self._engine, checkfirst=True)
                    logger.info("✅ 普通表创建完成")
                    
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    def _convert_to_hypertable(self):
        """转换为Hypertable"""
        tables = ['unified_price_data', 'unified_factor_data']
        
        for table in tables:
            try:
                with self.session() as s:
                    s.execute(text(f"SELECT create_hypertable('{table}', 'timestamp')"))
                    s.commit()
                    logger.info(f"✅ {table} -> Hypertable")
            except Exception as e:
                if "already a hypertable" in str(e):
                    logger.info(f"⏭️ {table} 已是Hypertable")
    
    # ==================== Continuous Aggregates ====================
    
    def setup_continuous_aggregates(self):
        """设置自动聚合视图"""
        logger.info("设置自动聚合视图...")
        
        with self.session() as s:
            # 5分钟聚合
            s.execute(text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS agg_5min
                WITH (timescaledb.continuous) AS
                SELECT
                    symbol,
                    time_bucket('5 min', timestamp) AS timestamp,
                    frequency,
                    FIRST(open_price, timestamp) AS open_price,
                    MAX(high_price) AS high_price,
                    MIN(low_price) AS low_price,
                    LAST(close_price, timestamp) AS close_price,
                    SUM(volume) AS volume,
                    SUM(amount) AS amount
                FROM unified_price_data
                WHERE frequency = '1min'
                GROUP BY symbol, time_bucket('5 min', timestamp), frequency
            """))
            
            # 日线聚合
            s.execute(text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS agg_daily
                WITH (timescaledb.continuous) AS
                SELECT
                    symbol,
                    time_bucket('1 day', timestamp) AS timestamp,
                    frequency,
                    FIRST(open_price, timestamp) AS open_price,
                    MAX(high_price) AS high_price,
                    MIN(low_price) AS low_price,
                    LAST(close_price, timestamp) AS close_price,
                    SUM(volume) AS volume,
                    SUM(amount) AS amount
                FROM unified_price_data
                WHERE frequency = '1min'
                GROUP BY symbol, time_bucket('1 day', timestamp), frequency
            """))
            
            # 周线聚合
            s.execute(text("""
                CREATE MATERIALIZED VIEW IF NOT EXISTS agg_weekly
                WITH (timescaledb.continuous) AS
                SELECT
                    symbol,
                    time_bucket('1 week', timestamp) AS timestamp,
                    frequency,
                    FIRST(open_price, timestamp) AS open_price,
                    MAX(high_price) AS high_price,
                    MIN(low_price) AS low_price,
                    LAST(close_price, timestamp) AS close_price,
                    SUM(volume) AS volume,
                    SUM(amount) AS amount
                FROM unified_price_data
                WHERE frequency = '1min'
                GROUP BY symbol, time_bucket('1 week', timestamp), frequency
            """))
            
            s.commit()
            logger.info("✅ 聚合视图创建完成")
        
        # 设置自动刷新策略
        self._setup_refresh_policy()
    
    def _setup_refresh_policy(self):
        """设置自动刷新策略"""
        with self.session() as s:
            for view in ['agg_5min', 'agg_daily', 'agg_weekly']:
                try:
                    s.execute(text(f"""
                        SELECT add_continuous_aggregate_policy('{view}',
                            start_offset => INTERVAL '1 hour',
                            end_offset => INTERVAL '1 minute',
                            schedule_interval => INTERVAL '1 hour')
                    """))
                except Exception as e:
                    logger.warning(f"刷新策略设置跳过: {view}: {e}")
            
            s.commit()
        
        logger.info("✅ 刷新策略设置完成")
    
    # ==================== 数据写入 ====================
    
    def insert_price(
        self,
        df: pd.DataFrame,
        frequency: str = '1min',
        upsert: bool = True
    ) -> int:
        """
        写入价格数据
        
        Args:
            df: DataFrame (必须包含: symbol, timestamp, close)
            frequency: 数据频率
            upsert: 是否更新已存在数据
            
        Returns:
            写入行数
        """
        if df.empty:
            return 0
        
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['frequency'] = frequency
        
        # 重命名列
        rename = {
            'open': 'open_price',
            'high': 'high_price',
            'low': 'low_price',
            'close': 'close_price'
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        
        records = df.to_dict('records')
        records = [{k: v for k, v in r.items() if v is not None} for r in records]
        
        sql = text("""
            INSERT INTO unified_price_data 
            (symbol, timestamp, frequency, open_price, high_price, low_price, close_price, volume, amount)
            VALUES 
            (:symbol, :timestamp, :frequency, :open_price, :high_price, :low_price, :close_price, :volume, :amount)
            ON CONFLICT (symbol, timestamp, frequency) 
        """)
        
        if upsert:
            sql += """
                DO UPDATE SET 
                    open_price = EXCLUDED.open_price,
                    high_price = EXCLUDED.high_price,
                    low_price = EXCLUDED.low_price,
                    close_price = EXCLUDED.close_price,
                    volume = EXCLUDED.volume,
                    amount = EXCLUDED.amount
            """
        else:
            sql += " DO NOTHING"
        
        with self.session() as s:
            s.execute(sql, records)
        
        logger.info(f"写入 {frequency}: {len(records)} 行")
        return len(records)
    
    def insert_factor(
        self,
        df: pd.DataFrame,
        frequency: str = 'daily',
        upsert: bool = True
    ) -> int:
        """写入因子数据"""
        if df.empty:
            return 0
        
        df = df.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['frequency'] = frequency
        
        records = df.to_dict('records')
        
        sql = text("""
            INSERT INTO unified_factor_data 
            (symbol, timestamp, frequency, factor_name, factor_value)
            VALUES 
            (:symbol, :timestamp, :frequency, :factor_name, :factor_value)
            ON CONFLICT (symbol, timestamp, frequency, factor_name) 
        """)
        
        if upsert:
            sql += " DO UPDATE SET factor_value = EXCLUDED.factor_value"
        else:
            sql += " DO NOTHING"
        
        with self.session() as s:
            s.execute(sql, records)
        
        logger.info(f"写入因子 {frequency}: {len(records)} 行")
        return len(records)
    
    # ==================== 数据查询 ====================
    
    def query_price(
        self,
        symbols: Union[str, List[str]] = None,
        frequency: str = '1min',
        start: Union[str, datetime] = None,
        end: Union[str, datetime] = None,
        limit: int = None,
        use_aggregate: bool = False
    ) -> pd.DataFrame:
        """
        查询价格数据
        
        Args:
            symbols: 股票代码
            frequency: 频率 (原始数据)
            start: 开始时间
            end: 结束时间
            limit: 最大行数
            use_aggregate: 是否使用聚合视图 (更快)
            
        Returns:
            DataFrame
        """
        # 如果是聚合频率，使用聚合视图
        if use_aggregate and frequency in ['5min', 'daily', 'weekly']:
            table = f'agg_{frequency}'
        else:
            table = 'unified_price_data'
        
        sql = f"SELECT * FROM {table} WHERE frequency = :freq"
        params = {'freq': frequency}
        
        if symbols:
            if isinstance(symbols, str):
                symbols = [symbols]
            placeholders = ','.join([f":sym_{i}" for i in range(len(symbols))])
            sql += f" AND symbol IN ({placeholders})"
            params.update({f"sym_{i}": s for i, s in enumerate(symbols)})
        
        if start:
            sql += " AND timestamp >= :start"
            params['start'] = pd.to_datetime(start)
        
        if end:
            sql += " AND timestamp <= :end"
            params['end'] = pd.to_datetime(end)
        
        sql += " ORDER BY symbol, timestamp"
        
        if limit:
            sql += f" LIMIT {limit}"
        
        df = pd.read_sql(sql, self._engine, params=params)
        
        # 重命名列
        rename = {
            'open_price': 'open',
            'high_price': 'high',
            'low_price': 'low',
            'close_price': 'close'
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        
        return df
    
    def query_factor(
        self,
        factor_names: Union[str, List[str]],
        symbols: Union[str, List[str]] = None,
        frequency: str = 'daily',
        start: Union[str, datetime] = None,
        end: Union[str, datetime] = None,
        limit: int = None,
        pivot: bool = False
    ) -> pd.DataFrame:
        """查询因子数据"""
        if isinstance(factor_names, str):
            factor_names = [factor_names]
        
        sql = """
            SELECT * FROM unified_factor_data 
            WHERE frequency = :freq AND factor_name IN ({})
        """.format(','.join([f":fac_{i}" for i in range(len(factor_names))]))
        
        params = {
            'freq': frequency,
            **{f"fac_{i}": f for i, f in enumerate(factor_names)}
        }
        
        if symbols:
            if isinstance(symbols, str):
                symbols = [symbols]
            placeholders = ','.join([f":sym_{i}" for i in range(len(symbols))])
            sql += f" AND symbol IN ({placeholders})"
            params.update({f"sym_{i}": s for i, s in enumerate(symbols)})
        
        if start:
            sql += " AND timestamp >= :start"
            params['start'] = pd.to_datetime(start)
        
        if end:
            sql += " AND timestamp <= :end"
            params['end'] = pd.to_datetime(end)
        
        sql += " ORDER BY symbol, timestamp"
        
        if limit:
            sql += f" LIMIT {limit}"
        
        df = pd.read_sql(sql, self._engine, params=params)
        
        if pivot and not df.empty:
            df = df.pivot_table(
                index=['symbol', 'timestamp'],
                columns='factor_name',
                values='factor_value',
                aggfunc='first'
            ).reset_index()
            df.columns.name = None
        
        return df
    
    # ==================== 统计 ====================
    
    def get_stats(self) -> Dict[str, int]:
        """获取各频率数据量"""
        with self.session() as s:
            result = s.execute(text("""
                SELECT frequency, COUNT(*) 
                FROM unified_price_data 
                GROUP BY frequency
            """)).fetchall()
        
        return {row[0]: row[1] for row in result}
    
    def get_aggregate_stats(self) -> Dict[str, int]:
        """获取聚合视图数据量"""
        stats = {}
        for agg in ['agg_5min', 'agg_daily', 'agg_weekly']:
            try:
                with self.session() as s:
                    count = s.execute(text(f"SELECT COUNT(*) FROM {agg}")).fetchone()[0]
                    stats[agg] = count
            except:
                pass
        return stats


# ==================== 便捷函数 ====================

# 单例实例
_db_instance: Optional[TimescaleDB] = None

def get_db(connection_string: str = None) -> TimescaleDB:
    """获取数据库单例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = TimescaleDB(connection_string)
    return _db_instance

def init_db(connection_string: str = None) -> TimescaleDB:
    """初始化数据库"""
    db = get_db(connection_string)
    db.init()
    db.setup_continuous_aggregates()
    return db


# ==================== 导出 ====================

__all__ = [
    'TimescaleDB',
    'Frequency',
    'get_db',
    'init_db',
    'UnifiedPriceData',
    'UnifiedFactorData',
]
