"""Logic management — hypothesis lifecycle for the outer research loop.

Submodules:
- proposals:       Create and validate LogicProposal objects
- reviews:         4-dimension review gate (mechanism/feasibility/novelty/research_value)
- cards:           LogicCard CRUD with YAML persistence
- scheduler:       Schedule generation across 7 scoring dimensions
- lifecycle:       State transitions, family promotion, arbitration
- family_registry: Family CRUD (registered/provisional/unknown)
"""

from research.logic.proposals import LogicProposal, create_proposal
from research.logic.reviews import LogicReview, review_proposal
from research.logic.cards import LogicCard, LogicCardStore
from research.logic.scheduler import LogicScheduler, ScheduleResult
from research.logic.lifecycle import (
    LifecycleManager,
    validate_transition,
    build_transition_record,
    validate_promotion,
    build_promotion_record,
)
from research.logic.family_registry import FamilyRegistry, FamilyRecord

__all__ = [
    "LogicProposal",
    "create_proposal",
    "LogicReview",
    "review_proposal",
    "LogicCard",
    "LogicCardStore",
    "LogicScheduler",
    "ScheduleResult",
    "LifecycleManager",
    "validate_transition",
    "build_transition_record",
    "validate_promotion",
    "build_promotion_record",
    "FamilyRegistry",
    "FamilyRecord",
]
