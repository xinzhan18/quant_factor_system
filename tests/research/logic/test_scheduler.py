"""Tests for research.logic.scheduler — 7-dimension schedule generation."""
import pytest

from research.logic.cards import ExplorationContract, LogicCard
from research.logic.scheduler import (
    LogicScheduler,
    ScheduleResult,
    ACTIVE_THRESHOLD,
    WARM_THRESHOLD,
)


def _make_card(
    logic_id: str = "L001",
    name: str = "test",
    category: str = "volume_price",
    status: str = "active",
    priority: str = "high",
    factors_generated: int = 0,
    factors_admitted: int = 0,
    rounds_without_admit: int = 0,
    direction_quota: int = 2,
    candidate_quota: int = 4,
    deepening_threads: list = None,
    next_actions: list = None,
) -> LogicCard:
    return LogicCard(
        logic_id=logic_id,
        name=name,
        category=category,
        status=status,
        priority=priority,
        hypothesis="test hypothesis",
        contract=ExplorationContract(
            direction_quota=direction_quota,
            candidate_quota=candidate_quota,
        ),
        evidence_summary={
            "factors_generated": factors_generated,
            "factors_admitted": factors_admitted,
            "rounds_without_admit": rounds_without_admit,
        },
        deepening_threads=deepening_threads or [],
        next_actions=next_actions or [],
    )


class TestLogicScheduler:
    def test_empty_cards(self):
        sched = LogicScheduler()
        result = sched.generate_schedule([])
        assert result.active_pool == []
        assert result.warm_pool == []
        assert result.parked_pool == []
        assert result.blocked_pool == []

    def test_single_high_priority_active(self):
        card = _make_card(priority="high", status="active")
        sched = LogicScheduler()
        result = sched.generate_schedule([card])
        assert len(result.active_pool) == 1
        assert result.active_pool[0].logic_id == "L001"
        assert result.active_pool[0].pool == "active"

    def test_dead_card_goes_to_blocked(self):
        card = _make_card(logic_id="L010", status="dead", priority="low")
        sched = LogicScheduler()
        result = sched.generate_schedule([card])
        assert len(result.blocked_pool) == 1
        assert result.blocked_pool[0].logic_id == "L010"

    def test_parked_card_stays_parked(self):
        card = _make_card(logic_id="L011", status="parked", priority="low")
        sched = LogicScheduler()
        result = sched.generate_schedule([card])
        assert len(result.parked_pool) == 1
        assert result.parked_pool[0].logic_id == "L011"

    def test_max_active_respected(self):
        cards = [
            _make_card(logic_id=f"L{i:03d}", priority="high")
            for i in range(1, 6)
        ]
        sched = LogicScheduler(max_active=2)
        result = sched.generate_schedule(cards)
        assert len(result.active_pool) <= 2

    def test_saturated_card_scores_low(self):
        healthy = _make_card(
            logic_id="L001",
            priority="high",
            status="active",
            factors_generated=10,
            factors_admitted=3,
        )
        saturated = _make_card(
            logic_id="L002",
            priority="high",
            status="saturated",
            factors_generated=20,
            factors_admitted=1,
            rounds_without_admit=5,
        )
        sched = LogicScheduler()
        result = sched.generate_schedule([healthy, saturated])
        # Healthy should rank higher
        active_ids = [b.logic_id for b in result.active_pool]
        if "L001" in active_ids and "L002" in active_ids:
            # both active is fine, but L001 should have higher score
            scores = {b.logic_id: b.score for b in result.active_pool}
            assert scores["L001"] > scores["L002"]
        elif "L001" in active_ids:
            pass  # expected
        else:
            pytest.fail("Healthy card L001 should be in active pool")

    def test_productive_card_scores_higher(self):
        productive = _make_card(
            logic_id="L001",
            priority="medium",
            status="productive",
            factors_generated=10,
            factors_admitted=5,
        )
        idle = _make_card(
            logic_id="L002",
            priority="medium",
            status="active",
            factors_generated=10,
            factors_admitted=0,
            rounds_without_admit=4,
        )
        sched = LogicScheduler()
        result = sched.generate_schedule([productive, idle])
        all_budgets = result.all_budgets
        score_map = {b.logic_id: b.score for b in all_budgets}
        assert score_map["L001"] > score_map["L002"]

    def test_schedule_result_to_dict(self):
        card = _make_card()
        sched = LogicScheduler()
        result = sched.generate_schedule([card])
        d = result.to_dict()
        assert "active_pool" in d
        assert "global_constraints" in d
        assert d["global_constraints"]["max_active"] == 3

    def test_budget_quotas_from_contract(self):
        card = _make_card(direction_quota=3, candidate_quota=6)
        sched = LogicScheduler()
        result = sched.generate_schedule([card])
        assert len(result.active_pool) == 1
        budget = result.active_pool[0]
        assert budget.direction_quota == 3
        assert budget.candidate_quota == 6

    def test_score_card_with_active_threads(self):
        """Card with active high-priority threads gets a bottleneck boost."""
        with_threads = _make_card(
            logic_id="L001",
            deepening_threads=[
                {"id": "T001", "status": "active", "priority": "high", "question": "test"},
            ],
        )
        without_threads = _make_card(
            logic_id="L002",
            deepening_threads=[],
        )
        sched = LogicScheduler()
        result = sched.generate_schedule([with_threads, without_threads])
        scores = {b.logic_id: b.score for b in result.all_budgets}
        assert scores["L001"] > scores["L002"]

    def test_score_card_no_threads_no_actions(self):
        """Card with no threads and no next_actions gets saturation penalty."""
        bare = _make_card(
            logic_id="L001",
            deepening_threads=[],
            next_actions=[],
        )
        with_actions = _make_card(
            logic_id="L002",
            deepening_threads=[],
            next_actions=["try wider windows"],
        )
        sched = LogicScheduler()
        result = sched.generate_schedule([bare, with_actions])
        scores = {b.logic_id: b.score for b in result.all_budgets}
        # bare gets saturation penalty, with_actions does not
        assert scores["L002"] > scores["L001"]

    def test_global_saturation_signal_emitted(self):
        """When all active logics are stuck, global_saturation_signal fires."""
        cards = [
            _make_card(
                logic_id=f"L{i:03d}",
                category=f"cat_{i}",
                deepening_threads=[],
                next_actions=[],
                rounds_without_admit=3,
            )
            for i in range(1, 4)
        ]
        sched = LogicScheduler(max_active=3)
        result = sched.generate_schedule(cards)
        assert result.global_saturation_signal is not None
        assert set(result.global_saturation_signal["affected_logics"]) == {
            "L001", "L002", "L003"
        }

    def test_budget_includes_thread_count(self):
        """LogicBudget.active_thread_count reflects card threads."""
        card = _make_card(
            logic_id="L001",
            deepening_threads=[
                {"id": "T001", "status": "active", "priority": "high", "question": "q1"},
                {"id": "T002", "status": "active", "priority": "medium", "question": "q2"},
                {"id": "T003", "status": "active", "priority": "low", "question": "q3"},
                {"id": "T004", "status": "resolved", "priority": "high", "question": "q4"},
            ],
            next_actions=["something to do"],
        )
        sched = LogicScheduler()
        result = sched.generate_schedule([card])
        budget = result.active_pool[0]
        assert budget.active_thread_count == 3  # only 3 active, not the resolved one
        assert budget.has_clear_next_action is True
