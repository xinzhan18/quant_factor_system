"""Logic management — hypothesis lifecycle for the outer research loop.

Submodules:
- cards:           LogicCard CRUD with YAML persistence
- scheduler:       Schedule generation across 7 scoring dimensions
- lifecycle:       State transitions, family promotion, arbitration
- family_registry: Family CRUD (registered/provisional/unknown)
"""

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
