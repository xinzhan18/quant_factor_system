"""Execution gate: technical pass/warn/fail classification.

The execution gate sits after statistical evidence generation but before
the judge.  It answers one question: **can this candidate be formally
evaluated, or should it be filtered out on technical grounds?**

It does NOT make admission decisions -- that is the judge's job.

Design reference: ``docs/refacor_logic/research_execute.md`` section 8.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class GateResult:
    """Outcome of the execution gate."""

    status: str  # "pass" | "warn" | "fail_technical"
    reason_codes: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {"status": self.status, "reason_codes": list(self.reason_codes)}


# ---------------------------------------------------------------------------
# Thresholds (intentionally kept as module-level constants so they are easy
# to find and override in tests)
# ---------------------------------------------------------------------------
MIN_VALID_RATIO = 0.10
WARN_VALID_RATIO = 0.30
MIN_VARIANCE = 1e-8
MAX_OUTLIER_RATIO = 0.50
WARN_OUTLIER_RATIO = 0.25
MAX_TURNOVER = 3.0
WARN_TURNOVER = 1.5
MIN_LIQUIDITY_COVERAGE = 0.10
WARN_LIQUIDITY_COVERAGE = 0.30


class ExecutionGate:
    """Classify a candidate result as pass / warn / fail_technical.

    The gate checks four areas (per the design doc):
    1. Computation gate  -- computable, non-empty, non-constant
    2. Basic quality gate -- coverage, sign, outliers
    3. Stability gate    -- train/validation not completely flipped
    4. Feasibility gate  -- turnover, liquidity not extreme
    """

    def evaluate(self, result: Dict[str, Any]) -> GateResult:
        """Run all gate checks against a candidate result dict.

        Parameters
        ----------
        result:
            A candidate result dictionary containing at minimum
            ``precheck``, ``diagnostics``, ``evaluation``, and
            ``feasibility`` sub-dicts.  Missing keys are tolerated
            and treated conservatively.

        Returns
        -------
        GateResult
        """
        reasons: List[str] = []
        has_fatal = False

        # --- 1. Computation gate ---
        precheck = result.get("precheck", {})
        if precheck.get("status") == "failed":
            return GateResult(
                status="fail_technical",
                reason_codes=["precheck_failed"] + precheck.get("reason_codes", []),
            )

        diag = result.get("diagnostics", {})
        valid_ratio = diag.get("base_valid_ratio")
        if valid_ratio is not None:
            if valid_ratio < MIN_VALID_RATIO:
                reasons.append("valid_ratio_too_low")
                has_fatal = True
            elif valid_ratio < WARN_VALID_RATIO:
                reasons.append("valid_ratio_low")

        variance = diag.get("base_variance")
        if variance is not None and variance < MIN_VARIANCE:
            reasons.append("near_constant_signal")
            has_fatal = True

        # --- 2. Basic quality gate ---
        outlier_ratio = diag.get("base_outlier_ratio")
        if outlier_ratio is not None:
            if outlier_ratio > MAX_OUTLIER_RATIO:
                reasons.append("extreme_outlier_ratio")
                has_fatal = True
            elif outlier_ratio > WARN_OUTLIER_RATIO:
                reasons.append("high_outlier_ratio")

        evaluation = result.get("evaluation", {})
        sign_consistency = evaluation.get("sign_consistency")
        if sign_consistency is False:
            # train and validation have opposite sign -- not necessarily fatal
            # but serious enough to warn
            reasons.append("sign_inconsistency")

        # --- 3. Stability gate ---
        decay_ratio = evaluation.get("train_validation_decay_ratio")
        if decay_ratio is not None and decay_ratio < 0:
            # Negative decay ratio means validation flipped sign vs train
            reasons.append("train_validation_sign_flip")
            has_fatal = True

        split_stability = evaluation.get("split_stability")
        if split_stability == "low":
            reasons.append("poor_split_stability")

        # --- 4. Feasibility gate ---
        feasibility = result.get("feasibility", {})
        turnover = feasibility.get("turnover")
        if turnover is not None:
            if turnover > MAX_TURNOVER:
                reasons.append("extreme_turnover")
                has_fatal = True
            elif turnover > WARN_TURNOVER:
                reasons.append("high_turnover")

        liq_coverage = feasibility.get("liquidity_coverage_ratio")
        if liq_coverage is not None:
            if liq_coverage < MIN_LIQUIDITY_COVERAGE:
                reasons.append("extreme_low_liquidity")
                has_fatal = True
            elif liq_coverage < WARN_LIQUIDITY_COVERAGE:
                reasons.append("low_liquidity_coverage")

        tail_concentration = feasibility.get("tail_trade_concentration")
        if tail_concentration is not None and tail_concentration > 0.80:
            reasons.append("extreme_tail_concentration")
            has_fatal = True

        # --- classify ---
        if has_fatal:
            status = "fail_technical"
        elif reasons:
            status = "warn"
        else:
            status = "pass"

        return GateResult(status=status, reason_codes=reasons)
