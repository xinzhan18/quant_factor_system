"""Route judge -- batch-local experiment group verdict.

Verdicts:
    continue       -- >=1 admit or high-quality reserve, mechanism still live
    pause          -- evidence not strong enough, but not disproven
    kill           -- systematic failure, high redundancy, or repeated bad pattern
    promote_family -- cross-batch success in same family/lineage

The route is a batch-local label; cross-batch continuity is tracked via
experiment_lineage_tag, not route_id.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from research.judge.candidate_judge import CandidateVerdict


@dataclass
class RouteEvidence:
    """Evidence bundle for a batch-local route."""

    route_id: str = ""
    experiment_lineage_tag: str = ""
    candidate_verdicts: List[CandidateVerdict] = field(default_factory=list)

    # Whether the mechanism slice still has headroom for exploration
    mechanism_still_live: bool = True

    # Whether the route hits a known systematic failure
    systematic_failure: bool = False

    # High redundancy with existing library
    high_redundancy: bool = False

    # Feasibility too poor long-term
    feasibility_long_term_poor: bool = False

    # Repeated bad pattern hit
    repeated_bad_pattern: bool = False

    # Cross-batch family success evidence (for promote_family)
    cross_batch_family_admits: int = 0
    cross_batch_family_batches: int = 0
    family_attempt_count: int = 0
    high_subspace_redundancy: bool = False


@dataclass
class RouteVerdict:
    """Verdict for a batch-local route."""

    route_id: str
    experiment_lineage_tag: str
    verdict: str  # continue / pause / kill / promote_family
    reason_codes: List[Tuple[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "route_id": self.route_id,
            "experiment_lineage_tag": self.experiment_lineage_tag,
            "verdict": self.verdict,
            "reason_codes": [
                {"code": c, "severity": s} for c, s in self.reason_codes
            ],
        }


class RouteJudge:
    """Judge a batch-local route based on its candidate verdicts and context."""

    def judge(self, evidence: RouteEvidence) -> RouteVerdict:
        """Produce a route verdict.

        Decision hierarchy:
        1. Kill conditions (systematic failure, bad pattern, ...)
        2. Promote family (cross-batch repeated success)
        3. Continue (at least 1 admit or reserve)
        4. Pause (fallback)
        """
        codes: List[Tuple[str, str]] = []

        # --- Kill conditions ---
        if evidence.systematic_failure:
            codes.append(("systematic_failure", "fatal"))
            return RouteVerdict(
                route_id=evidence.route_id,
                experiment_lineage_tag=evidence.experiment_lineage_tag,
                verdict="kill",
                reason_codes=codes,
            )

        if evidence.repeated_bad_pattern:
            codes.append(("repeated_bad_pattern", "fatal"))
            return RouteVerdict(
                route_id=evidence.route_id,
                experiment_lineage_tag=evidence.experiment_lineage_tag,
                verdict="kill",
                reason_codes=codes,
            )

        if evidence.high_redundancy and evidence.feasibility_long_term_poor:
            codes.append(("high_redundancy", "high"))
            codes.append(("feasibility_long_term_poor", "high"))
            return RouteVerdict(
                route_id=evidence.route_id,
                experiment_lineage_tag=evidence.experiment_lineage_tag,
                verdict="kill",
                reason_codes=codes,
            )

        # --- Promote family ---
        if (
            evidence.cross_batch_family_admits >= 2
            and evidence.cross_batch_family_batches >= 2
            and not evidence.high_subspace_redundancy
        ):
            codes.append(("cross_batch_family_success", "info"))
            return RouteVerdict(
                route_id=evidence.route_id,
                experiment_lineage_tag=evidence.experiment_lineage_tag,
                verdict="promote_family",
                reason_codes=codes,
            )

        # --- Continue ---
        admits = sum(
            1
            for v in evidence.candidate_verdicts
            if v.verdict in ("admit", "replace")
        )
        reserves = sum(
            1 for v in evidence.candidate_verdicts if v.verdict == "reserve"
        )

        if admits >= 1:
            codes.append(("candidate_admitted", "info"))
            if evidence.mechanism_still_live:
                codes.append(("mechanism_still_live", "info"))
            return RouteVerdict(
                route_id=evidence.route_id,
                experiment_lineage_tag=evidence.experiment_lineage_tag,
                verdict="continue",
                reason_codes=codes,
            )

        if reserves >= 1 and evidence.mechanism_still_live:
            codes.append(("candidate_reserved", "info"))
            codes.append(("mechanism_still_live", "info"))
            return RouteVerdict(
                route_id=evidence.route_id,
                experiment_lineage_tag=evidence.experiment_lineage_tag,
                verdict="continue",
                reason_codes=codes,
            )

        # --- Pause ---
        codes.append(("weak_evidence", "medium"))
        return RouteVerdict(
            route_id=evidence.route_id,
            experiment_lineage_tag=evidence.experiment_lineage_tag,
            verdict="pause",
            reason_codes=codes,
        )
