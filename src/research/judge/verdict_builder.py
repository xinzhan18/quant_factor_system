"""Verdict builder -- assemble a BatchJudgeReport from individual verdicts.

The BatchJudgeReport is the primary output artifact of research_judge.
It aggregates:
    - candidate verdicts
    - route verdicts
    - logic recommendations
    - holdout review requests
    - policy upgrade suggestions
    - summary statistics
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from research.judge.candidate_judge import CandidateVerdict
from research.judge.route_judge import RouteVerdict
from research.judge.logic_judge import LogicRecommendation


@dataclass
class PolicyUpgradeSuggestion:
    """Suggestion for a policy/forbidden upgrade, pending repeated evidence."""

    pattern_id: str = ""
    observed_batches: int = 0
    observed_routes: int = 0
    repeated_reason_codes: List[str] = field(default_factory=list)
    recommended_action: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "pattern_id": self.pattern_id,
            "observed_batches": self.observed_batches,
            "observed_routes": self.observed_routes,
            "repeated_reason_codes": list(self.repeated_reason_codes),
            "recommended_action": self.recommended_action,
        }


@dataclass
class BatchJudgeReport:
    """Full judge report for a batch.

    This is the primary output file:
        storage/batches/batch_XXX/judge_report.yaml
    """

    batch_id: str = ""
    judged_at: str = ""

    candidate_verdicts: List[CandidateVerdict] = field(default_factory=list)
    route_verdicts: List[RouteVerdict] = field(default_factory=list)
    logic_recommendations: List[LogicRecommendation] = field(default_factory=list)

    holdout_reviews_requested: List[str] = field(default_factory=list)
    policy_upgrade_suggestions: List[PolicyUpgradeSuggestion] = field(
        default_factory=list
    )

    def __post_init__(self) -> None:
        if not self.judged_at:
            self.judged_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    @property
    def summary(self) -> Dict[str, Any]:
        """Compute summary statistics."""
        cv = self.candidate_verdicts
        rv = self.route_verdicts

        return {
            "total_candidates": len(cv),
            "admits": sum(1 for v in cv if v.verdict == "admit"),
            "reserves": sum(1 for v in cv if v.verdict == "reserve"),
            "rejects": sum(1 for v in cv if v.verdict == "reject"),
            "replaces": sum(1 for v in cv if v.verdict == "replace"),
            "total_routes": len(rv),
            "route_continues": sum(1 for v in rv if v.verdict == "continue"),
            "route_pauses": sum(1 for v in rv if v.verdict == "pause"),
            "route_kills": sum(1 for v in rv if v.verdict == "kill"),
            "route_promotes": sum(
                1 for v in rv if v.verdict == "promote_family"
            ),
            "holdout_reviews_pending": len(self.holdout_reviews_requested),
            "policy_upgrades_suggested": len(self.policy_upgrade_suggestions),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "batch_id": self.batch_id,
            "judged_at": self.judged_at,
            "summary": self.summary,
            "candidate_verdicts": [v.to_dict() for v in self.candidate_verdicts],
            "route_verdicts": [v.to_dict() for v in self.route_verdicts],
            "logic_recommendations": [
                r.to_dict() for r in self.logic_recommendations
            ],
            "holdout_reviews_requested": list(self.holdout_reviews_requested),
            "policy_upgrade_suggestions": [
                s.to_dict() for s in self.policy_upgrade_suggestions
            ],
        }


class VerdictBuilder:
    """Assemble a BatchJudgeReport from individual components."""

    def __init__(self, batch_id: str) -> None:
        self._batch_id = batch_id
        self._candidate_verdicts: List[CandidateVerdict] = []
        self._route_verdicts: List[RouteVerdict] = []
        self._logic_recommendations: List[LogicRecommendation] = []
        self._policy_suggestions: List[PolicyUpgradeSuggestion] = []

    def add_candidate_verdict(self, verdict: CandidateVerdict) -> None:
        self._candidate_verdicts.append(verdict)

    def add_route_verdict(self, verdict: RouteVerdict) -> None:
        self._route_verdicts.append(verdict)

    def add_logic_recommendation(self, rec: LogicRecommendation) -> None:
        self._logic_recommendations.append(rec)

    def add_policy_suggestion(self, suggestion: PolicyUpgradeSuggestion) -> None:
        self._policy_suggestions.append(suggestion)

    def build(self) -> BatchJudgeReport:
        """Assemble all verdicts into a BatchJudgeReport."""
        holdout_requested = [
            v.candidate_id
            for v in self._candidate_verdicts
            if v.holdout_review_required
        ]

        return BatchJudgeReport(
            batch_id=self._batch_id,
            candidate_verdicts=list(self._candidate_verdicts),
            route_verdicts=list(self._route_verdicts),
            logic_recommendations=list(self._logic_recommendations),
            holdout_reviews_requested=holdout_requested,
            policy_upgrade_suggestions=list(self._policy_suggestions),
        )
