"""Tests for CycleController -- combined scheduler + holdout queue."""
from datetime import datetime, timedelta

from research.controller.batch_scheduler import BatchScheduler, MIN_BATCH_GAP_DAYS
from research.controller.holdout_queue import HoldoutQueue, DEFAULT_DEADLINE_DAYS
from research.controller.cycle_controller import CycleController, NextActions
from research.judge.candidate_judge import CandidateVerdict
from research.judge.route_judge import RouteVerdict
from research.judge.verdict_builder import BatchJudgeReport


def _make_report(
    batch_id: str = "batch_042",
    candidate_verdicts: list = None,
    route_verdicts: list = None,
) -> BatchJudgeReport:
    return BatchJudgeReport(
        batch_id=batch_id,
        candidate_verdicts=candidate_verdicts or [],
        route_verdicts=route_verdicts or [],
    )


class TestCycleControllerBasic:
    def test_default_can_start(self):
        ctrl = CycleController()
        actions = ctrl.next_actions()
        assert actions.can_start_batch
        assert actions.expired_count == 0

    def test_next_actions_to_dict(self):
        ctrl = CycleController()
        actions = ctrl.next_actions()
        d = actions.to_dict()
        assert "can_start_batch" in d
        assert "holdout_reviews_due" in d


class TestCycleControllerOnBatchComplete:
    def test_updates_scheduler(self):
        ctrl = CycleController()
        report = _make_report(
            candidate_verdicts=[
                CandidateVerdict(candidate_id="C001", verdict="reserve"),
            ],
            route_verdicts=[
                RouteVerdict(route_id="R001", experiment_lineage_tag="ELT_1", verdict="continue"),
            ],
        )
        ctrl.on_batch_complete(report)
        assert ctrl.scheduler.state.last_batch_id == "batch_042"
        assert ctrl.scheduler.state.last_batch_had_reserves

    def test_enqueues_holdout_reviews(self):
        ctrl = CycleController()
        report = _make_report(
            candidate_verdicts=[
                CandidateVerdict(
                    candidate_id="C001",
                    verdict="reserve",
                    holdout_review_required=True,
                    evidence_summary={"logic_id": "L021", "family_id": "FM_breakout"},
                ),
                CandidateVerdict(candidate_id="C002", verdict="admit"),
            ],
        )
        ctrl.on_batch_complete(report)
        pending = ctrl.holdout_queue.pending()
        assert len(pending) == 1
        assert pending[0].candidate_id == "C001"


class TestCycleControllerExpiry:
    def test_expires_overdue_holdouts(self):
        now = datetime(2026, 4, 5, 12, 0, 0)
        q = HoldoutQueue()
        q.enqueue("C001", "L021", "FM_breakout", "batch_042", now=now)
        ctrl = CycleController(holdout_queue=q)
        future = now + timedelta(days=DEFAULT_DEADLINE_DAYS + 1)
        actions = ctrl.next_actions(now=future)
        assert actions.expired_count == 1
        assert len(actions.holdout_reviews_due) == 0


class TestCycleControllerHoldoutBeforeBatch:
    def test_pending_holdouts_listed(self):
        now = datetime(2026, 4, 5, 12, 0, 0)
        q = HoldoutQueue()
        q.enqueue("C001", "L021", "FM_breakout", "batch_042", now=now)
        ctrl = CycleController(holdout_queue=q)
        # Still within deadline
        check_time = now + timedelta(days=1)
        actions = ctrl.next_actions(now=check_time)
        assert "C001" in actions.holdout_reviews_due


class TestCycleControllerAllKilled:
    def test_all_killed_blocks_next(self):
        ctrl = CycleController()
        report = _make_report(
            route_verdicts=[
                RouteVerdict(route_id="R001", experiment_lineage_tag="ELT_1", verdict="kill"),
                RouteVerdict(route_id="R002", experiment_lineage_tag="ELT_2", verdict="kill"),
            ],
        )
        ctrl.on_batch_complete(report)
        future = datetime.now() + timedelta(days=MIN_BATCH_GAP_DAYS + 1)
        actions = ctrl.next_actions(now=future)
        assert not actions.can_start_batch
        assert actions.needs_human_confirmation
