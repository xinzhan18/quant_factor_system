"""Adapter: make the old ReportDataBuilder work with the new config.yaml.

The old builder imports ``mining.config.MiningConfig``. Instead of
restoring the entire mining module, this adapter creates a compatible
MiningConfig-like object from ``storage/config.yaml`` + env vars.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass
class DatabaseConfig:
    host: str = "localhost"
    port: int = 5432
    database: str = "quant_data"
    user: str = "postgres"
    password: str = "postgres"

    @property
    def connection_string(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        return cls(
            host=os.getenv("TIMESCALE_HOST", "localhost"),
            port=int(os.getenv("TIMESCALE_PORT", "5432")),
            database=os.getenv("TIMESCALE_DB", "quant_data"),
            user=os.getenv("TIMESCALE_USER", "postgres"),
            password=os.getenv("TIMESCALE_PASSWORD", "postgres"),
        )


@dataclass
class SystemConfig:
    qlib_data_dir: str = "~/.qlib/qlib_data/cn_data_1d"
    database: DatabaseConfig = field(default_factory=DatabaseConfig.from_env)


@dataclass
class MiningConfig:
    """Minimal MiningConfig compatible with the old ReportDataBuilder."""

    system: SystemConfig = field(default_factory=SystemConfig)

    @property
    def qlib_data_dir(self) -> str:
        return self.system.qlib_data_dir

    train_start: str = "2015-01-01"
    train_end: str = "2021-12-31"
    test_start: str = "2022-01-01"
    test_end: str = "2023-12-31"

    @classmethod
    def from_config_yaml(cls, config: dict) -> "MiningConfig":
        """Build from the new storage/config.yaml dict."""
        sample = config.get("sample_policy", {})
        train_range = sample.get("train_range", ["2015-01-01", "2021-12-31"])
        val_range = sample.get("validation_range", ["2022-01-01", "2023-12-31"])
        qlib_dir = config.get("qlib_data_dir", "~/.qlib/qlib_data/cn_data_1d")

        return cls(
            system=SystemConfig(
                qlib_data_dir=qlib_dir,
                database=DatabaseConfig.from_env(),
            ),
            train_start=train_range[0],
            train_end=train_range[1],
            test_start=val_range[0],
            test_end=val_range[1],
        )
