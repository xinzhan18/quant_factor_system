"""Tests for Scheduler."""

from __future__ import annotations

import pytest
from mining.scheduler import Scheduler


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_logic(
    logic_id: str = "L1",
    category: str = "momentum",
    factors_generated: int = 5,
    factors_admitted: int = 1,
    rounds_without_admit: int = 0,
    best_ic: float | None = 0.04,
) -> dict:
    return {
        "logic_id": logic_id,
        "category": category,
        "factors_generated": factors_generated,
        "factors_admitted": factors_admitted,
        "rounds_without_admit": rounds_without_admit,
        "best_ic": best_ic,
    }


# ---------------------------------------------------------------------------
# score_logics tests
# ---------------------------------------------------------------------------

class TestScoreLogics:
    def test_new_logic_default_score(self):
        """A logic with factors_generated == 0 always scores 3.0."""
        scheduler = Scheduler()
        logic = make_logic(logic_id="L1", factors_generated=0)
        scored = scheduler.score_logics([logic], coverage={}, library_avg_ic=0.03)
        assert len(scored) == 1
        logic_id, score = scored[0]
        assert logic_id == "L1"
        assert score == 3.0

    def test_underrepresented_category_bonus(self):
        """Category with fewer than 2 active logics earns +3 potential."""
        scheduler = Scheduler()
        # coverage shows "volatility" has only 1 factor → underrepresented
        logic = make_logic(
            logic_id="L1",
            category="volatility",
            factors_generated=3,
            factors_admitted=0,
            rounds_without_admit=0,
            best_ic=None,
        )
        coverage = {"volatility": 1}
        scored = scheduler.score_logics([logic], coverage=coverage, library_avg_ic=0.03)
        _, score = scored[0]
        # potential = +3 (underrepresented), no recent success (admitted==0), no high ceiling
        # fatigue = 0 rounds_without_admit (capped at 5) + 0 zero-conversion (generated<=10)
        assert score > 0

    def test_underrepresented_gives_plus_three(self):
        """Verify the exact +3 bonus when all other terms are zero."""
        scheduler = Scheduler()
        logic = make_logic(
            logic_id="L1",
            category="rare",
            factors_generated=5,
            factors_admitted=0,
            rounds_without_admit=0,
            best_ic=None,
        )
        coverage = {"rare": 0}
        scored = scheduler.score_logics([logic], coverage=coverage, library_avg_ic=0.0)
        _, score = scored[0]
        # potential: +3 (underrepresented)
        # fatigue: 0 rounds, no zero-conversion
        assert score == 3.0

    def test_recent_success_bonus(self):
        """rounds_without_admit==0 AND factors_admitted>0 earns +2."""
        scheduler = Scheduler()
        logic = make_logic(
            logic_id="L1",
            category="other",
            factors_generated=5,
            factors_admitted=2,
            rounds_without_admit=0,
            best_ic=None,
        )
        # category with 5 logics → not underrepresented
        coverage = {"other": 5}
        scored = scheduler.score_logics([logic], coverage=coverage, library_avg_ic=0.0)
        _, score = scored[0]
        # potential: +2 (recent success), no high ceiling (best_ic=None)
        # fatigue: 0
        assert score == 2.0

    def test_high_ceiling_bonus(self):
        """|best_ic| > library_avg_ic earns +1."""
        scheduler = Scheduler()
        logic = make_logic(
            logic_id="L1",
            category="other",
            factors_generated=5,
            factors_admitted=0,
            rounds_without_admit=0,
            best_ic=0.05,
        )
        coverage = {"other": 5}
        scored = scheduler.score_logics([logic], coverage=coverage, library_avg_ic=0.03)
        _, score = scored[0]
        # potential: +1 (high ceiling)
        # fatigue: 0
        assert score == 1.0

    def test_fatigue_caps_at_minus_five(self):
        """rounds_without_admit=10 should NOT produce fatigue below -5."""
        scheduler = Scheduler()
        logic = make_logic(
            logic_id="L1",
            category="other",
            factors_generated=5,
            factors_admitted=0,
            rounds_without_admit=10,
            best_ic=None,
        )
        coverage = {"other": 5}
        scored = scheduler.score_logics([logic], coverage=coverage, library_avg_ic=0.0)
        _, score = scored[0]
        # potential: 0
        # fatigue: min(10, 5) = 5 → score = -5
        assert score == -5.0

    def test_fatigue_with_three_rounds(self):
        """rounds_without_admit=3 → fatigue=3."""
        scheduler = Scheduler()
        logic = make_logic(
            logic_id="L1",
            category="other",
            factors_generated=5,
            factors_admitted=0,
            rounds_without_admit=3,
            best_ic=None,
        )
        coverage = {"other": 5}
        scored = scheduler.score_logics([logic], coverage=coverage, library_avg_ic=0.0)
        _, score = scored[0]
        assert score == -3.0

    def test_zero_conversion_penalty(self):
        """factors_generated > 10 AND admitted == 0 adds -2 to fatigue."""
        scheduler = Scheduler()
        logic = make_logic(
            logic_id="L1",
            category="other",
            factors_generated=15,
            factors_admitted=0,
            rounds_without_admit=1,
            best_ic=None,
        )
        coverage = {"other": 5}
        scored = scheduler.score_logics([logic], coverage=coverage, library_avg_ic=0.0)
        _, score = scored[0]
        # potential: 0
        # fatigue: 1 (rounds) + 2 (zero-conversion) = 3 → score = -3
        assert score == -3.0

    def test_zero_conversion_does_not_exceed_cap(self):
        """Total fatigue including zero-conversion penalty is still capped at 5."""
        scheduler = Scheduler()
        logic = make_logic(
            logic_id="L1",
            category="other",
            factors_generated=20,
            factors_admitted=0,
            rounds_without_admit=4,  # 4 + 2 = 6, but capped at 5
            best_ic=None,
        )
        coverage = {"other": 5}
        scored = scheduler.score_logics([logic], coverage=coverage, library_avg_ic=0.0)
        _, score = scored[0]
        # fatigue = min(4 + 2, 5) = 5 → score = -5
        assert score == -5.0

    def test_sorted_descending(self):
        """score_logics returns results sorted by score descending."""
        scheduler = Scheduler()
        logics = [
            make_logic(logic_id="L_low", category="other", factors_generated=5,
                       factors_admitted=0, rounds_without_admit=4, best_ic=None),
            make_logic(logic_id="L_high", category="other", factors_generated=5,
                       factors_admitted=2, rounds_without_admit=0, best_ic=None),
        ]
        coverage = {"other": 5}
        scored = scheduler.score_logics(logics, coverage=coverage, library_avg_ic=0.0)
        ids = [lid for lid, _ in scored]
        assert ids[0] == "L_high"
        assert ids[1] == "L_low"

    def test_empty_logics(self):
        """Empty input returns empty list."""
        scheduler = Scheduler()
        result = scheduler.score_logics([], coverage={}, library_avg_ic=0.03)
        assert result == []

    def test_category_not_in_coverage(self):
        """Category missing from coverage dict is treated as 0 — underrepresented."""
        scheduler = Scheduler()
        logic = make_logic(
            logic_id="L1",
            category="exotic",
            factors_generated=5,
            factors_admitted=0,
            rounds_without_admit=0,
            best_ic=None,
        )
        # "exotic" not in coverage → count = 0, earns +3 bonus
        scored = scheduler.score_logics([logic], coverage={}, library_avg_ic=0.0)
        _, score = scored[0]
        assert score == 3.0


