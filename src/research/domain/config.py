"""Research configuration.

Replaces the old ``MiningConfig`` with a cleaner, layered structure.
``ResearchConfig`` is the top-level entry point.  Sub-configs for
evaluation profiles, universe, and preprocessing are broken out so
they can be versioned and stored independently in
``storage/evaluation_profiles/``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ======================================================================
# Universe
# ======================================================================

@dataclass
class UniverseConfig:
    """Defines which stocks are in scope.

    The default universe is CSI 1000 (the new system standard).
    """

    universe_id: str = "csi1000"
    label: str = "CSI 1000"
    filter_suspend: bool = True
    filter_limit: bool = True
    min_listing_days: int = 60


# ======================================================================
# Preprocessing
# ======================================================================

@dataclass
class PreprocessConfig:
    """Factor preprocessing settings."""

    winsorize_method: str = "mad"  # "mad" | "sigma"
    winsorize_n: float = 5.0
    standardize_method: str = "zscore"  # "zscore" | "rank"


# ======================================================================
# Neutralization
# ======================================================================

@dataclass
class NeutralizationConfig:
    """Neutralization settings."""

    mode: str = "none"  # "none" | "market_cap" | "industry" | "both"


# ======================================================================
# Evaluation Profile
# ======================================================================

@dataclass
class EvaluationProfile:
    """A versioned evaluation configuration (from research_execute.md Section 4.1).

    Each profile bundles a universe, preprocessing, neutralization, and
    pipeline specification.  Profiles are stored as YAML in
    ``storage/evaluation_profiles/evaluation/``.
    """

    profile_id: str = "standard_eval_v2"

    # Sub-configs
    universe: UniverseConfig = field(default_factory=UniverseConfig)
    preprocess: PreprocessConfig = field(default_factory=PreprocessConfig)
    neutralization: NeutralizationConfig = field(default_factory=NeutralizationConfig)

    # Pipeline parameters
    delay: int = 1  # trading-day delay before signal is actionable
    holding_horizon: int = 5  # days

    # Primary pipeline
    primary_pipeline: str = "rank_ic"  # "rank_ic" | "long_short" | "portfolio"

    # Auxiliary views (additional diagnostics to compute)
    auxiliary_views: List[str] = field(
        default_factory=lambda: ["long_short", "quintile", "turnover"]
    )

    # Tradability
    tradability_profile: str = "china_a_daily_tradeable_v1"

    # Style / Barra
    style_profile: Optional[str] = None  # e.g. "barra_cn_v1"


# ======================================================================
# Top-level Research Config
# ======================================================================

@dataclass
class ResearchConfig:
    """Top-level configuration for the research system.

    This replaces the old ``MiningConfig``.
    """

    # ---- Identity ----
    version: str = "1.0.0"

    # ---- Qlib ----
    qlib_data_dir: str = "~/.qlib/qlib_data/cn_data_1d"

    # ---- Default evaluation profile ----
    default_eval_profile: EvaluationProfile = field(
        default_factory=EvaluationProfile
    )

    # ---- Thresholds ----
    ic_threshold: float = 0.01
    correlation_threshold: float = 0.7
    replacement_ic_ratio: float = 1.3
    replacement_ic_min: float = 0.03

    # ---- Hard gates (auto-reject) ----
    hard_gate_oos_decay_min: float = 0.2
    hard_gate_coverage_min: float = 0.3
    hard_gate_ic_oos_min: float = 0.008

    # ---- Library ----
    target_library_size: int = 100

    # ---- Batching ----
    candidates_per_batch: int = 8
    max_expression_depth: int = 10

    # ---- Correlation check ----
    corr_check_years: int = 2

    # ---- Available base fields ----
    base_fields: List[str] = field(
        default_factory=lambda: [
            "$open", "$high", "$low", "$close", "$volume", "$amount",
            "$pe_ratio", "$pb_ratio", "$ps_ratio",
            "$market_cap", "$circ_market_cap", "$turnover_rate",
        ]
    )

    # ---- Categories ----
    categories: List[str] = field(
        default_factory=lambda: [
            "volume_price", "momentum", "volatility", "volume",
            "regime", "efficiency", "distribution", "trend",
            "candlestick", "fundamental", "liquidity", "other",
        ]
    )

    # ---- Storage paths (relative to project root) ----
    state_dir: str = "storage/state"
    logic_dir: str = "storage/logic"
    routes_dir: str = "storage/routes"
    registry_dir: str = "storage/registry"
    policy_dir: str = "storage/policy"
    history_dir: str = "storage/history"
    reports_dir: str = "storage/reports"
    memory_dir: str = "storage/memory"
    vault_dir: str = "storage/evidence/vault"
    cache_dir: str = "storage/runtime/cache"
