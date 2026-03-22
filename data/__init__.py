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

from .storage import (
    TimescaleDB,
    QuantDataManager,
    TIMESCALE_CONFIG,
    CHUNK_CONFIG,
    COMPRESSION_POLICY,
    get_timescaledb,
    init_quant_db,
    FactorVersion,
    VersionStatus,
    FactorVersionManager,
    Frequency,
    get_db,
    init_db,
)

from .data_manager import (
    DataManager,
    create_data_manager,
)

from .loaders import (
    get_factor_data,
    get_factor_metrics,
    get_price_data,
    get_database_tables,
    get_available_factors,
)

from .utils import (
    PostgresDB,
    get_postgres_db,
    init_postgres_db,
    FactorResult,
    FactorMeta,
    QuantDataFormatter,
    format_daily_data,
    format_factor_data,
    create_factor_matrix,
    BarData,
    FactorData,
    FactorDataGenerator,
    IndustrySource,
    get_industry_classification,
    get_industry_factors,
)

from .clean import (
    DataValidator,
    ValidationResult,
    validate_and_report,
)

from .qlib_sync import DataSynchronizer

__all__ = [
    # TimescaleDB 存储 (生产环境) ⭐
    'TimescaleDB',
    'QuantDataManager',
    'TIMESCALE_CONFIG',
    'CHUNK_CONFIG',
    'COMPRESSION_POLICY',
    'get_timescaledb',
    'init_quant_db',
    'get_db',
    'init_db',

    # 因子版本管理
    'FactorVersion',
    'VersionStatus',
    'FactorVersionManager',
    
    # 频率常量
    'Frequency',
    
    # 数据管理
    'DataManager',
    'create_data_manager',
    
    # 数据源
    'RiceQuantSource',
    
    # 数据加载
    'get_factor_data',
    'get_factor_metrics',
    'get_price_data',
    'get_database_tables',
    'get_available_factors',
    
    # 工具类
    'PostgresDB',
    'get_postgres_db',
    'init_postgres_db',
    'FactorResult',
    'FactorMeta',
    'QuantDataFormatter',
    'format_daily_data',
    'format_factor_data',
    'create_factor_matrix',
    'BarData',
    'FactorData',
    'FactorDataGenerator',
    
    # 行业数据
    'IndustrySource',
    'get_industry_classification',
    'get_industry_factors',
    
    # 数据验证
    'DataValidator',
    'ValidationResult',
    'validate_and_report',

    # Qlib 同步
    'DataSynchronizer',
]