# ---------------------------------------------------------------------------
# recommend tests
# ---------------------------------------------------------------------------

class TestRecommend:
    def test_recommend_top_n(self):
        """Returns exactly top_n logics."""
        scheduler = Scheduler()
        logics = [make_logic(logic_id=f"L{i}", factors_generated=i + 1) for i in range(5)]
        coverage = {}
        result = scheduler.recommend(logics, coverage=coverage, library_avg_ic=0.03, top_n=2)
        assert len(result) == 2

    def test_recommend_returns_dicts(self):
        """Returns the original dict objects, not just IDs."""
        scheduler = Scheduler()
        logics = [make_logic(logic_id="L1"), make_logic(logic_id="L2")]
        result = scheduler.recommend(logics, coverage={}, library_avg_ic=0.03, top_n=1)
        assert isinstance(result[0], dict)
        assert "logic_id" in result[0]

    def test_recommend_top_n_fewer_than_logics(self):
        """top_n=1 returns one logic."""
        scheduler = Scheduler()
        logics = [
            make_logic(logic_id="L1", factors_generated=0),
            make_logic(logic_id="L2", rounds_without_admit=5),
        ]
        result = scheduler.recommend(logics, coverage={}, library_avg_ic=0.03, top_n=1)
        assert len(result) == 1

    def test_recommend_fewer_available_than_top_n(self):
        """When fewer logics exist than top_n, returns all of them."""
        scheduler = Scheduler()
        logics = [make_logic(logic_id="L1")]
        result = scheduler.recommend(logics, coverage={}, library_avg_ic=0.03, top_n=5)
        assert len(result) == 1

    def test_recommend_best_first(self):
        """Best-scoring logic comes first in recommendation."""
        scheduler = Scheduler()
        logics = [
            make_logic(logic_id="L_bad", category="other", factors_generated=5,
                       factors_admitted=0, rounds_without_admit=5, best_ic=None),
            make_logic(logic_id="L_good", factors_generated=0),  # new → 3.0
        ]
        result = scheduler.recommend(logics, coverage={"other": 5}, library_avg_ic=0.03, top_n=2)
        assert result[0]["logic_id"] == "L_good"


