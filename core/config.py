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
import threading
from typing import Any, Dict, Optional
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


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
class SystemConfig:
    """系统配置"""
    name: str = "QuantFactorSystem"
    version: str = "4.1.0"
    created_at: datetime = field(default_factory=datetime.now)
    qlib_data_dir: str = "~/.qlib/qlib_data/cn_data_1d"

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    def validate(self) -> bool:
        """验证配置"""
        if self.database.port < 1 or self.database.port > 65535:
            raise ValueError(f"无效的数据库端口: {self.database.port}")

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
        }


# 全局配置实例 (线程安全)
_config: Optional[SystemConfig] = None
_config_lock = threading.Lock()


def get_config() -> SystemConfig:
    """获取全局配置（线程安全）"""
    global _config
    if _config is None:
        with _config_lock:
            if _config is None:
                _config = _load_config_from_sources()
    return _config


def _load_config_from_sources() -> SystemConfig:
    """按优先级加载配置：环境变量 > config.yaml > 默认值"""
    config = SystemConfig()

    # 尝试加载 config.yaml
    yaml_path = Path(__file__).parent.parent / 'config.yaml'
    if yaml_path.exists():
        try:
            import yaml
            with open(yaml_path) as f:
                yaml_config = yaml.safe_load(f) or {}

            if 'database' in yaml_config:
                db = yaml_config['database']
                config.database.host = db.get('host', config.database.host)
                config.database.port = db.get('port', config.database.port)
                config.database.database = db.get('database', config.database.database)
                config.database.user = db.get('user', config.database.user)
                config.database.password = db.get('password', config.database.password)
        except ImportError:
            pass

    # 环境变量覆盖（最高优先级）
    config.database = DatabaseConfig.from_env()

    return config


def load_config(config_dict: Dict[str, Any]) -> SystemConfig:
    """加载配置"""
    global _config
    with _config_lock:
        _config = SystemConfig(**config_dict)
    return _config


def reset_config():
    """重置配置为默认值"""
    global _config
    with _config_lock:
        _config = None
