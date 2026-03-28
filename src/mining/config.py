"""Mining configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class DatabaseConfig:
    """数据库配置"""
    host: str = "localhost"
    port: int = 5432
    database: str = "quant_data"
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


@dataclass
class MiningConfig:
    """Configuration for the factor mining pipeline."""

    # System config reference
    system: SystemConfig = field(default_factory=SystemConfig)

    @property
    def qlib_data_dir(self) -> str:
        return self.system.qlib_data_dir

    # Evaluation thresholds
    ic_threshold: float = 0.03
    correlation_threshold: float = 0.7
    replacement_ic_ratio: float = 1.3
    replacement_ic_min: float = 0.05

    # Fast screening
    fast_screening_universe_size: int = 50

    # Library target
    target_library_size: int = 100

    # Universe
    universe: str = "all"
    custom_universe: Optional[List[str]] = None

    # Time ranges
    train_start: str = "2015-01-01"
    train_end: str = "2022-12-31"
    test_start: str = "2023-01-01"
    test_end: str = "2024-12-31"

    # Holdout set — never used in mining/evaluation, reserved for final backtest
    holdout_start: str = "2025-01-01"
    holdout_end: Optional[str] = None  # None = up to latest available data

    # Per-batch
    candidates_per_batch: int = 8

    # Expression limits
    max_expression_depth: int = 10

    # IC decay horizons (days) for multi-horizon analysis
    decay_horizons: List[int] = field(default_factory=lambda: [1, 5, 10, 20])

    # Paths (relative to project root)
    memory_dir: str = "storage/memory"
    library_dir: str = "storage/library"
    candidates_dir: str = "storage/candidates"
    report_dir: str = "storage/reports"

    # Available base fields
    base_fields: List[str] = field(default_factory=lambda: [
        "$open", "$high", "$low", "$close", "$volume", "$amount", "$vwap",
        "$returns",
    ])

    # Minute-aggregated fields (available after sync_minute_aggregates)
    minute_agg_fields: List[str] = field(default_factory=lambda: [
        "$intraday_vol", "$intraday_skew", "$intraday_kurt",
        "$vwap_dev", "$volume_conc", "$high_low_range",
        "$morning_momentum", "$afternoon_ret",
    ])

    # Predefined categories
    categories: List[str] = field(default_factory=lambda: [
        "vwap", "momentum", "volatility", "volume", "regime",
        "efficiency", "distribution", "trend", "candlestick",
        "intraday_agg", "other",
    ])

    # === Preprocessing ===
    # Universe filtering
    filter_suspend: bool = True
    filter_limit: bool = True

    # Factor value cleaning
    winsorize_method: str = "mad"  # "mad" or "sigma"
    winsorize_n: float = 5.0  # MAD multiplier (or sigma multiplier)
    standardize_method: str = "zscore"  # "zscore" or "rank"

    # Neutralization (optional, requires $market_cap / $industry_code synced)
    neutralize_mode: str = "none"  # "none", "market_cap", "industry", "both"
