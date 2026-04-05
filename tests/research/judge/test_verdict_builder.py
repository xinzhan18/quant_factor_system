"""Tests for VerdictBuilder and BatchJudgeReport."""
from research.judge.candidate_judge import CandidateVerdict
from research.judge.route_judge import RouteVerdict
from research.judge.logic_judge import LogicRecommendation
from research.judge.verdict_builder import (
    BatchJudgeReport,
    PolicyUpgradeSuggestion,
    VerdictBuilder,
)


class TestVerdictBuilder:
    def test_empty_build(self):
        builder = VerdictBuilder(batch_id="batch_042")
        report = builder.build()
        assert report.batch_id == "batch_042"
        assert report.summary["total_candidates"] == 0
        assert report.summary["total_routes"] == 0

    def test_add_candidate_verdicts(self):
        builder = VerdictBuilder(batch_id="batch_042")
        builder.add_candidate_verdict(
            CandidateVerdict(candidate_id="C001", verdict="admit")
        )
        builder.add_candidate_verdict(
            CandidateVerdict(candidate_id="C002", verdict="reject")
        )
        builder.add_candidate_verdict(
            CandidateVerdict(candidate_id="C003", verdict="reserve")
        )
        report = builder.build()
        assert report.summary["admits"] == 1
        assert report.summary["rejects"] == 1
        assert report.summary["reserves"] == 1
        assert report.summary["total_candidates"] == 3

    def test_add_route_verdicts(self):
        builder = VerdictBuilder(batch_id="batch_042")
        builder.add_route_verdict(
            RouteVerdict(route_id="R001", experiment_lineage_tag="ELT_1", verdict="continue")
        )
        builder.add_route_verdict(
            RouteVerdict(route_id="R002", experiment_lineage_tag="ELT_2", verdict="kill")
        )
        report = builder.build()
        assert report.summary["route_continues"] == 1
        assert report.summary["route_kills"] == 1

    def test_add_logic_recommendation(self):
        builder = VerdictBuilder(batch_id="batch_042")
        builder.add_logic_recommendation(
            LogicRecommendation(logic_id="L021", recommendation="active")
        )
        report = builder.build()
        assert len(report.logic_recommendations) == 1
        assert report.logic_recommendations[0].recommendation == "active"

    def test_holdout_reviews_collected(self):
        builder = VerdictBuilder(batch_id="batch_042")
        builder.add_candidate_verdict(
            CandidateVerdict(
                candidate_id="C001",
                verdict="reserve",
                holdout_review_required=True,
            )
        )
        builder.add_candidate_verdict(
            CandidateVerdict(candidate_id="C002", verdict="admit")
        )
        report = builder.build()
        assert report.holdout_reviews_requested == ["C001"]

    def test_policy_suggestions(self):
        builder = VerdictBuilder(batch_id="batch_042")
        builder.add_policy_suggestion(
            PolicyUpgradeSuggestion(
                pattern_id="pure_price_breakout",
                observed_batches=5,
                observed_routes=11,
                repeated_reason_codes=["high_overlap_low_increment"],
                recommended_action="add_to_forbidden",
            )
        )
        report = builder.build()
        assert len(report.policy_upgrade_suggestions) == 1
        assert report.policy_upgrade_suggestions[0].pattern_id == "pure_price_breakout"


class TestBatchJudgeReport:
    def test_to_dict(self):
        report = BatchJudgeReport(
            batch_id="batch_042",
            candidate_verdicts=[
                CandidateVerdict(candidate_id="C001", verdict="admit"),
            ],
            route_verdicts=[
                RouteVerdict(route_id="R001", experiment_lineage_tag="ELT_1", verdict="continue"),
            ],
            logic_recommendations=[
                LogicRecommendation(logic_id="L021", recommendation="active"),
            ],
        )
        d = report.to_dict()
        assert d["batch_id"] == "batch_042"
        assert d["summary"]["admits"] == 1
        assert len(d["candidate_verdicts"]) == 1
        assert len(d["route_verdicts"]) == 1
        assert len(d["logic_recommendations"]) == 1

    def test_summary_counts(self):
        report = BatchJudgeReport(
            batch_id="batch_043",
            candidate_verdicts=[
                CandidateVerdict(candidate_id="C001", verdict="admit"),
                CandidateVerdict(candidate_id="C002", verdict="admit"),
                CandidateVerdict(candidate_id="C003", verdict="reject"),
                CandidateVerdict(candidate_id="C004", verdict="reserve"),
                CandidateVerdict(candidate_id="C005", verdict="replace"),
            ],
            route_verdicts=[
                RouteVerdict(route_id="R001", experiment_lineage_tag="ELT_1", verdict="continue"),
                RouteVerdict(route_id="R002", experiment_lineage_tag="ELT_2", verdict="pause"),
                RouteVerdict(route_id="R003", experiment_lineage_tag="ELT_3", verdict="promote_family"),
            ],
        )
        s = report.summary
        assert s["admits"] == 2
        assert s["rejects"] == 1
        assert s["reserves"] == 1
        assert s["replaces"] == 1
        assert s["route_continues"] == 1
        assert s["route_pauses"] == 1
        assert s["route_promotes"] == 1

    def test_policy_suggestion_to_dict(self):
        ps = PolicyUpgradeSuggestion(
            pattern_id="test",
            observed_batches=3,
            observed_routes=5,
            repeated_reason_codes=["code_a"],
            recommended_action="review",
        )
        d = ps.to_dict()
        assert d["pattern_id"] == "test"
        assert d["observed_batches"] == 3
