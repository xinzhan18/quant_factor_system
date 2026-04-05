"""4-dimension review gate for logic proposals.

Each proposal is reviewed on four axes:
- **mechanism**:       Does it have an independent market mechanism?
- **feasibility**:     Can the current platform implement it?
- **novelty**:         Is it distinct from existing logics?
- **research_value**:  Is it worth the exploration budget?

Each dimension produces a verdict (pass/borderline/fail) and a score [0, 1].
The aggregate verdict determines the outcome:
    create_logic | downgrade_to_direction | park | reject
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from research.logic._yaml_utils import dump_yaml, now_ts

logger = logging.getLogger(__name__)

REVIEW_DIMENSIONS = ("mechanism", "feasibility", "novelty", "research_value")
VALID_VERDICTS = frozenset({"pass", "borderline", "fail"})
REVIEW_OUTCOMES = frozenset(
    {"create_logic", "downgrade_to_direction", "park", "reject"}
)


@dataclass
class DimensionReview:
    """Result for a single review dimension."""

    verdict: str  # pass / borderline / fail
    score: float  # 0.0 - 1.0
    comments: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.verdict not in VALID_VERDICTS:
            raise ValueError(
                f"Invalid verdict {self.verdict!r}; "
                f"must be one of {sorted(VALID_VERDICTS)}"
            )
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"Score must be in [0, 1], got {self.score}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "verdict": self.verdict,
            "score": self.score,
            "comments": self.comments,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DimensionReview":
        return cls(
            verdict=data["verdict"],
            score=data["score"],
            comments=data.get("comments", []),
        )


@dataclass
class LogicReview:
    """Aggregate review for a proposal."""

    proposal_id: str
    mechanism: DimensionReview
    feasibility: DimensionReview
    novelty: DimensionReview
    research_value: DimensionReview
    outcome: str = ""  # set by compute_outcome()
    outcome_reason: str = ""
    reviewed_at: str = ""
    target_logic_id: Optional[str] = None  # for downgrade_to_direction

    def __post_init__(self) -> None:
        if not self.reviewed_at:
            self.reviewed_at = now_ts()
        if not self.outcome:
            self.outcome = self.compute_outcome()

    @property
    def dimensions(self) -> Dict[str, DimensionReview]:
        return {
            "mechanism": self.mechanism,
            "feasibility": self.feasibility,
            "novelty": self.novelty,
            "research_value": self.research_value,
        }

    def compute_outcome(self) -> str:
        """Derive the aggregate outcome from dimension verdicts.

        Rules:
        - Any fail in mechanism or feasibility -> reject
        - All pass -> create_logic
        - novelty fail (others pass/borderline) -> downgrade_to_direction
        - Otherwise (borderline mix) -> park
        """
        dims = self.dimensions

        # Hard reject: mechanism or feasibility fail
        if dims["mechanism"].verdict == "fail":
            self.outcome_reason = "mechanism review failed"
            return "reject"
        if dims["feasibility"].verdict == "fail":
            self.outcome_reason = "feasibility review failed"
            return "reject"

        # Novelty fail means it's a sub-direction, not a new logic
        if dims["novelty"].verdict == "fail":
            self.outcome_reason = "not novel enough; subsumable under existing logic"
            return "downgrade_to_direction"

        # All pass -> create
        if all(d.verdict == "pass" for d in dims.values()):
            self.outcome_reason = "all dimensions passed"
            return "create_logic"

        # Research value fail -> park
        if dims["research_value"].verdict == "fail":
            self.outcome_reason = "research value too low to justify budget"
            return "park"

        # Mixed borderline: park if too many borderlines, else create
        borderline_count = sum(
            1 for d in dims.values() if d.verdict == "borderline"
        )
        if borderline_count >= 3:
            self.outcome_reason = (
                f"{borderline_count} borderline dimensions; needs more evidence"
            )
            return "park"

        self.outcome_reason = "sufficient dimensions passed"
        return "create_logic"

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "proposal_id": self.proposal_id,
            "schema_version": "v2",
            "mechanism_review": self.mechanism.to_dict(),
            "feasibility_review": self.feasibility.to_dict(),
            "novelty_review": self.novelty.to_dict(),
            "research_value_review": self.research_value.to_dict(),
            "outcome": self.outcome,
            "outcome_reason": self.outcome_reason,
            "reviewed_at": self.reviewed_at,
        }
        if self.target_logic_id:
            d["target_logic_id"] = self.target_logic_id
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogicReview":
        return cls(
            proposal_id=data["proposal_id"],
            mechanism=DimensionReview.from_dict(data["mechanism_review"]),
            feasibility=DimensionReview.from_dict(data["feasibility_review"]),
            novelty=DimensionReview.from_dict(data["novelty_review"]),
            research_value=DimensionReview.from_dict(
                data["research_value_review"]
            ),
            outcome=data.get("outcome", ""),
            outcome_reason=data.get("outcome_reason", ""),
            reviewed_at=data.get("reviewed_at", ""),
            target_logic_id=data.get("target_logic_id"),
        )


def review_proposal(
    proposal_id: str,
    *,
    mechanism: DimensionReview,
    feasibility: DimensionReview,
    novelty: DimensionReview,
    research_value: DimensionReview,
    target_logic_id: Optional[str] = None,
) -> LogicReview:
    """Build a LogicReview from four dimension reviews.

    The outcome is computed automatically from the verdicts.
    """
    return LogicReview(
        proposal_id=proposal_id,
        mechanism=mechanism,
        feasibility=feasibility,
        novelty=novelty,
        research_value=research_value,
        target_logic_id=target_logic_id,
    )


def save_review(storage_dir: Path, review: LogicReview) -> Path:
    """Persist a review to ``storage/logic/reviews/review_<id>.yaml``."""
    reviews_dir = storage_dir / "logic" / "reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    path = reviews_dir / f"review_{review.proposal_id}.yaml"
    dump_yaml(path, review.to_dict())
    logger.info(
        "Saved review for %s -> %s at %s",
        review.proposal_id,
        review.outcome,
        path,
    )
    return path


def load_review(
    storage_dir: Path, proposal_id: str
) -> Optional[LogicReview]:
    """Load a review by proposal ID. Returns None if not found."""
    path = storage_dir / "logic" / "reviews" / f"review_{proposal_id}.yaml"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return LogicReview.from_dict(data)
