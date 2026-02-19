"""
量化因子系统配置
QuantFactor System Configuration

功能:
- 统一配置管理
- 环境变量支持
- 默认参数
- 配置验证
"""

import os
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "quant"
    user: str = "postgres"
    password: str = "postgres"
    pool_size: int = 5
    max_overflow: int = 10
    pool_recycle: int = 3600
    
    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @classmethod
    def from_env(cls) -> 'DatabaseConfig':
        """从环境变量读取配置"""
        return cls(
            host=os.getenv('TIMESCALE_HOST', 'localhost'),
            port=int(os.getenv('TIMESCALE_PORT', 5432)),
            database=os.getenv('TIMESCALE_DB', 'quant'),
            user=os.getenv('TIMESCALE_USER', 'postgres'),
            password=os.getenv('TIMESCALE_PASSWORD', 'postgres'),
        )


@dataclass
class CacheConfig:
    """缓存配置"""
    enabled: bool = True
    directory: str = "./cache"
    max_size_mb: int = 1000
    expire_seconds: int = 3600


@dataclass
class LoggingConfig:
    """日志配置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: Optional[str] = None
    console: bool = True


@dataclass
class PipelineConfig:
    """Pipeline配置"""
    default_window: int = 20
    max_factors: int = 100
    enable_cache: bool = True
    save_results: bool = True


@dataclass
class FactorConfig:
    """因子配置"""
    supported_frequencies = ['tick', '1min', '5min', '15min', '30min', '1hour', 'daily', 'weekly', 'monthly']
    default_frequency = 'daily'
    
    # 因子参数约束
    momentum_windows = [5, 10, 20, 60, 120, 250]
    ma_windows = [5, 10, 20, 50, 100, 200]
    rsi_windows = [6, 14, 21]


@dataclass
class SystemConfig:
    """系统配置"""
    name: str = "QuantFactorSystem"
    version: str = "3.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    factor: FactorConfig = field(default_factory=FactorConfig)
    
    def validate(self) -> bool:
        """验证配置"""
        if self.database.port < 1 or self.database.port > 65535:
            raise ValueError(f"无效的数据库端口: {self.database.port}")
        
        if self.pipeline.default_window < 1:
            raise ValueError(f"无效的默认窗口: {self.pipeline.default_window}")
        
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'version': self.version,
            'database': {
                'host': self.database.host,
                'port': self.database.port,
                'database': self.database.database,
            },
            'pipeline': {
                'default_window': self.pipeline.default_window,
                'max_factors': self.pipeline.max_factors,
            },
        }


# 全局配置实例
_config: Optional[SystemConfig] = None


def get_config() -> SystemConfig:
    """获取全局配置"""
    global _config
    if _config is None:
        _config = SystemConfig()
    return _config


def load_config(config_dict: Dict[str, Any]) -> SystemConfig:
    """加载配置"""
    global _config
    _config = SystemConfig(**config_dict)
    return _config


def reset_config():
    """重置配置为默认值"""
    global _config
    _config = SystemConfig()
