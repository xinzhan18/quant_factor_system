"""
数据模块
Data Module

⚠️ 注意: 本项目只支持 TimescaleDB

安装 TimescaleDB:
    docker run -d --name timescaledb \
      -p 5432:5432 \
      -e POSTGRES_PASSWORD=quant123 \
      timescale/timescaledb:latest-pg14

使用:
    from quant_factor_system.data import TimescaleDB, QuantDataManager
    
    # 初始化
    manager = QuantDataManager()
    manager.initialize()
    
    # 更新数据
    manager.update_daily(symbols=['SH600000'])
    
    # 查询
    df = manager.get_price(symbols=['SH600000'], frequency='daily')
"""

from .ricequant_source import (
    RiceQuantSource,
)

from .timescale_storage import (
    TimescaleDB,
    QuantDataManager,
    TIMESCALE_CONFIG,
    CHUNK_CONFIG,
    COMPRESSION_POLICY,
    get_timescaledb,
    init_quant_db,
)

from .data_manager import (
    DataManager,
    create_data_manager,
)

__all__ = [
    # TimescaleDB 存储 (生产环境) ⭐
    'TimescaleDB',
    'QuantDataManager',
    'TIMESCALE_CONFIG',
    'CHUNK_CONFIG',
    'COMPRESSION_POLICY',
    'get_timescaledb',
    'init_quant_db',
    
    # 数据管理
    'DataManager',
    'create_data_manager',
    
    # 数据源
    'RiceQuantSource',
]
