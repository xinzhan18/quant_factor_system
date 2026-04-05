"""Mechanism alignment -- 4 structural checks for candidate-thesis consistency.

Checks:
    1. thesis_match        -- candidate still answers the logic thesis
    2. route_question_match -- candidate answers this batch's research question
    3. sign_behavior_match -- signal direction / trigger consistent with hypothesis
    4. non_style_only      -- result not mainly explained by a single style/beta

Verdicts:
    aligned  -- >=3 checks pass AND non_style_only passes
    unclear  -- exactly 2 checks pass, or explanation ambiguity
    drifted  -- thesis/route mismatch OR mainly style residual
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


# ------------------------------------------------------------------
# Reason codes emitted by this module
# ------------------------------------------------------------------
REASON_MECHANISM_ALIGNED = ("mechanism_aligned", "info")
REASON_MECHANISM_UNCLEAR = ("mechanism_unclear", "medium")
REASON_MECHANISM_DRIFTED = ("mechanism_drifted", "fatal")


@dataclass
class AlignmentEvidence:
    """Input evidence for mechanism alignment checks."""

    thesis_match: bool = False
    route_question_match: bool = False
    sign_behavior_match: bool = False
    non_style_only: bool = True


@dataclass
class AlignmentResult:
    """Output of mechanism alignment assessment."""

    verdict: str  # aligned / unclear / drifted
    checks_passed: int
    detail: Dict[str, bool] = field(default_factory=dict)
    reason_code: str = ""
    severity: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "checks_passed": self.checks_passed,
            "detail": dict(self.detail),
            "reason_code": self.reason_code,
            "severity": self.severity,
        }


class MechanismAlignment:
    """Evaluate mechanism alignment from 4 structural checks."""

    def evaluate(self, evidence: AlignmentEvidence) -> AlignmentResult:
        """Run the 4 checks and produce a verdict.

        Rules (from research_judge.md section 5.1.1):
        - aligned:  >=3 pass AND non_style_only pass
        - unclear:  exactly 2 pass, or ambiguity
        - drifted:  thesis/route mismatch OR mainly style
        """
        checks = {
            "thesis_match": evidence.thesis_match,
            "route_question_match": evidence.route_question_match,
            "sign_behavior_match": evidence.sign_behavior_match,
            "non_style_only": evidence.non_style_only,
        }
        passed = sum(1 for v in checks.values() if v)

        # Drifted: thesis or route mismatch, or mainly style
        if not evidence.non_style_only:
            return AlignmentResult(
                verdict="drifted",
                checks_passed=passed,
                detail=checks,
                reason_code="mechanism_drifted",
                severity="fatal",
            )

        if not evidence.thesis_match or not evidence.route_question_match:
            return AlignmentResult(
                verdict="drifted",
                checks_passed=passed,
                detail=checks,
                reason_code="mechanism_drifted",
                severity="fatal",
            )

        # Aligned: >=3 pass and non_style_only ok
        if passed >= 3:
            return AlignmentResult(
                verdict="aligned",
                checks_passed=passed,
                detail=checks,
                reason_code="mechanism_aligned",
                severity="info",
            )

        # Unclear: exactly 2 pass
        return AlignmentResult(
            verdict="unclear",
            checks_passed=passed,
            detail=checks,
            reason_code="mechanism_unclear",
            severity="medium",
        )
