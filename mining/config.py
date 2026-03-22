"""Mining configuration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from core.config import SystemConfig


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
    correlation_threshold: float = 0.5
    replacement_ic_ratio: float = 1.3
    replacement_ic_min: float = 0.05

    # Fast screening
    fast_screening_universe_size: int = 50

    # Library target
    target_library_size: int = 100

    # Universe
    universe: str = "csi500"
    custom_universe: Optional[List[str]] = None

    # Time ranges
    train_start: str = "2020-01-01"
    train_end: str = "2024-12-31"
    test_start: str = "2025-01-01"
    test_end: Optional[str] = None

    # Per-batch
    candidates_per_batch: int = 8

    # Expression limits
    max_expression_depth: int = 10

    # Paths (relative to project root)
    memory_dir: str = "mining/memory"
    library_dir: str = "mining/library"
    candidates_dir: str = "mining/candidates"

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
