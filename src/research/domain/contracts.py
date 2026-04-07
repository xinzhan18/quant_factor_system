"""Logic-layer contracts centered on the long-lived LogicCard object."""

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
