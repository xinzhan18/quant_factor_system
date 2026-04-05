"""Write permission definitions and ownership map.

Encodes the §7 permission table from the memory architecture:
which actor may write which governance objects, and at what level.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass
from typing import Dict, FrozenSet, List, Optional


class WriteLevel(enum.Enum):
    """Write-access level for governance mutations.

    level_1: Direct execution with audit receipt.  Covers routine
             objects such as factor_registry, logic_card, research_state.
    level_2: Requires repeated evidence before writing.  Used for
             high-impact objects like forbidden.
    """

    level_1 = "level_1"
    level_2 = "level_2"


class Actor(enum.Enum):
    """Known actors in the research system."""

    guarded_writer = "guarded_writer"
    judge = "judge"
    logic = "logic"
    idea = "idea"
    execute = "execute"
    report = "report"


# ---------------------------------------------------------------------------
# Target objects that governance controls
# ---------------------------------------------------------------------------

class TargetObject(enum.Enum):
    factor_registry = "factor_registry"
    logic_card = "logic_card"
    route_card = "route_card"
    research_state = "research_state"
    forbidden = "forbidden"
    judge_report = "judge_report"
    search_ledger = "search_ledger"
    batch_result = "batch_result"
    batch_manifest = "batch_manifest"
    idea_report = "idea_report"
    execute_report = "execute_report"


# ---------------------------------------------------------------------------
# Permission entry
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PermissionEntry:
    target: TargetObject
    level: WriteLevel
    allowed_actions: FrozenSet[str]


# ---------------------------------------------------------------------------
# The canonical permission map  (memory.md §7)
# ---------------------------------------------------------------------------

_GUARDED_WRITER_PERMISSIONS: List[PermissionEntry] = [
    PermissionEntry(
        target=TargetObject.factor_registry,
        level=WriteLevel.level_1,
        allowed_actions=frozenset({"admit", "retire", "replace", "update"}),
    ),
    PermissionEntry(
        target=TargetObject.logic_card,
        level=WriteLevel.level_1,
        allowed_actions=frozenset({"create", "update", "transition"}),
    ),
    PermissionEntry(
        target=TargetObject.route_card,
        level=WriteLevel.level_1,
        allowed_actions=frozenset({"create", "update", "transition"}),
    ),
    PermissionEntry(
        target=TargetObject.research_state,
        level=WriteLevel.level_1,
        allowed_actions=frozenset({"update"}),
    ),
    PermissionEntry(
        target=TargetObject.forbidden,
        level=WriteLevel.level_2,
        allowed_actions=frozenset({"add", "reassess", "retire", "reactivate"}),
    ),
]

_JUDGE_PERMISSIONS: List[PermissionEntry] = [
    PermissionEntry(
        target=TargetObject.judge_report,
        level=WriteLevel.level_1,
        allowed_actions=frozenset({"create"}),
    ),
    PermissionEntry(
        target=TargetObject.search_ledger,
        level=WriteLevel.level_1,
        allowed_actions=frozenset({"append"}),
    ),
]

_IDEA_PERMISSIONS: List[PermissionEntry] = [
    PermissionEntry(
        target=TargetObject.batch_manifest,
        level=WriteLevel.level_1,
        allowed_actions=frozenset({"create"}),
    ),
    PermissionEntry(
        target=TargetObject.idea_report,
        level=WriteLevel.level_1,
        allowed_actions=frozenset({"create"}),
    ),
    PermissionEntry(
        target=TargetObject.route_card,
        level=WriteLevel.level_1,
        allowed_actions=frozenset({"create", "update"}),
    ),
]

_EXECUTE_PERMISSIONS: List[PermissionEntry] = [
    PermissionEntry(
        target=TargetObject.batch_result,
        level=WriteLevel.level_1,
        allowed_actions=frozenset({"create"}),
    ),
    PermissionEntry(
        target=TargetObject.execute_report,
        level=WriteLevel.level_1,
        allowed_actions=frozenset({"create"}),
    ),
]

# ---------------------------------------------------------------------------
# Public permission map: actor -> list of PermissionEntry
# ---------------------------------------------------------------------------

WRITE_PERMISSIONS: Dict[Actor, List[PermissionEntry]] = {
    Actor.guarded_writer: _GUARDED_WRITER_PERMISSIONS,
    Actor.judge: _JUDGE_PERMISSIONS,
    Actor.idea: _IDEA_PERMISSIONS,
    Actor.execute: _EXECUTE_PERMISSIONS,
}


def actor_can_write(actor: Actor, target: TargetObject, action: str) -> bool:
    """Return True if *actor* is allowed to perform *action* on *target*."""
    entries = WRITE_PERMISSIONS.get(actor, [])
    for entry in entries:
        if entry.target == target and action in entry.allowed_actions:
            return True
    return False


def required_level(actor: Actor, target: TargetObject) -> Optional[WriteLevel]:
    """Return the WriteLevel required for *actor* to touch *target*, or None."""
    entries = WRITE_PERMISSIONS.get(actor, [])
    for entry in entries:
        if entry.target == target:
            return entry.level
    return None
