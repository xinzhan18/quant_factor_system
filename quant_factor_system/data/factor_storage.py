"""
PostgreSQL 因子存储管理器
支持高频/低频因子，宽表/窄表存储，按时间分区
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from contextlib import contextmanager
import logging
import os

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, DateTime, Date,
    Text, UniqueConstraint, BigInteger, Index, PrimaryKeyConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy import text, inspect, event
from sqlalchemy.engine import Engine

logger = logging.getLogger(__name__)
Base = declarative_base()


# ==================== 因子配置表 ====================

class FactorConfig(Base):
    """因子配置表"""
    __tablename__ = 'factor_config'
    
    name = Column(String(100), primary_key=True)
    display_name = Column(String(200))
    category = Column(String(50))  # tech, return, volatility, etc.
    frequency = Column(String(20), nullable=False)  # minute, daily, weekly, monthly
    storage_type = Column(String(20), nullable=False)  # wide, narrow
    description = Column(Text)
    unit = Column(String(50))  # percent, price, ratio, etc.
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)


# ==================== 窄表模型（高频因子） ====================

def create_narrow_table_class(base: Any, table_suffix: str) -> Any:
    """动态创建窄表模型"""
    
    class NarrowFactor(Base):
        __tablename__ = f'factor_values_{table_suffix}'
        __table_args__ = (
            PrimaryKeyConstraint('factor_name', 'symbol', 'timestamp'),
            {'schema': None}
        )
        
        id = Column(BigInteger, autoincrement=True)
        factor_name = Column(String(100), nullable=False)
        symbol = Column(String(20), nullable=False)
        timestamp = Column(DateTime, nullable=False)
        factor_value = Column(Float)
        ic = Column(Float)  # 信息系数
        created_at = Column(DateTime, default=datetime.now)
        
        def __repr__(self):
            return f"<{self.__tablename__}({self.factor_name}, {self.symbol}, {self.timestamp})>"
    
    return NarrowFactor


# ==================== 宽表模型（低频因子） ====================

class DailyFactorWide(Base):
    """日级因子宽表 - 每天每只股票一行，多个因子作为列"""
    __tablename__ = 'daily_factors_wide'
    
    symbol = Column(String(20), nullable=False, primary_key=True)
    date = Column(Date, nullable=False, primary_key=True)
    
    # 动量因子
    momentum_5d = Column(Float)
    momentum_10d = Column(Float)
    momentum_20d = Column(Float)
    momentum_60d = Column(Float)
    
    # 收益率因子
    return_1d = Column(Float)
    return_5d = Column(Float)
    return_10d = Column(Float)
    return_20d = Column(Float)
    return_60d = Column(Float)
    
    # 均线因子
    ma_5 = Column(Float)
    ma_10 = Column(Float)
    ma_20 = Column(Float)
    ma_60 = Column(Float)
    
    # 偏离度因子
    dist_ma10 = Column(Float)  # 价格偏离10日均线
    dist_ma20 = Column(Float)  # 价格偏离20日均线
    
    # 技术指标
    rsi_14 = Column(Float)
    zscore_60 = Column(Float)
    volatility_20d = Column(Float)
    
    # 质量因子（可选扩展）
    turnover_ratio = Column(Float)  # 换手率
    
    # 元数据
    updated_at = Column(DateTime, default=datetime.now)


class WeeklyFactorWide(Base):
    """周级因子宽表"""
    __tablename__ = 'weekly_factors_wide'
    
    symbol = Column(String(20), nullable=False, primary_key=True)
    date = Column(Date, nullable=False, primary_key=True)  # 周收盘日
    
    # 动量
    momentum_4w = Column(Float)
    momentum_12w = Column(Float)
    momentum_26w = Column(Float)
    
    # 收益率
    return_1w = Column(Float)
    return_4w = Column(Float)
    return_12w = Column(Float)
    
    # 均线
    ma_10 = Column(Float)
    ma_20 = Column(Float)
    
    # 技术指标
    rsi_14 = Column(Float)
    zscore_60 = Column(Float)
    
    updated_at = Column(DateTime, default=datetime.now)


# ==================== 因子存储管理器 ====================

class FactorStorage:
    """
    PostgreSQL 因子存储管理器
    
    功能:
    - 支持高频/低频因子存储
    - 宽表（日级）+ 窄表（分钟级）
    - 按时间自动分区
    - 长期持久化存储
    """
    
    _instance = None
    
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
            connection_string = os.environ.get(
                'DATABASE_URL',
                "postgresql://postgres:postgres@localhost:5432/quant"
            )
        
        self.connection_string = connection_string
        
        # 引擎
        self._engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_recycle=3600,
            echo=False,
            pool_pre_ping=True
        )
        
        self._session_factory = scoped_session(
            sessionmaker(bind=self._engine))
        
        # 窄表模型字典
        self._narrow_models = {}
        
        self._initialized = True
        logger.info(f"FactorStorage: {connection_string.split('@')[1]}")
    
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
                
                return {
                    'connected': True,
                    'version': version[:50],
                    'type': 'postgresql'
                }
        except Exception as e:
            return {
                'connected': False,
                'message': str(e),
                'type': 'postgresql'
            }
    
    def close(self):
        """关闭连接"""
        if self._session_factory:
            self._session_factory.remove()
        if self._engine:
            self._engine.dispose()
    
    # ==================== 初始化 ====================
    
    def init(self):
        """初始化数据库表结构"""
        try:
            # 创建配置表
            Base.metadata.create_all(self._engine, tables=[FactorConfig.__table__])
            
            # 创建宽表
            Base.metadata.create_all(self._engine, tables=[DailyFactorWide.__table__])
            Base.metadata.create_all(self._engine, tables=[WeeklyFactorWide.__table__])
            
            # 创建唯一约束 (防止重复插入)
            self._create_unique_constraints()
            
            # 创建分钟因子窄表（分区表）
            self._create_minute_partitions()
            
            logger.info("✅ FactorStorage 初始化完成")
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    def _create_unique_constraints(self):
        """创建唯一约束"""
        conn = self._engine.connect()
        
        try:
            # DailyFactorWide 表的唯一约束
            conn.execute(text("""
                ALTER TABLE daily_factors_wide 
                DROP CONSTRAINT IF EXISTS uq_daily_factor_symbol_date;
            """))
            
            conn.execute(text("""
                ALTER TABLE daily_factors_wide 
                ADD CONSTRAINT uq_daily_factor_symbol_date 
                UNIQUE (symbol, date);
            """))
            
            logger.info("✅ 创建唯一约束: daily_factors_wide(symbol, date)")
            
        except Exception as e:
            if "already exists" in str(e) or "duplicate" in str(e):
                logger.info("唯一约束已存在")
            else:
                logger.warning(f"创建唯一约束失败: {e}")
        finally:
            conn.close()
    
    def _create_minute_partitions(self):
        """创建分钟因子分区表"""
        conn = self._engine.connect()
        
        # 主表
        create_sql = """
        CREATE TABLE IF NOT EXISTS minute_factor_values (
            id BIGSERIAL,
            factor_name VARCHAR(100) NOT NULL,
            symbol VARCHAR(20) NOT NULL,
            timestamp TIMESTAMP NOT NULL,
            factor_value FLOAT,
            ic FLOAT,
            created_at TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (factor_name, symbol, timestamp)
        ) PARTITION BY RANGE (timestamp);
        """
        
        try:
            conn.execute(text(create_sql))
            logger.info("分钟因子主表创建成功")
        except Exception as e:
            if "already exists" in str(e):
                logger.info("分钟因子主表已存在")
            else:
                raise e
        finally:
            conn.close()
    
    def create_minute_partition(self, year: int, month: int):
        """为指定月份创建分区"""
        conn = self._engine.connect()
        
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year+1}-01-01"
        else:
            end_date = f"{year}-{month+1:02d}-01"
        
        partition_name = f"minute_factor_values_{year}_{month:02d}"
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {partition_name} 
        PARTITION OF minute_factor_values
        FOR VALUES FROM ('{start_date}') TO ('{end_date}');
        """
        
        index_sql = f"""
        CREATE INDEX IF NOT EXISTS idx_{partition_name}_symbol 
        ON {partition_name} (symbol, timestamp DESC);
        """
        
        try:
            conn.execute(text(create_sql))
            conn.execute(text(index_sql))
            logger.info(f"✅ 创建分区: {partition_name}")
        except Exception as e:
            if "already exists" in str(e):
                logger.info(f"分区已存在: {partition_name}")
            else:
                raise e
        finally:
            conn.close()
    
    def auto_create_partitions(self, months_ahead: int = 3):
        """自动创建未来月份的分区"""
        conn = self._engine.connect()
        
        # 检查现有分区
        check_sql = """
        SELECT child.relname AS partition_name
        FROM pg_inherits
        JOIN pg_class parent ON pg_inherits.inhparent = parent.oid
        JOIN pg_class child ON pg_inherits.inhrelid = child.oid
        WHERE parent.relname = 'minute_factor_values';
        """
        
        try:
            result = conn.execute(text(check_sql)).fetchall()
            existing = [row[0] for row in result]
        except:
            existing = []
        
        now = datetime.now()
        
        # 创建缺失的分区
        for i in range(months_ahead):
            year = (now.month + i - 1) // 12 + now.year if now.month + i > 12 else now.year
            month = (now.month + i - 1) % 12 + 1
            
            partition_name = f"minute_factor_values_{year}_{month:02d}"
            
            if partition_name not in existing:
                self.create_minute_partition(year, month)
        
        conn.close()
    
    # ==================== 因子配置管理 ====================
    
    def register_factor(
        self,
        name: str,
        frequency: str,
        storage_type: str,
        display_name: str = None,
        category: str = None,
        description: str = None,
        unit: str = None
    ):
        """注册因子配置"""
        with self.session() as s:
            config = FactorConfig(
                name=name,
                display_name=display_name or name,
                category=category or 'custom',
                frequency=frequency,
                storage_type=storage_type,
                description=description,
                unit=unit
            )
            s.merge(config)  # upsert
        logger.info(f"✅ 注册因子: {name} ({frequency}, {storage_type})")
    
    def get_factor_config(self, name: str) -> Optional[Dict]:
        """获取因子配置"""
        with self.session() as s:
            result = s.execute(
                text("SELECT * FROM factor_config WHERE name = :name"),
                {'name': name}
            ).fetchone()
            
            if result:
                return {
                    'name': result[0],
                    'display_name': result[1],
                    'category': result[2],
                    'frequency': result[3],
                    'storage_type': result[4],
                    'description': result[5],
                    'unit': result[6]
                }
        return None
    
    def list_factors(self, frequency: str = None) -> List[Dict]:
        """列出因子配置"""
        with self.session() as s:
            sql = "SELECT * FROM factor_config"
            params = {}
            
            if frequency:
                sql += " WHERE frequency = :frequency"
                params['frequency'] = frequency
            
            results = s.execute(text(sql), params).fetchall()
            
            return [
                {
                    'name': r[0],
                    'display_name': r[1],
                    'category': r[2],
                    'frequency': r[3],
                    'storage_type': r[4],
                    'description': r[5],
                    'unit': r[6]
                }
                for r in results
            ]
    
    # ==================== 数据存储 - 窄表（分钟级） ====================
    
    def save_minute_factor(
        self,
        factor_name: str,
        df: pd.DataFrame,
        ic: float = None
    ):
        """保存分钟因子数据（窄表）"""
        if df.empty:
            return
        
        # 确保时间戳列存在
        if 'timestamp' not in df.columns:
            if 'datetime' in df.columns:
                df = df.rename(columns={'datetime': 'timestamp'})
            else:
                df['timestamp'] = datetime.now()
        
        df = df.copy()
        df['factor_name'] = factor_name
        df['ic'] = ic
        
        # 写入数据库
        df.to_sql(
            'minute_factor_values',
            self._engine,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=1000
        )
        
        logger.info(f"✅ 保存分钟因子: {factor_name}, {len(df)} 行")
    
    def query_minute_factor(
        self,
        factor_name: str,
        symbols: List[str] = None,
        start: datetime = None,
        end: datetime = None,
        limit: int = 100000
    ) -> pd.DataFrame:
        """查询分钟因子数据"""
        sql = "SELECT * FROM minute_factor_values WHERE factor_name = :factor_name"
        params = {'factor_name': factor_name, 'limit': limit}
        
        if symbols:
            sql += " AND symbol = ANY(:symbols)"
            params['symbols'] = symbols
        
        if start:
            sql += " AND timestamp >= :start"
            params['start'] = start
        
        if end:
            sql += " AND timestamp <= :end"
            params['end'] = end
        
        sql += " ORDER BY timestamp DESC LIMIT :limit"
        
        return pd.read_sql(sql, self._engine, params=params)
    
    # ==================== 数据存储 - 宽表（日级） ====================
    
    def save_daily_factor(
        self,
        df: pd.DataFrame,
        factor_columns: List[str] = None,
        append_only: bool = True
    ):
        """
        保存日级因子数据
        
        Args:
            df: 因子数据
            factor_columns: 因子列
            append_only: 是否只新增不更新 (默认True)
        """
        if df.empty:
            return
        
        if append_only:
            self._save_daily_factor_append_only(df, factor_columns)
        else:
            self._save_daily_factor_upsert(df, factor_columns)
    
    def _save_daily_factor_append_only(
        self,
        df: pd.DataFrame,
        factor_columns: List[str] = None
    ):
        """
        保存日级因子数据 (APPEND ONLY - 不允许覆盖)
        
        Raises:
            ValueError: 如果数据已存在
        """
        df = df.copy()
        
        # 确保必要列存在
        if 'date' not in df.columns:
            if 'timestamp' in df.columns:
                df['date'] = df['timestamp'].dt.date
            else:
                df['date'] = datetime.now().date()
        
        # 只保留需要的列
        if factor_columns:
            cols = ['symbol', 'date'] + factor_columns
            df = df[[c for c in cols if c in df.columns]]
        
        # 检查是否存在
        for _, row in df.iterrows():
            if self._exists_daily_factor(
                row.get('symbol'),
                row.get('date')
            ):
                raise ValueError(
                    f"因子值已存在，禁止覆盖: symbol={row.get('symbol')}, date={row.get('date')}"
                )
        
        # 批量插入
        df.to_sql(
            'daily_factors_wide',
            self._engine,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=1000
        )
        
        logger.info(f"✅ 保存日级因子 (APPEND ONLY): {len(df)} 行")
    
    def _save_daily_factor_upsert(
        self,
        df: pd.DataFrame,
        factor_columns: List[str] = None
    ):
        """
        保存日级因子数据 (UPSERT - 允许更新)
        """
        df = df.copy()
        
        # 确保必要列存在
        if 'date' not in df.columns:
            if 'timestamp' in df.columns:
                df['date'] = df['timestamp'].dt.date
            else:
                df['date'] = datetime.now().date()
        
        # 只保留需要的列
        if factor_columns:
            cols = ['symbol', 'date'] + factor_columns
            df = df[[c for c in cols if c in df.columns]]
        
        # 更新或插入
        for _, row in df.iterrows():
            self._upsert_daily_row(row)
        
        logger.info(f"✅ 保存日级因子 (UPSERT): {len(df)} 行")
    
    def _exists_daily_factor(self, symbol: str, date) -> bool:
        """
        检查日级因子是否已存在
        
        Args:
            symbol: 股票代码
            date: 日期
            
        Returns:
            bool: 是否存在
        """
        if symbol is None or date is None:
            return False
            
        try:
            with self.session() as s:
                result = s.execute(
                    text("""
                        SELECT 1 FROM daily_factors_wide 
                        WHERE symbol = :symbol AND date = :date
                        LIMIT 1
                    """),
                    {'symbol': symbol, 'date': date}
                ).fetchone()
                return result is not None
        except Exception:
            return False
    
    def _upsert_daily_row(self, row: pd.Series):
        """单行 Upsert (仅用于append_only=False时)"""
        conn = self._engine.connect()
        
        # 过滤有效列
        valid_cols = [c for c in row.index if c in ['symbol', 'date'] or row[c] is not None]
        filtered_row = row[valid_cols]
        
        cols = ', '.join([c for c in filtered_row.index if c in ['symbol', 'date']])
        update_cols = ', '.join([c for c in filtered_row.index if c not in ['symbol', 'date']])
        
        if not update_cols:
            return
        
        values = ', '.join([f":{c}" for c in filtered_row.index])
        set_clause = ', '.join([
            f"{c} = EXCLUDED.{c}" 
            for c in filtered_row.index 
            if c not in ['symbol', 'date']
        ])
        
        sql = f"""
        INSERT INTO daily_factors_wide ({cols})
        VALUES ({values})
        ON CONFLICT (symbol, date) DO UPDATE SET {set_clause}, updated_at = NOW();
        """
        
        try:
            conn.execute(text(sql), filtered_row.to_dict())
        finally:
            conn.close()
    
    def query_daily_factor(
        self,
        symbols: List[str] = None,
        start_date: datetime = None,
        end_date: datetime = None,
        factor_columns: List[str] = None
    ) -> pd.DataFrame:
        """查询日级因子数据"""
        sql = "SELECT * FROM daily_factors_wide WHERE 1=1"
        params = {}
        
        if symbols:
            sql += " AND symbol = ANY(:symbols)"
            params['symbols'] = symbols
        
        if start_date:
            sql += " AND date >= :start_date"
            params['start_date'] = start_date
        
        if end_date:
            sql += " AND date <= :end_date"
            params['end_date'] = end_date
        
        if factor_columns:
            sql += " AND (" + " OR ".join([f"{c} IS NOT NULL" for c in factor_columns]) + ")"
        
        sql += " ORDER BY date DESC, symbol"
        
        df = pd.read_sql(sql, self._engine, params=params)
        
        # 只返回需要的列
        if factor_columns:
            cols = ['symbol', 'date'] + [c for c in factor_columns if c in df.columns]
            df = df[cols]
        
        return df
    
    # ==================== 周级因子 ====================
    
    def save_weekly_factor(
        self,
        df: pd.DataFrame,
        factor_columns: List[str] = None
    ):
        """保存周级因子数据（宽表）"""
        if df.empty:
            return
        
        df = df.copy()
        
        if 'date' not in df.columns:
            df['date'] = datetime.now().date()
        
        df.to_sql(
            'weekly_factors_wide',
            self._engine,
            if_exists='append',
            index=False,
            method='multi',
            chunksize=1000
        )
        
        logger.info(f"✅ 保存周级因子: {len(df)} 行")
    
    def query_weekly_factor(
        self,
        symbols: List[str] = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> pd.DataFrame:
        """查询周级因子数据"""
        sql = "SELECT * FROM weekly_factors_wide WHERE 1=1"
        params = {}
        
        if symbols:
            sql += " AND symbol = ANY(:symbols)"
            params['symbols'] = symbols
        
        if start_date:
            sql += " AND date >= :start_date"
            params['start_date'] = start_date
        
        if end_date:
            sql += " AND date <= :end_date"
            params['end_date'] = end_date
        
        sql += " ORDER BY date DESC, symbol"
        
        return pd.read_sql(sql, self._engine, params=params)
    
    # ==================== 统计信息 ====================
    
    def get_stats(self) -> Dict[str, Any]:
        """获取存储统计"""
        stats = {}
        
        # 因子配置数量
        with self.session() as s:
            stats['total_factors'] = s.execute(text("SELECT COUNT(*) FROM factor_config")).scalar()
        
        # 宽表行数
        with self.session() as s:
            stats['daily_factors_count'] = s.execute(
                text("SELECT COUNT(*) FROM daily_factors_wide")
            ).scalar()
        
        # 分钟因子分区数
        with self.session() as s:
            result = s.execute(text("""
                SELECT COUNT(*) FROM pg_inherits
                JOIN pg_class ON pg_inherits.inhrelid = pg_class.oid
                WHERE pg_inherits.inhparent = 'minute_factor_values'::regclass
            """)).scalar()
            stats['minute_partitions'] = result or 0
        
        # 估算分钟因子数据量
        with self.session() as s:
            try:
                total = s.execute(text("""
                    SELECT SUM(n_live_tup) FROM pg_stat_user_tables
                    WHERE relname = 'minute_factor_values'
                """)).scalar()
                stats['minute_factors_estimated'] = total or 0
            except:
                stats['minute_factors_estimated'] = 'N/A'
        
        return stats


# ==================== 便捷函数 ====================

_storage_instance: Optional[FactorStorage] = None

def get_factor_storage(connection_string: str = None) -> FactorStorage:
    """获取因子存储单例"""
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = FactorStorage(connection_string)
    return _storage_instance

def init_factor_storage(connection_string: str = None) -> FactorStorage:
    """初始化因子存储"""
    storage = get_factor_storage(connection_string)
    storage.init()
    return storage


# ==================== 导出 ====================

__all__ = [
    'FactorStorage',
    'FactorConfig',
    'DailyFactorWide',
    'WeeklyFactorWide',
    'get_factor_storage',
    'init_factor_storage',
]
