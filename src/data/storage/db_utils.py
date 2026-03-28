"""
数据库工具
Database Utilities
"""

from .timescale_storage import TimescaleDB

# 单例实例
_db_instance = None

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


__all__ = ['get_db', 'init_db']
