"""Cycle controller -- combine scheduler + holdout queue into next_actions.

The CycleController is the top-level orchestrator that:
    1. Expires overdue holdout entries
    2. Checks if the next batch should start
    3. Identifies holdout reviews due before next batch
    4. Returns a structured next_actions dict
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from research.controller.batch_scheduler import (
    BatchScheduler,
    SchedulerDecision,
    SchedulerState,
)
from research.controller.holdout_queue import HoldoutEntry, HoldoutQueue
from research.judge.verdict_builder import BatchJudgeReport


@dataclass
class NextActions:
    """Structured output of what should happen next in the research cycle."""

    # Batch scheduling
    can_start_batch: bool = False
    batch_reason: str = ""
    needs_human_confirmation: bool = False

    # Holdout reviews due
    holdout_reviews_due: List[str] = field(default_factory=list)

    # Expired holdouts
    expired_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "can_start_batch": self.can_start_batch,
            "batch_reason": self.batch_reason,
            "needs_human_confirmation": self.needs_human_confirmation,
            "holdout_reviews_due": list(self.holdout_reviews_due),
            "expired_count": self.expired_count,
        }


class CycleController:
    """Top-level cycle controller combining scheduler and holdout queue."""

    def __init__(
        self,
        scheduler: Optional[BatchScheduler] = None,
        holdout_queue: Optional[HoldoutQueue] = None,
    ) -> None:
        self._scheduler = scheduler or BatchScheduler()
        self._holdout_queue = holdout_queue or HoldoutQueue()

    @property
    def scheduler(self) -> BatchScheduler:
        return self._scheduler

    @property
    def holdout_queue(self) -> HoldoutQueue:
        return self._holdout_queue

    def on_batch_complete(self, report: BatchJudgeReport) -> None:
        """Update state after a batch completes.

        1. Update scheduler state from report
        2. Enqueue holdout reviews for flagged candidates
        """
        self._scheduler.update_from_report(report)

        # Enqueue holdout reviews for candidates that need them
        for cv in report.candidate_verdicts:
            if cv.holdout_review_required:
                # Extract logic_id and family_id from evidence if available
                logic_id = cv.evidence_summary.get("logic_id", "")
                family_id = cv.evidence_summary.get("family_id", "")
                self._holdout_queue.enqueue(
                    candidate_id=cv.candidate_id,
                    logic_id=logic_id,
                    family_id=family_id,
                    batch_id=report.batch_id,
                )

    def next_actions(self, now: Optional[datetime] = None) -> NextActions:
        """Determine what should happen next.

        Steps:
        1. Expire overdue holdout entries
        2. Check scheduler readiness
        3. List pending holdout reviews that should run before next batch
        """
        now = now or datetime.now()

        # 1. Expire overdue holdouts
        expired_count = self._holdout_queue.expire_past_deadline(now=now)

        # 2. Check scheduler
        decision = self._scheduler.should_start_next(now=now)

        # 3. List pending holdouts
        pending_ids = [e.candidate_id for e in self._holdout_queue.pending()]

        return NextActions(
            can_start_batch=decision.can_start,
            batch_reason=decision.reason,
            needs_human_confirmation=decision.needs_human_confirmation,
            holdout_reviews_due=pending_ids,
            expired_count=expired_count,
        )