# ---------------------------------------------------------------------------
# should_trigger_outer_loop tests
# ---------------------------------------------------------------------------

class TestShouldTriggerOuterLoop:
    def test_should_trigger_outer_loop_all_negative(self):
        """All logics with non-positive scores → should trigger."""
        scheduler = Scheduler()
        # Both logics are fatigued
        logics = [
            make_logic(logic_id="L1", category="other", factors_generated=5,
                       factors_admitted=0, rounds_without_admit=5, best_ic=None),
            make_logic(logic_id="L2", category="other", factors_generated=5,
                       factors_admitted=0, rounds_without_admit=5, best_ic=None),
        ]
        coverage = {"other": 5}
        assert scheduler.should_trigger_outer_loop(logics, coverage, library_avg_ic=0.0) is True

    def test_should_not_trigger_with_positive_score(self):
        """At least one positive score → should NOT trigger outer loop."""
        scheduler = Scheduler()
        logics = [
            make_logic(logic_id="L1", category="other", factors_generated=5,
                       factors_admitted=0, rounds_without_admit=5, best_ic=None),
            make_logic(logic_id="L2", factors_generated=0),  # new → score = 3.0
        ]
        coverage = {"other": 5}
        assert scheduler.should_trigger_outer_loop(logics, coverage, library_avg_ic=0.0) is False

    def test_should_trigger_with_empty_logics(self):
        """No logics at all → should trigger outer loop."""
        scheduler = Scheduler()
        assert scheduler.should_trigger_outer_loop([], {}, library_avg_ic=0.0) is True

    def test_should_trigger_when_all_scores_zero(self):
        """Score of exactly zero is considered non-positive → triggers."""
        scheduler = Scheduler()
        # potential=0, fatigue=0 → score=0
        logic = make_logic(
            logic_id="L1",
            category="other",
            factors_generated=5,
            factors_admitted=0,
            rounds_without_admit=0,
            best_ic=None,
        )
        coverage = {"other": 5}
        assert scheduler.should_trigger_outer_loop([logic], coverage, library_avg_ic=0.0) is True

    def test_should_not_trigger_mixed_scores(self):
        """Mixed positive and negative scores → should NOT trigger."""
        scheduler = Scheduler()
        logics = [
            make_logic(logic_id="L1", category="other", factors_generated=5,
                       factors_admitted=0, rounds_without_admit=3, best_ic=None),  # -3
            make_logic(logic_id="L2", category="rare", factors_generated=5,
                       factors_admitted=2, rounds_without_admit=0, best_ic=None),  # +5 (+3 underrep + +2 recent)
        ]
        coverage = {"other": 5, "rare": 0}
        assert scheduler.should_trigger_outer_loop(logics, coverage, library_avg_ic=0.0) is False
