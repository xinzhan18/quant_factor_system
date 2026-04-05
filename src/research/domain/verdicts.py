"""Verdict enums and records.

Three levels of verdict:
  1. **CandidateVerdict** — per-candidate (admit / replace / reject / defer)
  2. **RouteVerdict**     — per-route (pass / borderline / fail)
  3. **LogicRecommendation** — per-logic (continue / warm / park / saturate / kill)

Each verdict carries a list of ``ReasonCode`` entries plus optional
free-text explanation.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

from research.domain.reason_codes import ReasonCode


# ======================================================================
# Enums
# ======================================================================

class CandidateVerdict(enum.Enum):
    """Outcome for a single candidate after judge evaluation."""

    ADMIT = "admit"
    REPLACE = "replace"
    REJECT = "reject"
    DEFER = "defer"  # needs additional evidence


class RouteVerdict(enum.Enum):
    """Outcome for a research route after probe / evaluation."""

    PASS = "pass"
    BORDERLINE = "borderline"
    FAIL = "fail"


class LogicRecommendation(enum.Enum):
    """Recommended lifecycle action for a logic after a batch round."""

    CONTINUE = "continue"
    WARM = "warm"
    PARK = "park"
    SATURATE = "saturate"
    KILL = "kill"


# ======================================================================
# Bucket enums (used in JudgePacket candidate briefs)
# ======================================================================

class EffectBucket(enum.Enum):
    """Validation effect strength bucket."""

    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    NONE = "none"


class StabilityBucket(enum.Enum):
    """Stability assessment bucket."""

    ROBUST = "robust"
    ACCEPTABLE = "acceptable"
    FRAGILE = "fragile"
    UNSTABLE = "unstable"


class RedundancyBucket(enum.Enum):
    """Redundancy assessment bucket."""

    NOVEL = "novel"
    LOW_OVERLAP = "low_overlap"
    MODERATE_OVERLAP = "moderate_overlap"
    HIGH_OVERLAP = "high_overlap"


class FeasibilityBucket(enum.Enum):
    """Feasibility assessment bucket."""

    GOOD = "good"
    ACCEPTABLE = "acceptable"
    MARGINAL = "marginal"
    INFEASIBLE = "infeasible"


# ======================================================================
# Verdict Records
# ======================================================================

@dataclass
class CandidateVerdictRecord:
    """Full verdict for a single candidate.

    Created by the judge after reviewing all evidence.
    """

    candidate_id: str
    verdict: CandidateVerdict
    reason_codes: List[ReasonCode] = field(default_factory=list)
    explanation: str = ""
    replace_target_id: Optional[str] = None  # only if verdict == REPLACE
    confidence: float = 0.0  # 0.0 - 1.0

    # Bucket assignments
    effect_bucket: Optional[EffectBucket] = None
    stability_bucket: Optional[StabilityBucket] = None
    redundancy_bucket: Optional[RedundancyBucket] = None
    feasibility_bucket: Optional[FeasibilityBucket] = None

    # Flags
    support_window_warning: bool = False
    holdout_review_recommended: bool = False

    judged_at: Optional[datetime] = None

    @property
    def has_fatal(self) -> bool:
        return any(rc.is_fatal for rc in self.reason_codes)


@dataclass
class RouteVerdictRecord:
    """Verdict for a research route (after probe or batch evaluation)."""

    route_id: str
    logic_id: str
    verdict: RouteVerdict
    reason_codes: List[ReasonCode] = field(default_factory=list)
    explanation: str = ""

    # Probe-level metrics (populated after probe)
    probe_ic_mean: Optional[float] = None
    probe_ic_seg_a: Optional[float] = None
    probe_ic_seg_b: Optional[float] = None
    neighbor_consistency: Optional[float] = None

    judged_at: Optional[datetime] = None


@dataclass
class LogicRecommendationRecord:
    """Lifecycle recommendation for a logic after a batch round."""

    logic_id: str
    recommendation: LogicRecommendation
    reason_codes: List[ReasonCode] = field(default_factory=list)
    explanation: str = ""

    # Evidence summary
    probe_attempts: int = 0
    eval_attempts: int = 0
    admits: int = 0
    near_misses: int = 0

    judged_at: Optional[datetime] = None


# ======================================================================
# Batch-level report
# ======================================================================

@dataclass
class BatchJudgeReport:
    """Aggregated judge output for a full batch.

    This is the top-level artifact produced by the judge skill.
    """

    batch_id: str
    candidate_verdicts: List[CandidateVerdictRecord] = field(default_factory=list)
    route_verdicts: List[RouteVerdictRecord] = field(default_factory=list)
    logic_recommendations: List[LogicRecommendationRecord] = field(
        default_factory=list
    )

    summary: str = ""
    judged_at: Optional[datetime] = None

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def admitted(self) -> List[CandidateVerdictRecord]:
        return [
            v for v in self.candidate_verdicts
            if v.verdict in (CandidateVerdict.ADMIT, CandidateVerdict.REPLACE)
        ]

    @property
    def rejected(self) -> List[CandidateVerdictRecord]:
        return [
            v for v in self.candidate_verdicts
            if v.verdict is CandidateVerdict.REJECT
        ]
