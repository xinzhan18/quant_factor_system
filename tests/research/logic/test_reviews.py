"""Tests for research.logic.reviews — 4-dimension review gate."""
import pytest

from research.logic.reviews import (
    DimensionReview,
    LogicReview,
    review_proposal,
    save_review,
    load_review,
)


def _pass_dim(score: float = 0.8) -> DimensionReview:
    return DimensionReview(verdict="pass", score=score, comments=["ok"])


def _fail_dim(score: float = 0.2) -> DimensionReview:
    return DimensionReview(verdict="fail", score=score, comments=["bad"])


def _borderline_dim(score: float = 0.5) -> DimensionReview:
    return DimensionReview(
        verdict="borderline", score=score, comments=["unclear"]
    )


class TestDimensionReview:
    def test_valid_verdicts(self):
        for v in ("pass", "borderline", "fail"):
            d = DimensionReview(verdict=v, score=0.5)
            assert d.verdict == v

    def test_invalid_verdict_raises(self):
        with pytest.raises(ValueError, match="Invalid verdict"):
            DimensionReview(verdict="maybe", score=0.5)

    def test_score_out_of_range(self):
        with pytest.raises(ValueError, match="Score must be"):
            DimensionReview(verdict="pass", score=1.5)
        with pytest.raises(ValueError, match="Score must be"):
            DimensionReview(verdict="pass", score=-0.1)

    def test_roundtrip_dict(self):
        d = DimensionReview(
            verdict="borderline", score=0.6, comments=["test"]
        )
        d2 = DimensionReview.from_dict(d.to_dict())
        assert d2.verdict == d.verdict
        assert d2.score == d.score
        assert d2.comments == d.comments


class TestReviewOutcome:
    """Test the outcome computation rules."""

    def test_all_pass_creates_logic(self):
        r = review_proposal(
            "P001",
            mechanism=_pass_dim(),
            feasibility=_pass_dim(),
            novelty=_pass_dim(),
            research_value=_pass_dim(),
        )
        assert r.outcome == "create_logic"

    def test_mechanism_fail_rejects(self):
        r = review_proposal(
            "P002",
            mechanism=_fail_dim(),
            feasibility=_pass_dim(),
            novelty=_pass_dim(),
            research_value=_pass_dim(),
        )
        assert r.outcome == "reject"
        assert "mechanism" in r.outcome_reason

    def test_feasibility_fail_rejects(self):
        r = review_proposal(
            "P003",
            mechanism=_pass_dim(),
            feasibility=_fail_dim(),
            novelty=_pass_dim(),
            research_value=_pass_dim(),
        )
        assert r.outcome == "reject"
        assert "feasibility" in r.outcome_reason

    def test_novelty_fail_downgrades(self):
        r = review_proposal(
            "P004",
            mechanism=_pass_dim(),
            feasibility=_pass_dim(),
            novelty=_fail_dim(),
            research_value=_pass_dim(),
        )
        assert r.outcome == "downgrade_to_direction"

    def test_research_value_fail_parks(self):
        r = review_proposal(
            "P005",
            mechanism=_pass_dim(),
            feasibility=_pass_dim(),
            novelty=_pass_dim(),
            research_value=_fail_dim(),
        )
        assert r.outcome == "park"

    def test_many_borderlines_parks(self):
        r = review_proposal(
            "P006",
            mechanism=_borderline_dim(),
            feasibility=_borderline_dim(),
            novelty=_borderline_dim(),
            research_value=_borderline_dim(),
        )
        assert r.outcome == "park"

    def test_one_borderline_creates(self):
        """One borderline among passes should still create."""
        r = review_proposal(
            "P007",
            mechanism=_pass_dim(),
            feasibility=_pass_dim(),
            novelty=_borderline_dim(),
            research_value=_pass_dim(),
        )
        assert r.outcome == "create_logic"

    def test_two_borderlines_creates(self):
        """Two borderlines should still create (threshold is 3)."""
        r = review_proposal(
            "P008",
            mechanism=_pass_dim(),
            feasibility=_borderline_dim(),
            novelty=_borderline_dim(),
            research_value=_pass_dim(),
        )
        assert r.outcome == "create_logic"


class TestReviewPersistence:
    """Test save/load round-trip."""

    def test_save_and_load(self, tmp_path):
        r = review_proposal(
            "P001",
            mechanism=_pass_dim(0.9),
            feasibility=_pass_dim(0.85),
            novelty=_borderline_dim(0.5),
            research_value=_pass_dim(0.7),
        )
        path = save_review(tmp_path, r)
        assert path.exists()

        loaded = load_review(tmp_path, "P001")
        assert loaded is not None
        assert loaded.proposal_id == "P001"
        assert loaded.outcome == r.outcome
        assert loaded.mechanism.score == 0.9
        assert loaded.novelty.verdict == "borderline"

    def test_load_nonexistent(self, tmp_path):
        assert load_review(tmp_path, "P999") is None
