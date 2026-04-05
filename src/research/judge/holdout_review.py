"""Holdout review -- asynchronous post-judge review for reserved candidates.

Holdout is not part of the daily research loop. It runs after judge,
before the next batch, on candidates that require extra confirmation.

Review outcomes:
    supportive    -- holdout evidence supports promotion
    neutral       -- holdout inconclusive, maintain reserve
    contradictory -- holdout contradicts, block promotion

Triggers:
    - high multiple_testing_risk_bucket + strong validation
    - reserve_for_replace_review
    - judge flags holdout_review_required

Deadline: 1 batch or 7 days, whichever comes first.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


VALID_OUTCOMES = frozenset({"supportive", "neutral", "contradictory"})


@dataclass
class HoldoutEvidence:
    """Evidence from holdout-period evaluation."""

    candidate_id: str = ""

    # Holdout IC sign matches validation sign
    sign_consistent: bool = True

    # No structural break detected in holdout period
    no_structural_break: bool = True

    # Whether holdout IC is materially positive (same direction)
    holdout_ic_positive: bool = True

    # New fatal issues discovered in holdout
    fatal_new_issue: bool = False
    fatal_issue_detail: str = ""


@dataclass
class HoldoutResult:
    """Result of a holdout review."""

    candidate_id: str
    outcome: str  # supportive / neutral / contradictory
    reason_codes: List[Tuple[str, str]] = field(default_factory=list)
    can_promote: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "outcome": self.outcome,
            "reason_codes": [
                {"code": c, "severity": s} for c, s in self.reason_codes
            ],
            "can_promote": self.can_promote,
        }


class HoldoutReview:
    """Evaluate holdout evidence for reserved candidates.

    Conservative by design: holdout is a veto, not a primary
    significance source.
    """

    def review(self, evidence: HoldoutEvidence) -> HoldoutResult:
        """Produce a holdout review outcome.

        Rules:
        - contradictory: fatal new issue, or sign inconsistency
        - supportive: sign consistent + no break + positive IC
        - neutral: fallback
        """
        codes: List[Tuple[str, str]] = []

        # Contradictory: fatal issue
        if evidence.fatal_new_issue:
            codes.append(("holdout_fatal_issue", "fatal"))
            if evidence.fatal_issue_detail:
                codes.append((f"detail:{evidence.fatal_issue_detail}", "high"))
            return HoldoutResult(
                candidate_id=evidence.candidate_id,
                outcome="contradictory",
                reason_codes=codes,
                can_promote=False,
            )

        # Contradictory: sign flip in holdout
        if not evidence.sign_consistent:
            codes.append(("holdout_sign_inconsistent", "high"))
            return HoldoutResult(
                candidate_id=evidence.candidate_id,
                outcome="contradictory",
                reason_codes=codes,
                can_promote=False,
            )

        # Supportive: all positive signals
        if (
            evidence.sign_consistent
            and evidence.no_structural_break
            and evidence.holdout_ic_positive
        ):
            codes.append(("holdout_supportive", "info"))
            return HoldoutResult(
                candidate_id=evidence.candidate_id,
                outcome="supportive",
                reason_codes=codes,
                can_promote=True,
            )

        # Neutral: inconclusive
        codes.append(("holdout_neutral", "medium"))
        return HoldoutResult(
            candidate_id=evidence.candidate_id,
            outcome="neutral",
            reason_codes=codes,
            can_promote=False,
        )
