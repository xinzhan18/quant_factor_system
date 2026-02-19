"""
PostgreSQL 数据库管理
"""

import pandas as pd
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import contextmanager
import logging
import os

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Text, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy import text

logger = logging.getLogger(__name__)
Base = declarative_base()


# ==================== 数据模型 ====================

class FactorResult(Base):
    """因子计算结果表"""
    __tablename__ = 'factor_results'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    factor_name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    factor_value = Column(Float)
    ic = Column(Float)
    return_value = Column(Float)
    created_at = Column(DateTime, default=datetime.now)
    
    __table_args__ = (
        UniqueConstraint('factor_name', 'symbol', 'timestamp', name='uix_factor_result'),
    )


class FactorMeta(Base):
    """因子元信息表"""
    __tablename__ = 'factor_meta'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)
    class_name = Column(String(100))
    category = Column(String(50))
    params = Column(Text)  # JSON
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.now)


# ==================== PostgreSQL 管理器 ====================

class PostgresDB:
    """
    PostgreSQL 数据库管理器
    
    功能:
    - 连接管理
    - 因子结果存储
    - 因子元信息管理
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
        logger.info(f"PostgreSQL: {connection_string.split('@')[1]}")
    
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
        """初始化数据库表"""
        try:
            Base.metadata.create_all(self._engine)
            logger.info("✅ PostgreSQL 表创建完成")
        except Exception as e:
            logger.error(f"初始化失败: {e}")
            raise
    
    # ==================== 因子结果操作 ====================
    
    def save_factor_result(
        self,
        factor_name: str,
        symbol: str,
        timestamp: datetime,
        factor_value: float,
        ic: float = None,
        return_value: float = None
    ):
        """保存因子结果"""
        with self.session() as s:
            result = FactorResult(
                factor_name=factor_name,
                symbol=symbol,
                timestamp=timestamp,
                factor_value=factor_value,
                ic=ic,
                return_value=return_value
            )
            s.add(result)
        logger.debug(f"保存因子结果: {factor_name} {symbol}")
    
    def save_factor_results(self, df: pd.DataFrame, factor_name: str, ic: float = None):
        """批量保存因子结果"""
        if df.empty:
            return
        
        with self.session() as s:
            for _, row in df.iterrows():
                result = FactorResult(
                    factor_name=factor_name,
                    symbol=row.get('symbol', 'UNKNOWN'),
                    timestamp=row.get('timestamp', datetime.now()),
                    factor_value=row.get(factor_name, row.get('factor_value')),
                    ic=ic
                )
                s.add(result)
        logger.info(f"批量保存 {len(df)} 条因子结果")
    
    def query_factor_results(
        self,
        factor_name: str = None,
        symbol: str = None,
        start: datetime = None,
        end: datetime = None,
        limit: int = 1000
    ) -> pd.DataFrame:
        """查询因子结果"""
        sql = "SELECT * FROM factor_results WHERE 1=1"
        params = {}
        
        if factor_name:
            sql += " AND factor_name = :factor_name"
            params['factor_name'] = factor_name
        
        if symbol:
            sql += " AND symbol = :symbol"
            params['symbol'] = symbol
        
        if start:
            sql += " AND timestamp >= :start"
            params['start'] = start
        
        if end:
            sql += " AND timestamp <= :end"
            params['end'] = end
        
        sql += " ORDER BY timestamp DESC LIMIT :limit"
        params['limit'] = limit
        
        return pd.read_sql(sql, self._engine, params=params)
    
    def get_latest_factor(self, factor_name: str, symbol: str = None) -> pd.DataFrame:
        """获取最新因子值"""
        sql = """
            SELECT DISTINCT ON (symbol) * 
            FROM factor_results 
            WHERE factor_name = :factor_name
        """
        params = {'factor_name': factor_name}
        
        if symbol:
            sql += " AND symbol = :symbol"
            params['symbol'] = symbol
        
        sql += " ORDER BY symbol, timestamp DESC"
        
        return pd.read_sql(sql, self._engine, params=params)
    
    # ==================== 因子元信息 ====================
    
    def save_factor_meta(
        self,
        name: str,
        class_name: str,
        category: str = "custom",
        params: dict = None,
        description: str = ""
    ):
        """保存因子元信息"""
        import json
        
        with self.session() as s:
            meta = FactorMeta(
                name=name,
                class_name=class_name,
                category=category,
                params=json.dumps(params or {}),
                description=description
            )
            s.add(meta)
        logger.info(f"保存因子元信息: {name}")
    
    def get_factor_meta(self, name: str) -> Optional[Dict]:
        """获取因子元信息"""
        import json
        
        with self.session() as s:
            result = s.execute(
                text("SELECT * FROM factor_meta WHERE name = :name"),
                {'name': name}
            ).fetchone()
            
            if result:
                return {
                    'name': result[1],
                    'class_name': result[2],
                    'category': result[3],
                    'params': json.loads(result[4]) if result[4] else {},
                    'description': result[5]
                }
        return None
    
    def list_factor_meta(self, category: str = None) -> List[Dict]:
        """列出因子元信息"""
        import json
        
        sql = "SELECT * FROM factor_meta"
        params = {}
        
        if category:
            sql += " WHERE category = :category"
            params['category'] = category
        
        with self.session() as s:
            results = s.execute(text(sql), params).fetchall()
            
            return [
                {
                    'name': r[1],
                    'class_name': r[2],
                    'category': r[3],
                    'params': json.loads(r[4]) if r[4] else {},
                    'description': r[5]
                }
                for r in results
            ]
    
    # ==================== 统计 ====================
    
    def get_stats(self) -> Dict[str, int]:
        """获取统计信息"""
        with self.session() as s:
            factor_count = s.execute(text("SELECT COUNT(*) FROM factor_results")).scalar()
            meta_count = s.execute(text("SELECT COUNT(*) FROM factor_meta")).scalar()
            
            return {
                'factor_results': factor_count or 0,
                'factor_meta': meta_count or 0
            }


# ==================== 便捷函数 ====================

_db_instance: Optional[PostgresDB] = None

def get_postgres_db(connection_string: str = None) -> PostgresDB:
    """获取 PostgreSQL 数据库单例"""
    global _db_instance
    if _db_instance is None:
        _db_instance = PostgresDB(connection_string)
    return _db_instance

def init_postgres_db(connection_string: str = None) -> PostgresDB:
    """初始化 PostgreSQL 数据库"""
    db = get_postgres_db(connection_string)
    db.init()
    return db


# ==================== 导出 ====================

__all__ = [
    'PostgresDB',
    'get_postgres_db',
    'init_postgres_db',
    'FactorResult',
    'FactorMeta',
]
