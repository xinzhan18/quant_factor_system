"""Logic-layer contracts: LogicCard, LogicProposal, LogicReview, ScheduleSnapshot.

These objects model the outer-loop logic management system described in
logic_plan.md.  A **LogicCard** is the primary persistent object for a
market hypothesis.  **LogicProposal** and **LogicReview** handle the
proposal-review-admit workflow.  **ScheduleSnapshot** captures a
point-in-time budget allocation.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ======================================================================
# Enums
# ======================================================================

class LogicStatus(enum.Enum):
    """Lifecycle state of a market logic."""

    PROPOSED = "proposed"
    ACTIVE = "active"
    WARM = "warm"
    PRODUCTIVE = "productive"
    SATURATED = "saturated"
    PARKED = "parked"
    DEAD = "dead"


class LogicPriority(enum.Enum):
    """Scheduling priority for a logic."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class OriginType(enum.Enum):
    """How a logic proposal was sourced."""

    CANONICAL = "canonical"
    EMPIRICAL_LIBRARY = "empirical_library"
    NEAR_MISS_GENERALIZATION = "near_miss_generalization"
    CROSSOVER_HYPOTHESIS = "crossover_hypothesis"
    EXTERNAL_INSPIRATION = "external_inspiration"


class ProposalDecision(enum.Enum):
    """Outcome of reviewing a logic proposal."""

    CREATE_LOGIC = "create_logic"
    DOWNGRADE_TO_DIRECTION = "downgrade_to_direction"
    PARK = "park"
    REJECT = "reject"


class ReviewVerdict(enum.Enum):
    """Verdict for a single review dimension."""

    PASS = "pass"
    BORDERLINE = "borderline"
    FAIL = "fail"


# ======================================================================
# LogicCard
# ======================================================================

@dataclass
class LogicCard:
    """The primary persistent object for a market hypothesis.

    Stored at ``storage/logic/cards/LXXX.yaml``.
    Defined in logic_plan.md Section 3.3 and memory.md Section B.
    """

    # ---- Identity ----
    logic_id: str = ""
    name: str = ""
    category: str = ""
    status: str = "active"  # matches LogicStatus values
    priority: str = "medium"  # matches LogicPriority values

    # ---- Hypothesis ----
    hypothesis: Dict[str, str] = field(default_factory=dict)
    # Expected keys: condition, behavior, timeframe, direction

    # ---- Contract (budget constraints for /idea) ----
    contract: Dict[str, Any] = field(default_factory=dict)
    # Expected keys: direction_quota, candidate_quota, preferred_mode,
    # preferred_families, suggested_ops, required_fields,
    # avoid_patterns, current_focus_question

    # ---- Discovery ----
    discovery_budget: Dict[str, int] = field(default_factory=dict)
    # Expected keys: direction_quota, candidate_quota

    # ---- Families ----
    preferred_families: List[str] = field(default_factory=list)
    productive_families: List[str] = field(default_factory=list)
    failed_families: List[str] = field(default_factory=list)

    # ---- Diagnostics ----
    current_bottleneck: str = ""
    next_actions: List[str] = field(default_factory=list)

    # ---- Implementation Space ----
    implementation_space: Dict[str, Any] = field(default_factory=dict)
    # Expected keys: execution_style, vectorization_risk, style_drift_risk

    # ---- Stats ----
    evidence_summary: Dict[str, Any] = field(default_factory=dict)
    # Expected keys: probe_attempts, eval_attempts, admits, near_miss,
    # best_ic, best_incremental_ic
    search_ledger_ref: str = ""

    # ---- Timestamps ----
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# ======================================================================
# LogicProposal
# ======================================================================

@dataclass
class LogicProposal:
    """A draft market hypothesis, not yet admitted as a logic.

    Stored at ``storage/logic/proposals/proposal_XXX.yaml``.
    """

    proposal_id: str = ""
    schema_version: str = "v2"
    name: str = ""
    origin_type: str = ""  # matches OriginType values
    category: str = ""

    # ---- Thesis ----
    thesis: str = ""
    mechanism: str = ""

    # ---- Observability ----
    observable_proxy: Dict[str, Any] = field(default_factory=dict)
    # Expected keys: required_fields, optional_fields, notes

    # ---- Expected Horizon ----
    expected_horizon: Dict[str, Any] = field(default_factory=dict)
    # Expected keys: formation_window, holding_window

    # ---- Implementation Space ----
    implementation_space: Dict[str, Any] = field(default_factory=dict)
    # Expected keys: preferred_families, suggested_ops, discouraged_ops

    # ---- Novelty ----
    novelty_claim: str = ""

    # ---- Probe Readiness ----
    probe_readiness: Dict[str, Any] = field(default_factory=dict)
    # Expected keys: can_probe, suggested_probe_forms

    # ---- Relations ----
    relations_guess: Dict[str, Any] = field(default_factory=dict)
    # Expected keys: possible_parent_logic, overlaps_with

    submitted_at: Optional[str] = None


# ======================================================================
# LogicReview
# ======================================================================

@dataclass
class DimensionReview:
    """Review result for a single dimension."""

    verdict: str = ""  # matches ReviewVerdict values
    score: float = 0.0
    comments: List[str] = field(default_factory=list)


@dataclass
class LogicReview:
    """Result of reviewing a LogicProposal.

    Stored at ``storage/logic/reviews/review_XXX.yaml``.
    """

    proposal_id: str = ""
    schema_version: str = "v2"

    mechanism_review: DimensionReview = field(default_factory=DimensionReview)
    feasibility_review: DimensionReview = field(default_factory=DimensionReview)
    novelty_review: DimensionReview = field(default_factory=DimensionReview)
    research_value_review: DimensionReview = field(default_factory=DimensionReview)

    overall_verdict: str = ""  # matches ReviewVerdict values
    decision: str = ""  # matches ProposalDecision values
    decision_rationale: str = ""

    reviewed_at: Optional[str] = None


# ======================================================================
# ScheduleSnapshot
# ======================================================================

@dataclass
class LogicBudget:
    """Per-logic budget allocation in a schedule."""

    logic_id: str = ""
    direction_quota: int = 0
    candidate_quota: int = 0
    eligible_this_round: bool = False
    preferred_mode: str = "dsl"
    current_focus_question: str = ""


@dataclass
class ScheduleSnapshot:
    """Point-in-time research budget allocation.

    Written by ``/logic schedule`` to
    ``storage/logic/snapshots/schedule_YYYYMMDD_HHMMSS.yaml``.
    """

    snapshot_id: str = ""
    created_at: Optional[str] = None

    # ---- Pool assignments ----
    active_pool: List[str] = field(default_factory=list)
    warm_pool: List[str] = field(default_factory=list)
    parked_pool: List[str] = field(default_factory=list)
    blocked_pool: List[str] = field(default_factory=list)

    # ---- Budgets ----
    budgets: List[LogicBudget] = field(default_factory=list)

    # ---- Global constraints ----
    global_route_limit: int = 3
    global_candidate_limit: int = 8
    python_candidate_limit: int = 2
