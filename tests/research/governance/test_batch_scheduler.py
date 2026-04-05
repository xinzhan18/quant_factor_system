"""Tests for BatchScheduler -- batch start decision logic."""
from datetime import datetime, timedelta

from research.governance.batch_scheduler import (
    BatchScheduler,
    SchedulerState,
    MAX_BATCHES_PER_WEEK,
    MIN_BATCH_GAP_DAYS,
)
from research.judge.candidate_judge import CandidateVerdict
from research.judge.route_judge import RouteVerdict
from research.judge.verdict_builder import BatchJudgeReport


def _make_report(
    batch_id: str = "batch_042",
    n_reserves: int = 0,
    n_route_kills: int = 0,
    n_routes: int = 1,
) -> BatchJudgeReport:
    """Helper to build a minimal report."""
    cvs = [
        CandidateVerdict(candidate_id=f"C{i:03d}", verdict="reserve")
        for i in range(n_reserves)
    ]
    rvs = []
    for i in range(n_routes):
        v = "kill" if i < n_route_kills else "continue"
        rvs.append(
            RouteVerdict(
                route_id=f"R{i:03d}",
                experiment_lineage_tag=f"ELT_{i}",
                verdict=v,
            )
        )
    return BatchJudgeReport(
        batch_id=batch_id,
        candidate_verdicts=cvs,
        route_verdicts=rvs,
    )


class TestBatchSchedulerAutoStart:
    def test_ready_by_default(self):
        scheduler = BatchScheduler()
        decision = scheduler.should_start_next()
        assert decision.can_start

    def test_auto_continue_with_reserves(self):
        scheduler = BatchScheduler()
        report = _make_report(n_reserves=2, n_routes=1)
        scheduler.update_from_report(report)
        # Need to satisfy the gap check -- advance time
        future = datetime.now() + timedelta(days=MIN_BATCH_GAP_DAYS + 1)
        decision = scheduler.should_start_next(now=future)
        assert decision.can_start
        assert "reserves" in decision.reason


class TestBatchSchedulerKill:
    def test_all_killed_needs_human(self):
        scheduler = BatchScheduler()
        report = _make_report(n_routes=2, n_route_kills=2)
        scheduler.update_from_report(report)
        future = datetime.now() + timedelta(days=MIN_BATCH_GAP_DAYS + 1)
        decision = scheduler.should_start_next(now=future)
        assert not decision.can_start
        assert decision.needs_human_confirmation

    def test_human_confirmation_unblocks(self):
        scheduler = BatchScheduler()
        report = _make_report(n_routes=2, n_route_kills=2)
        scheduler.update_from_report(report)
        scheduler.confirm_human()
        future = datetime.now() + timedelta(days=MIN_BATCH_GAP_DAYS + 1)
        decision = scheduler.should_start_next(now=future)
        assert decision.can_start


class TestBatchSchedulerFrequency:
    def test_frequency_limit(self):
        state = SchedulerState()
        now = datetime.now()
        # Fill up the week
        for i in range(MAX_BATCHES_PER_WEEK):
            date_str = (now - timedelta(days=i)).strftime("%Y-%m-%d")
            state.recent_batch_dates.append(date_str)
        scheduler = BatchScheduler(state=state)
        decision = scheduler.should_start_next(now=now)
        assert not decision.can_start
        assert "frequency_limit" in decision.reason

    def test_min_gap_enforced(self):
        state = SchedulerState()
        now = datetime.now()
        state.recent_batch_dates.append(now.strftime("%Y-%m-%d"))
        scheduler = BatchScheduler(state=state)
        # Check same day -- should be blocked
        decision = scheduler.should_start_next(now=now)
        assert not decision.can_start
        assert "min_gap" in decision.reason

    def test_gap_satisfied(self):
        state = SchedulerState()
        now = datetime.now()
        old_date = (now - timedelta(days=MIN_BATCH_GAP_DAYS + 1)).strftime("%Y-%m-%d")
        state.recent_batch_dates.append(old_date)
        scheduler = BatchScheduler(state=state)
        decision = scheduler.should_start_next(now=now)
        assert decision.can_start


class TestSchedulerStateSerialization:
    def test_to_dict(self):
        state = SchedulerState(
            recent_batch_dates=["2026-04-01", "2026-04-03"],
            last_batch_id="batch_042",
            last_batch_had_reserves=True,
        )
        d = state.to_dict()
        assert d["last_batch_id"] == "batch_042"
        assert len(d["recent_batch_dates"]) == 2
