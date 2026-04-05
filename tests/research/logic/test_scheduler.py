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


class TestSaveSchedule:
    def test_save_creates_file(self, tmp_path):
        card = _make_card()
        sched = LogicScheduler()
        result = sched.generate_schedule([card])
        path = sched.save_schedule(tmp_path, result)
        assert path.exists()
        assert path.parent.name == "snapshots"
