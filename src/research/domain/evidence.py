"""Evidence structs (all frozen dataclasses).

Every piece of quantitative evidence produced during evaluation is
represented as a frozen dataclass.  These are pure data containers
with no side effects.

Organisation follows the four evidence dimensions from the judge:
  1. Effect Strength
  2. Stability
  3. Redundancy
  4. Feasibility

Plus cross-cutting: mechanism alignment, risk review, probe results,
and batch-level execution results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional, Tuple


# ======================================================================
# 1. Effect Strength
# ======================================================================

@dataclass(frozen=True)
class EffectStrengthEvidence:
    """Core signal-strength metrics for a candidate."""

    ic_mean_is: float
    ic_mean_oos: float
    icir_is: float
    icir_oos: float
    ls_tstat: float
    ls_sharpe: float
    monotonicity_is: float
    monotonicity_oos: float
    long_contribution: Optional[float] = None


@dataclass(frozen=True)
class SearchAdjustedStrength:
    """Effect strength after multiple-testing adjustment."""

    raw_ic: float
    adjusted_ic: float
    adjustment_method: str  # "bonferroni" | "bh" | "bootstrap"
    n_tests: int
    significant: bool


@dataclass(frozen=True)
class MultipleTestingView:
    """Summary of multiple-testing context for this batch / logic."""

    total_candidates_tested: int
    total_routes_tested: int
    logic_id: str
    family_id: str
    adjustment_method: str
    adjusted_threshold: float


# ======================================================================
# 2. Stability
# ======================================================================

@dataclass(frozen=True)
class SplitStabilityResult:
    """IC comparison across two time segments."""

    ic_seg_a: float
    ic_seg_b: float
    seg_a_range: Tuple[date, date]
    seg_b_range: Tuple[date, date]
    sign_consistent: bool
    ratio: float  # min(|a|,|b|) / max(|a|,|b|)


@dataclass(frozen=True)
class RegimeStabilityResult:
    """Performance under different market regimes."""

    regime_label: str  # e.g. "bull", "bear", "sideways"
    ic_mean: float
    ls_sharpe: float
    n_days: int


@dataclass(frozen=True)
class BootstrapStabilityResult:
    """Bootstrap confidence interval for IC."""

    n_bootstrap: int
    ic_mean: float
    ic_std: float
    ci_lower: float  # 5th percentile
    ci_upper: float  # 95th percentile
    pct_positive: float  # fraction of bootstrap samples with IC > 0


@dataclass(frozen=True)
class ExpandingWindowResult:
    """IC in an expanding-window analysis."""

    window_id: str
    window_end: date
    ic_mean: float
    ic_cumulative: float
    n_observations: int


# ======================================================================
# 3. Redundancy
# ======================================================================

@dataclass(frozen=True)
class PairwiseRedundancy:
    """Correlation between two factors."""

    factor_id_a: str
    factor_id_b: str
    correlation: float
    method: str = "pearson"  # "pearson" | "spearman"


@dataclass(frozen=True)
class FamilyRedundancyView:
    """Redundancy summary within a factor family."""

    family_id: str
    n_members: int
    max_pairwise_corr: float
    mean_pairwise_corr: float
    incremental_ic: Optional[float] = None


@dataclass(frozen=True)
class SubspaceRedundancyView:
    """Redundancy in a broader subspace (category / logic)."""

    subspace_label: str
    n_factors: int
    max_pairwise_corr: float
    mean_pairwise_corr: float


@dataclass(frozen=True)
class RedundancyEvidence:
    """Aggregated redundancy evidence for a candidate."""

    max_correlation: float
    most_correlated_factor_id: str
    pairwise: List[PairwiseRedundancy] = field(default_factory=list)
    family_view: Optional[FamilyRedundancyView] = None
    subspace_view: Optional[SubspaceRedundancyView] = None
    incremental_ic: Optional[float] = None


# ======================================================================
# 4. Feasibility
# ======================================================================

@dataclass(frozen=True)
class FeasibilityEvidence:
    """Practical feasibility checks."""

    coverage: float  # fraction of universe with non-NaN values
    turnover_mean: Optional[float] = None  # daily factor turnover
    compute_seconds: Optional[float] = None
    memory_mb: Optional[float] = None
    expression_depth: Optional[int] = None
    data_fields_used: tuple = ()  # e.g. ("$close", "$volume")


# ======================================================================
# Cross-cutting: Mechanism & Risk
# ======================================================================

@dataclass(frozen=True)
class MechanismAlignmentResult:
    """How well a candidate aligns with its logic's stated mechanism."""

    logic_id: str
    alignment_score: float  # 0.0 - 1.0
    size_proxy_risk: bool
    style_repackaging_risk: bool
    explanation: str = ""


@dataclass(frozen=True)
class RiskReviewEvidence:
    """Style / risk factor diagnostics."""

    factor_size_corr: Optional[float] = None
    barra_residual_ic: Optional[float] = None
    dominant_barra_style: Optional[str] = None
    alpha_survival_ratio: Optional[float] = None
    style_warning: bool = False


@dataclass(frozen=True)
class SupportWindowCheck:
    """Result of evaluating a candidate on a support validation window."""

    window_id: str
    ic_mean: float
    ic_positive_ratio: float
    monotonicity: float
    consistent_with_primary: bool


# ======================================================================
# Probe & Execution Results
# ======================================================================

@dataclass(frozen=True)
class ProbeResult:
    """Result of a lightweight probe run (training period only)."""

    route_id: str
    expression: str
    computable: bool
    valid_ratio: float
    variance_ok: bool
    ic_mean_full: Optional[float] = None
    ic_mean_seg_a: Optional[float] = None
    ic_mean_seg_b: Optional[float] = None
    forbidden_hit: bool = False
    overlap_risk_hint: bool = False
    neighbor_consistency: Optional[float] = None


@dataclass(frozen=True)
class CandidateExecuteResult:
    """Full execution result for a single candidate."""

    candidate_id: str
    expression: str

    # Gate status
    execution_gate_passed: bool
    gate_failure_reasons: tuple = ()  # tuple of ReasonCode names

    # Evidence bundles (Optional — populated only if gate passed)
    effect: Optional[EffectStrengthEvidence] = None
    redundancy: Optional[RedundancyEvidence] = None
    feasibility: Optional[FeasibilityEvidence] = None
    risk_review: Optional[RiskReviewEvidence] = None
    mechanism_alignment: Optional[MechanismAlignmentResult] = None

    # Stability evidence
    split_stability: Optional[SplitStabilityResult] = None
    regime_stability: tuple = ()  # tuple of RegimeStabilityResult
    bootstrap: Optional[BootstrapStabilityResult] = None
    expanding_windows: tuple = ()  # tuple of ExpandingWindowResult
    support_window_checks: tuple = ()  # tuple of SupportWindowCheck


@dataclass(frozen=True)
class BatchExecuteResult:
    """Aggregated execution results for a full batch."""

    batch_id: str
    sample_policy_version: str
    evaluation_profile_id: str
    candidates: tuple = ()  # tuple of CandidateExecuteResult
    total_candidates: int = 0
    gate_passed_count: int = 0
    execution_time_seconds: Optional[float] = None
