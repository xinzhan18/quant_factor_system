"""Research domain types — re-exports for convenience.

Usage::

    from research.domain import FactorRecord, CandidateRecord, RouteRecord
    from research.domain import ReasonCode, Severity
    from research.domain import CandidateVerdict, RouteVerdict
"""

from research.domain.schema import (
    CandidateRecord,
    Decision,
    EvaluationContext,
    FactorRecord,
    FactorStatus,
    Lineage,
    MutationType,
    RouteRecord,
    RouteStatus,
    RouteType,
    SourceType,
)
from research.domain.reason_codes import ReasonCode, Severity
from research.domain.verdicts import (
    BatchJudgeReport,
    CandidateVerdict,
    CandidateVerdictRecord,
    EffectBucket,
    FeasibilityBucket,
    LogicRecommendation,
    LogicRecommendationRecord,
    RedundancyBucket,
    RouteVerdict,
    RouteVerdictRecord,
    StabilityBucket,
)
from research.domain.experiment_lineage import ExperimentLineageTag
from research.domain.sample_policy import SamplePolicy, SupportWindow, ValidationWindow
from research.domain.config import (
    EvaluationProfile,
    ResearchConfig,
    UniverseConfig,
)
from research.domain.contracts import LogicCard
from research.domain.governance import (
    GuardedWriteReceipt,
    GuardedWriteRequest,
    WriteLevel,
    WritableObject,
)

__all__ = [
    # schema
    "FactorRecord",
    "CandidateRecord",
    "RouteRecord",
    "Lineage",
    "EvaluationContext",
    "SourceType",
    "FactorStatus",
    "RouteType",
    "RouteStatus",
    "Decision",
    "MutationType",
    # reason codes
    "ReasonCode",
    "Severity",
    # verdicts
    "CandidateVerdict",
    "CandidateVerdictRecord",
    "RouteVerdict",
    "RouteVerdictRecord",
    "LogicRecommendation",
    "LogicRecommendationRecord",
    "BatchJudgeReport",
    "EffectBucket",
    "StabilityBucket",
    "RedundancyBucket",
    "FeasibilityBucket",
    # experiment lineage
    "ExperimentLineageTag",
    # sample policy
    "SamplePolicy",
    "ValidationWindow",
    "SupportWindow",
    # config
    "ResearchConfig",
    "EvaluationProfile",
    "UniverseConfig",
    "LogicCard",
    # governance
    "GuardedWriteRequest",
    "GuardedWriteReceipt",
    "WriteLevel",
    "WritableObject",
]
