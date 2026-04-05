"""Batch scheduler -- decide when to start the next research batch.

Rules:
    - Auto-continue if reserves exist from the previous batch
    - Require human confirmation if all routes were killed
    - Frequency limit: at most 2 batches per week
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from research.judge.verdict_builder import BatchJudgeReport


# Maximum batches per 7-day rolling window
MAX_BATCHES_PER_WEEK = 2

# Minimum gap between batches (in days)
MIN_BATCH_GAP_DAYS = 2


@dataclass
class SchedulerState:
    """Persistent state for the batch scheduler."""

    recent_batch_dates: List[str] = field(default_factory=list)
    last_batch_id: str = ""
    last_batch_had_reserves: bool = False
    last_batch_all_killed: bool = False
    human_confirmed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recent_batch_dates": list(self.recent_batch_dates),
            "last_batch_id": self.last_batch_id,
            "last_batch_had_reserves": self.last_batch_had_reserves,
            "last_batch_all_killed": self.last_batch_all_killed,
            "human_confirmed": self.human_confirmed,
        }


@dataclass
class SchedulerDecision:
    """Output of should_start_next()."""

    can_start: bool = False
    reason: str = ""
    needs_human_confirmation: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "can_start": self.can_start,
            "reason": self.reason,
            "needs_human_confirmation": self.needs_human_confirmation,
        }


class BatchScheduler:
    """Decide whether the next batch can start."""

    def __init__(self, state: Optional[SchedulerState] = None) -> None:
        self._state = state or SchedulerState()

    @property
    def state(self) -> SchedulerState:
        return self._state

    def update_from_report(self, report: BatchJudgeReport) -> None:
        """Update scheduler state from a completed batch judge report."""
        summary = report.summary
        now_str = datetime.now().strftime("%Y-%m-%d")

        self._state.last_batch_id = report.batch_id
        self._state.last_batch_had_reserves = summary["reserves"] > 0
        self._state.last_batch_all_killed = (
            summary["total_routes"] > 0
            and summary["route_kills"] == summary["total_routes"]
        )
        self._state.human_confirmed = False

        # Track dates for frequency limiting
        self._state.recent_batch_dates.append(now_str)
        # Keep only last 14 days
        cutoff = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
        self._state.recent_batch_dates = [
            d for d in self._state.recent_batch_dates if d >= cutoff
        ]

    def confirm_human(self) -> None:
        """Record human confirmation to proceed after all-killed batch."""
        self._state.human_confirmed = True

    def should_start_next(
        self, now: Optional[datetime] = None
    ) -> SchedulerDecision:
        """Decide whether the next batch should start.

        Returns:
            SchedulerDecision with can_start, reason, and whether
            human confirmation is needed.
        """
        now = now or datetime.now()
        now_str = now.strftime("%Y-%m-%d")

        # Frequency check: count batches in last 7 days
        week_ago = (now - timedelta(days=7)).strftime("%Y-%m-%d")
        recent = [d for d in self._state.recent_batch_dates if d >= week_ago]

        if len(recent) >= MAX_BATCHES_PER_WEEK:
            return SchedulerDecision(
                can_start=False,
                reason=f"frequency_limit: {len(recent)}/{MAX_BATCHES_PER_WEEK} batches this week",
            )

        # Gap check: last batch must be at least MIN_BATCH_GAP_DAYS ago
        if self._state.recent_batch_dates:
            last_date_str = max(self._state.recent_batch_dates)
            try:
                last_date = datetime.strptime(last_date_str, "%Y-%m-%d")
                if (now - last_date).days < MIN_BATCH_GAP_DAYS:
                    return SchedulerDecision(
                        can_start=False,
                        reason=f"min_gap: last batch was {last_date_str}, need {MIN_BATCH_GAP_DAYS}d gap",
                    )
            except ValueError:
                pass

        # All-killed: need human confirmation
        if self._state.last_batch_all_killed and not self._state.human_confirmed:
            return SchedulerDecision(
                can_start=False,
                reason="all_routes_killed: human confirmation required",
                needs_human_confirmation=True,
            )

        # Auto-continue if reserves exist
        if self._state.last_batch_had_reserves:
            return SchedulerDecision(
                can_start=True,
                reason="auto_continue: reserves exist from last batch",
            )

        # Default: can start if no blockers
        return SchedulerDecision(
            can_start=True,
            reason="ready: no blockers",
        )
