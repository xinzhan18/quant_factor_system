"""Core domain records: FactorRecord v3, CandidateRecord, RouteRecord.

These are the mutable state objects that flow through the research
pipeline.  They are *not* frozen because lifecycle transitions and
metric updates modify them in place.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


# ======================================================================
# Enums
# ======================================================================

class SourceType(enum.Enum):
    """How a factor is implemented."""

    DSL = "dsl"
    PYTHON = "python"


class FactorStatus(enum.Enum):
    """Lifecycle status of a factor in the registry."""

    ACTIVE = "active"
    LEGACY = "legacy"
    RETIRED = "retired"


class RouteType(enum.Enum):
    """Research purpose of a route."""

    GENESIS = "genesis"
    MUTATE = "mutate"
    CROSSOVER = "crossover"
    REPAIR = "repair"
    DECORRELATE = "decorrelate"


class RouteStatus(enum.Enum):
    """Lifecycle status of a route."""

    PLANNED = "planned"
    PROBING = "probing"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    RESERVED = "reserved"


class Decision(enum.Enum):
    """Admission decision for a factor."""

    ADMIT = "admit"
    REPLACE = "replace"


class MutationType(enum.Enum):
    """How a candidate was derived from its parents."""

    GENESIS = "genesis"
    WINDOW_VARIATION = "window_variation"
    RANK_TRANSFORM = "rank_transform"
    PARAMETER_VARIATION = "parameter_variation"
    STABILITY_FIX = "stability_fix"
    DECORRELATE = "decorrelate"
    ADDITIVE = "additive"
    GATED = "gated"
    INTERACTION = "interaction"
    REPAIR = "repair"
    OTHER = "other"


# ======================================================================
# Lineage
# ======================================================================

@dataclass
class Lineage:
    """Derivation lineage for a candidate / factor."""

    parent_logic: str = ""
    parent_experiment_tags: List[str] = field(default_factory=list)
    parent_routes: List[str] = field(default_factory=list)
    parent_factors: List[str] = field(default_factory=list)
    mutation_type: str = "genesis"


# ======================================================================
# Evaluation Context
# ======================================================================

@dataclass
class EvaluationContext:
    """Records which profile was active when a factor was admitted."""

    eval_profile: str = ""
    holdout_used: bool = False


# ======================================================================
# FactorRecord
# ======================================================================

@dataclass
class FactorRecord:
    """A factor admitted to the registry.

    The metadata truth source stored at
    ``storage/registry/factors/factor_XXX.yaml``.
    """

    # ---- Identity ----
    factor_id: str = ""
    name: str = ""
    category: str = ""
    source_type: str = "dsl"  # "dsl" | "python"

    # ---- Provenance ----
    logic_id: str = ""
    route_id: str = ""
    route_type: str = ""
    experiment_lineage_tag: str = ""
    family_id: str = ""

    # ---- Implementation ----
    expression: Optional[str] = None  # for DSL factors
    code_path: Optional[str] = None  # for Python factors

    # ---- Admission ----
    admitted_at: Optional[str] = None  # ISO datetime string
    decision: str = "admit"  # "admit" | "replace"
    replace_target_id: Optional[str] = None
    status: str = "active"  # "active" | "legacy" | "retired"

    # ---- Evaluation Context ----
    evaluation_context: EvaluationContext = field(
        default_factory=EvaluationContext
    )

    # ---- Lineage ----
    lineage: Lineage = field(default_factory=Lineage)

    # ---- Snapshots (dicts for flexibility) ----
    metrics_snapshot: Dict[str, Any] = field(default_factory=dict)
    strict_stats_snapshot: Dict[str, Any] = field(default_factory=dict)
    risk_review_snapshot: Dict[str, Any] = field(default_factory=dict)
    similarity_snapshot: Dict[str, Any] = field(default_factory=dict)
    feasibility_snapshot: Dict[str, Any] = field(default_factory=dict)

    # ---- Report ----
    report_path: Optional[str] = None
    replacement_history: List[str] = field(default_factory=list)



# ======================================================================
# CandidateRecord
# ======================================================================

@dataclass
class CandidateRecord:
    """A candidate factor not yet admitted to the registry.

    Defined in idea_plan.md Section 16.  Candidates flow from /idea
    through /execute to /judge.
    """

    # ---- Identity ----
    candidate_id: str = ""
    logic_id: str = ""
    route_id: str = ""
    family_id: str = ""
    route_type: str = ""  # genesis / mutate / crossover / repair / decorrelate
    source_type: str = "dsl"  # "dsl" | "python"
    experiment_lineage_tag: str = ""

    # ---- Content ----
    name: str = ""
    expression: Optional[str] = None  # for DSL
    code: Optional[str] = None  # for Python
    code_path: Optional[str] = None  # for Python (file reference)
    params: Dict[str, Any] = field(default_factory=dict)
    param_space: Dict[str, List[Any]] = field(default_factory=dict)

    # ---- Rationale ----
    rationale: str = ""
    implementation_reason: str = ""

    # ---- Lineage ----
    lineage: Lineage = field(default_factory=Lineage)

    # ---- Metrics (populated by /execute) ----
    metrics: Dict[str, Any] = field(default_factory=dict)


# ======================================================================
# RouteRecord
# ======================================================================

@dataclass
class RouteRecord:
    """A research route — the design layer between logic and candidate.

    Defined in idea_plan.md Section 3 / memory.md Section C.
    """

    # ---- Identity ----
    route_id: str = ""
    logic_id: str = ""
    family_id: str = ""
    route_type: str = ""  # genesis / mutate / crossover / repair / decorrelate
    status: str = "planned"
    priority: str = "medium"  # "high" | "medium" | "low"

    # ---- Research Question ----
    research_question: str = ""
    hypothesis_slice: str = ""

    # ---- Origin ----
    origin_source: str = ""  # "logic_native" | "mutation" | "crossover"
    parent_routes: List[str] = field(default_factory=list)
    parent_factors: List[str] = field(default_factory=list)

    # ---- Structure ----
    requires_branching: bool = False
    estimated_branch_count: int = 0
    requires_multi_state_logic: bool = False
    requires_multi_stage_pipeline: bool = False
    intermediate_variable_count: int = 0
    dsl_naturalness: str = "high"  # "high" | "medium" | "low"

    # ---- Probe ----
    core_probe_form: str = ""
    neighbor_probe_form: str = ""
    probe_profile: str = "probe_v2_train_only"

    # ---- Expansion Template ----
    candidate_target_count: int = 3
    allowed_variations: List[str] = field(default_factory=list)
    forbidden_variations: List[str] = field(default_factory=list)

    # ---- Execution Outcomes ----
    probe_history: List[Dict[str, Any]] = field(default_factory=list)
    eval_attempts: int = 0
    admits: int = 0
    near_misses: int = 0
    overlap_blocked: int = 0
    style_drift_blocked: int = 0

    # ---- Diagnosis ----
    primary_failure_mode: str = ""
    implementation_preference: str = "dsl"
    next_action: str = ""
