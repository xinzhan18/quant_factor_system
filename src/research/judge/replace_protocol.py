"""Replace protocol -- 5-dimension discrete comparison for factor replacement.

Hard conditions (all must pass):
    1. High similarity with existing factor
    2. No sign flip (fatal regression)
    3. Residual IC not significantly worse

Then 5 discrete comparisons (better / similar / worse):
    Main dimensions:
        - stability_compare
        - redundancy_compare
        - mechanism_cleanliness_compare
    Auxiliary dimensions:
        - statistical_strength_compare
        - feasibility_compare

Decision rules:
    replace             -- >=2 main better, no main worse, no aux materially worse
    reserve_for_review  -- 1 main better, or all similar with aux improvement
    no_replace          -- any main worse, or no improvement shown
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


VALID_COMPARISONS = ("better", "similar", "worse")
VALID_DECISIONS = ("replace", "reserve_for_review", "no_replace")


@dataclass
class HardConditions:
    """Hard preconditions that must all pass before discrete comparison."""

    high_similarity: bool = False
    no_sign_flip: bool = True
    residual_ic_not_worse: bool = True


@dataclass
class DiscreteComparison:
    """5-dimension discrete comparison between new and existing factor.

    Each value must be one of: better, similar, worse.
    """

    stability_compare: str = "similar"
    redundancy_compare: str = "similar"
    mechanism_cleanliness_compare: str = "similar"
    statistical_strength_compare: str = "similar"
    feasibility_compare: str = "similar"

    # Whether auxiliary dimensions are materially worse (not just worse)
    feasibility_materially_worse: bool = False
    strength_materially_worse: bool = False

    def __post_init__(self) -> None:
        for dim in (
            "stability_compare",
            "redundancy_compare",
            "mechanism_cleanliness_compare",
            "statistical_strength_compare",
            "feasibility_compare",
        ):
            val = getattr(self, dim)
            if val not in VALID_COMPARISONS:
                raise ValueError(
                    f"{dim} must be one of {VALID_COMPARISONS}, got '{val}'"
                )


@dataclass
class ReplaceResult:
    """Output of the replace protocol."""

    decision: str  # replace / reserve_for_review / no_replace
    hard_conditions_passed: bool
    hard_failure_reason: str = ""
    main_better_count: int = 0
    main_worse_count: int = 0
    has_materially_worse_aux: bool = False
    reason_codes: list = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "decision": self.decision,
            "hard_conditions_passed": self.hard_conditions_passed,
            "hard_failure_reason": self.hard_failure_reason,
            "main_better_count": self.main_better_count,
            "main_worse_count": self.main_worse_count,
            "has_materially_worse_aux": self.has_materially_worse_aux,
            "reason_codes": list(self.reason_codes),
        }


class ReplaceProtocol:
    """Evaluate whether a new factor should replace an existing one."""

    def evaluate(
        self,
        hard: HardConditions,
        comparison: DiscreteComparison,
    ) -> ReplaceResult:
        """Run hard gate then discrete comparison to decide replace/no_replace.

        Returns:
            ReplaceResult with decision and supporting evidence.
        """
        # --- Hard gate ---
        if not hard.high_similarity:
            return ReplaceResult(
                decision="no_replace",
                hard_conditions_passed=False,
                hard_failure_reason="low_similarity",
                reason_codes=[("low_similarity", "high")],
            )
        if not hard.no_sign_flip:
            return ReplaceResult(
                decision="no_replace",
                hard_conditions_passed=False,
                hard_failure_reason="sign_flip_detected",
                reason_codes=[("sign_flip_detected", "fatal")],
            )
        if not hard.residual_ic_not_worse:
            return ReplaceResult(
                decision="no_replace",
                hard_conditions_passed=False,
                hard_failure_reason="residual_ic_regression",
                reason_codes=[("residual_ic_regression", "high")],
            )

        # --- Discrete comparison ---
        main_dims = [
            comparison.stability_compare,
            comparison.redundancy_compare,
            comparison.mechanism_cleanliness_compare,
        ]
        main_better = sum(1 for d in main_dims if d == "better")
        main_worse = sum(1 for d in main_dims if d == "worse")

        aux_materially_worse = (
            comparison.feasibility_materially_worse
            or comparison.strength_materially_worse
        )

        reason_codes: list = []

        # Any main dimension worse -> no_replace
        if main_worse > 0:
            reason_codes.append(("main_dimension_regression", "high"))
            return ReplaceResult(
                decision="no_replace",
                hard_conditions_passed=True,
                main_better_count=main_better,
                main_worse_count=main_worse,
                has_materially_worse_aux=aux_materially_worse,
                reason_codes=reason_codes,
            )

        # Materially worse on aux -> no_replace
        if aux_materially_worse:
            reason_codes.append(("auxiliary_materially_worse", "high"))
            return ReplaceResult(
                decision="no_replace",
                hard_conditions_passed=True,
                main_better_count=main_better,
                main_worse_count=main_worse,
                has_materially_worse_aux=True,
                reason_codes=reason_codes,
            )

        # Replace: >=2 main better, no main worse, no aux materially worse
        if main_better >= 2:
            reason_codes.append(("replace_justified", "info"))
            return ReplaceResult(
                decision="replace",
                hard_conditions_passed=True,
                main_better_count=main_better,
                main_worse_count=0,
                has_materially_worse_aux=False,
                reason_codes=reason_codes,
            )

        # Reserve: 1 main better, or all similar with aux improvement
        aux_dims = [
            comparison.statistical_strength_compare,
            comparison.feasibility_compare,
        ]
        aux_better = sum(1 for d in aux_dims if d == "better")

        if main_better == 1 or (main_better == 0 and aux_better > 0):
            reason_codes.append(("marginal_improvement", "medium"))
            return ReplaceResult(
                decision="reserve_for_review",
                hard_conditions_passed=True,
                main_better_count=main_better,
                main_worse_count=0,
                has_materially_worse_aux=False,
                reason_codes=reason_codes,
            )

        # All similar, no aux improvement
        reason_codes.append(("no_improvement_shown", "medium"))
        return ReplaceResult(
            decision="no_replace",
            hard_conditions_passed=True,
            main_better_count=0,
            main_worse_count=0,
            has_materially_worse_aux=False,
            reason_codes=reason_codes,
        )
