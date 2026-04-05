"""Schedule generation for logic cards across 7 scoring dimensions.

The scheduler reads all logic cards, scores each on 7 dimensions,
and produces a ScheduleResult that partitions logics into pools
(active/warm/parked/blocked) with per-logic budgets.

Scoring dimensions:
1. priority       - inherits from card priority (high=3, medium=2, low=1)
2. lifecycle      - bonus for active/productive, penalty for saturated/dead
3. productivity   - ratio of admitted factors to generated factors
4. saturation     - penalty when recent rounds yield no new admits
5. bottleneck     - penalty when stuck (high generated, low admitted)
6. discovery_need - bonus when category is underrepresented
7. validation_exposure - penalty when too many active logics in same category
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from research.logic._yaml_utils import dump_yaml, now_ts
from research.logic.cards import LogicCard

logger = logging.getLogger(__name__)

# --- Scoring weights (sum to 1.0) ---
WEIGHTS = {
    "priority": 0.20,
    "lifecycle": 0.15,
    "productivity": 0.20,
    "saturation": 0.15,
    "bottleneck": 0.10,
    "discovery_need": 0.10,
    "validation_exposure": 0.10,
}

PRIORITY_SCORES = {"high": 1.0, "medium": 0.6, "low": 0.3}

LIFECYCLE_SCORES = {
    "proposed": 0.5,
    "active": 1.0,
    "warm": 0.7,
    "productive": 0.9,
    "saturated": 0.2,
    "parked": 0.0,
    "dead": 0.0,
}

# Thresholds for pool assignment
ACTIVE_THRESHOLD = 0.45
WARM_THRESHOLD = 0.25

# Default quotas
DEFAULT_DIRECTION_QUOTA = 2
DEFAULT_CANDIDATE_QUOTA = 4


@dataclass
class LogicBudget:
    """Per-logic allocation within a schedule."""

    logic_id: str
    score: float
    pool: str  # active / warm / parked / blocked
    direction_quota: int = DEFAULT_DIRECTION_QUOTA
    candidate_quota: int = DEFAULT_CANDIDATE_QUOTA

    def to_dict(self) -> Dict[str, Any]:
        return {
            "logic_id": self.logic_id,
            "score": round(self.score, 4),
            "pool": self.pool,
            "direction_quota": self.direction_quota,
            "candidate_quota": self.candidate_quota,
        }


@dataclass
class ScheduleResult:
    """Output of a scheduling pass."""

    active_pool: List[LogicBudget] = field(default_factory=list)
    warm_pool: List[LogicBudget] = field(default_factory=list)
    parked_pool: List[LogicBudget] = field(default_factory=list)
    blocked_pool: List[LogicBudget] = field(default_factory=list)
    global_constraints: Dict[str, Any] = field(default_factory=dict)
    generated_at: str = ""

    def __post_init__(self) -> None:
        if not self.generated_at:
            self.generated_at = now_ts()

    @property
    def all_budgets(self) -> List[LogicBudget]:
        return (
            self.active_pool
            + self.warm_pool
            + self.parked_pool
            + self.blocked_pool
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "active_pool": [b.to_dict() for b in self.active_pool],
            "warm_pool": [b.to_dict() for b in self.warm_pool],
            "parked_pool": [b.to_dict() for b in self.parked_pool],
            "blocked_pool": [b.to_dict() for b in self.blocked_pool],
            "global_constraints": self.global_constraints,
        }


class LogicScheduler:
    """Score logic cards and generate a schedule with pool assignments."""

    def __init__(
        self,
        *,
        max_active: int = 3,
        max_total_routes: int = 6,
        max_total_candidates: int = 12,
    ) -> None:
        self._max_active = max_active
        self._max_total_routes = max_total_routes
        self._max_total_candidates = max_total_candidates

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_schedule(
        self,
        cards: List[LogicCard],
        *,
        category_counts: Optional[Dict[str, int]] = None,
    ) -> ScheduleResult:
        """Score all cards and assign them to pools.

        Parameters
        ----------
        cards:
            All logic cards (any status).
        category_counts:
            Map of category -> number of admitted factors. Used for the
            discovery_need and validation_exposure dimensions. If None,
            counts are derived from the cards themselves.
        """
        if category_counts is None:
            category_counts = self._derive_category_counts(cards)

        scored: List[tuple] = []
        for card in cards:
            score = self._score_card(card, category_counts)
            scored.append((card, score))

        # Sort descending by score
        scored.sort(key=lambda x: x[1], reverse=True)

        result = ScheduleResult(
            global_constraints={
                "max_active": self._max_active,
                "max_total_routes": self._max_total_routes,
                "max_total_candidates": self._max_total_candidates,
            },
        )

        active_count = 0
        for card, score in scored:
            # Dead/parked cards go directly to their pools
            if card.status in ("dead", "parked"):
                budget = LogicBudget(
                    logic_id=card.logic_id,
                    score=score,
                    pool=card.status,
                    direction_quota=0,
                    candidate_quota=0,
                )
                if card.status == "dead":
                    result.blocked_pool.append(budget)
                else:
                    result.parked_pool.append(budget)
                continue

            # Assign to pool based on score and capacity
            if score >= ACTIVE_THRESHOLD and active_count < self._max_active:
                direction_q = card.contract.direction_quota or DEFAULT_DIRECTION_QUOTA
                candidate_q = card.contract.candidate_quota or DEFAULT_CANDIDATE_QUOTA
                budget = LogicBudget(
                    logic_id=card.logic_id,
                    score=score,
                    pool="active",
                    direction_quota=direction_q,
                    candidate_quota=candidate_q,
                )
                result.active_pool.append(budget)
                active_count += 1
            elif score >= WARM_THRESHOLD:
                budget = LogicBudget(
                    logic_id=card.logic_id,
                    score=score,
                    pool="warm",
                    direction_quota=1,
                    candidate_quota=2,
                )
                result.warm_pool.append(budget)
            else:
                budget = LogicBudget(
                    logic_id=card.logic_id,
                    score=score,
                    pool="parked",
                    direction_quota=0,
                    candidate_quota=0,
                )
                result.parked_pool.append(budget)

        return result

    def save_schedule(
        self, storage_dir: Path, result: ScheduleResult
    ) -> Path:
        """Persist schedule snapshot to storage/logic/snapshots/."""
        snapshots_dir = storage_dir / "logic" / "snapshots"
        snapshots_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = snapshots_dir / f"schedule_{ts}.yaml"
        dump_yaml(path, result.to_dict())
        logger.info("Saved schedule snapshot at %s", path)
        return path

    # ------------------------------------------------------------------
    # Scoring internals
    # ------------------------------------------------------------------

    def _score_card(
        self,
        card: LogicCard,
        category_counts: Dict[str, int],
    ) -> float:
        """Compute weighted score for a single card."""
        dims: Dict[str, float] = {}

        # 1. Priority
        dims["priority"] = PRIORITY_SCORES.get(card.priority, 0.3)

        # 2. Lifecycle
        dims["lifecycle"] = LIFECYCLE_SCORES.get(card.status, 0.0)

        # 3. Productivity
        ev = card.evidence_summary
        generated = ev.get("factors_generated", 0)
        admitted = ev.get("factors_admitted", 0)
        if generated > 0:
            dims["productivity"] = min(admitted / generated, 1.0)
        else:
            dims["productivity"] = 0.5  # neutral for new logics

        # 4. Saturation (inverse of rounds_without_admit, capped)
        rounds_dry = ev.get("rounds_without_admit", 0)
        dims["saturation"] = max(0.0, 1.0 - rounds_dry * 0.2)

        # 5. Bottleneck (high generated + low admitted = stuck)
        if generated > 5 and admitted == 0:
            dims["bottleneck"] = 0.0
        elif generated > 0:
            dims["bottleneck"] = min(admitted / max(generated, 1), 1.0)
        else:
            dims["bottleneck"] = 0.5

        # 6. Discovery need (underrepresented category)
        cat_count = category_counts.get(card.category, 0)
        if cat_count <= 1:
            dims["discovery_need"] = 1.0
        elif cat_count <= 3:
            dims["discovery_need"] = 0.6
        else:
            dims["discovery_need"] = 0.3

        # 7. Validation exposure (penalty for crowded categories)
        if cat_count >= 5:
            dims["validation_exposure"] = 0.2
        elif cat_count >= 3:
            dims["validation_exposure"] = 0.5
        else:
            dims["validation_exposure"] = 1.0

        # Weighted sum
        total = sum(WEIGHTS[k] * dims[k] for k in WEIGHTS)
        return total

    @staticmethod
    def _derive_category_counts(cards: List[LogicCard]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for card in cards:
            if card.status not in ("dead", "parked"):
                counts[card.category] = counts.get(card.category, 0) + 1
        return counts
