"""Logic judge -- lifecycle recommendation for market logics.

This is recommendation only. The logic layer has final authority
over lifecycle transitions. Judge recommends based on cumulative
route and candidate evidence from the current batch.

Recommendations:
    active     -- should keep receiving budget
    warm       -- not primary focus, but worth observing
    productive -- stable positive output
    saturated  -- high coverage, diminishing returns
    parked     -- not worth budget now, but not disproven
    dead       -- hypothesis lacks stable research value
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple

from research.judge.route_judge import RouteVerdict


VALID_RECOMMENDATIONS = frozenset(
    {"active", "warm", "productive", "saturated", "parked", "dead"}
)


@dataclass
class LogicEvidence:
    """Cumulative evidence for a logic lifecycle recommendation."""

    logic_id: str = ""
    route_verdicts: List[RouteVerdict] = field(default_factory=list)

    # Cumulative stats
    total_admits: int = 0
    total_rejects: int = 0
    total_batches: int = 0
    productive_families: int = 0
    failed_families: int = 0

    # Saturation signals
    recent_admits_declining: bool = False
    high_library_coverage: bool = False

    # Whether any route was promoted to family this batch
    family_promoted_this_batch: bool = False


@dataclass
class LogicRecommendation:
    """Lifecycle recommendation for a logic."""

    logic_id: str
    recommendation: str  # active / warm / productive / saturated / parked / dead
    reason_codes: List[Tuple[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "logic_id": self.logic_id,
            "recommendation": self.recommendation,
            "reason_codes": [
                {"code": c, "severity": s} for c, s in self.reason_codes
            ],
        }


class LogicJudge:
    """Recommend a lifecycle status for a market logic.

    This is a recommendation only -- the logic layer makes the final call.
    """

    def recommend(self, evidence: LogicEvidence) -> LogicRecommendation:
        """Produce a lifecycle recommendation based on cumulative evidence.

        Decision hierarchy:
        1. Dead -- all routes killed, or zero admits across many batches
        2. Saturated -- high coverage + declining admits
        3. Productive -- repeated positive output with family promotion
        4. Parked -- too few batches to judge but weak signal
        5. Warm -- some promise but not primary
        6. Active -- default for ongoing research
        """
        codes: List[Tuple[str, str]] = []

        # Aggregate route verdicts
        kills = sum(
            1 for rv in evidence.route_verdicts if rv.verdict == "kill"
        )
        continues = sum(
            1 for rv in evidence.route_verdicts if rv.verdict == "continue"
        )
        promotions = sum(
            1 for rv in evidence.route_verdicts if rv.verdict == "promote_family"
        )
        total_routes = len(evidence.route_verdicts)

        # Dead: all routes killed + no admits in history
        if total_routes > 0 and kills == total_routes:
            codes.append(("all_routes_killed", "fatal"))
            return LogicRecommendation(
                logic_id=evidence.logic_id,
                recommendation="dead",
                reason_codes=codes,
            )

        if (
            evidence.total_batches >= 3
            and evidence.total_admits == 0
            and evidence.failed_families > 0
        ):
            codes.append(("no_admits_after_repeated_batches", "high"))
            return LogicRecommendation(
                logic_id=evidence.logic_id,
                recommendation="dead",
                reason_codes=codes,
            )

        # Saturated: high coverage + declining admits
        if evidence.high_library_coverage and evidence.recent_admits_declining:
            codes.append(("high_coverage_declining_admits", "medium"))
            return LogicRecommendation(
                logic_id=evidence.logic_id,
                recommendation="saturated",
                reason_codes=codes,
            )

        # Productive: family promotion evidence
        if (
            evidence.family_promoted_this_batch
            or (evidence.productive_families >= 1 and evidence.total_admits >= 2)
        ):
            codes.append(("family_productive", "info"))
            return LogicRecommendation(
                logic_id=evidence.logic_id,
                recommendation="productive",
                reason_codes=codes,
            )

        # Parked: few batches, no continues, weak signal
        if evidence.total_batches <= 1 and continues == 0 and total_routes > 0:
            codes.append(("insufficient_evidence_weak_signal", "medium"))
            return LogicRecommendation(
                logic_id=evidence.logic_id,
                recommendation="parked",
                reason_codes=codes,
            )

        # Warm: some continues but no strong positive
        if continues > 0 and evidence.total_admits == 0:
            codes.append(("some_promise_no_admits", "medium"))
            return LogicRecommendation(
                logic_id=evidence.logic_id,
                recommendation="warm",
                reason_codes=codes,
            )

        # Active: default for ongoing research with admits
        codes.append(("ongoing_research", "info"))
        return LogicRecommendation(
            logic_id=evidence.logic_id,
            recommendation="active",
            reason_codes=codes,
        )
