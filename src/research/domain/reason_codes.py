"""Reason codes with severity mapping.

Every gate / check / review in the research pipeline emits a reason code
when it triggers.  Downstream consumers (judge, reporting, memory) use
severity to decide whether the code is fatal (auto-reject), high
(strong negative signal), medium (flag for review) or info (contextual).

Categories follow research_judge.md Section 10.
"""

from __future__ import annotations

import enum
from typing import Dict, List


class Severity(enum.Enum):
    """How seriously a reason code should be treated."""

    FATAL = "fatal"
    HIGH = "high"
    MEDIUM = "medium"
    INFO = "info"


class ReasonCode(enum.Enum):
    """Structured reason codes emitted by gates and reviews.

    Naming convention: ``<CATEGORY>_<DETAIL>``.
    Each member's value is a ``(code_string, severity)`` tuple so that
    ``ReasonCode.STRENGTH_IC_TOO_LOW.severity`` works directly.
    """

    # --- Strength ---
    STRENGTH_IC_TOO_LOW = ("strength_ic_too_low", Severity.FATAL)
    STRENGTH_ICIR_TOO_LOW = ("strength_icir_too_low", Severity.HIGH)
    STRENGTH_LS_TSTAT_WEAK = ("strength_ls_tstat_weak", Severity.HIGH)
    STRENGTH_MONOTONICITY_POOR = ("strength_monotonicity_poor", Severity.HIGH)
    STRENGTH_SHARPE_LOW = ("strength_sharpe_low", Severity.MEDIUM)
    STRENGTH_LONG_CONTRIBUTION_LOW = ("strength_long_contribution_low", Severity.MEDIUM)

    # --- Stability ---
    STABILITY_OOS_DECAY = ("stability_oos_decay", Severity.FATAL)
    STABILITY_IC_SIGN_FLIP = ("stability_ic_sign_flip", Severity.HIGH)
    STABILITY_REGIME_MISMATCH = ("stability_regime_mismatch", Severity.HIGH)
    STABILITY_EXPANDING_WINDOW_FAIL = ("stability_expanding_window_fail", Severity.MEDIUM)
    STABILITY_BOOTSTRAP_WIDE = ("stability_bootstrap_wide", Severity.MEDIUM)

    # --- Redundancy ---
    REDUNDANCY_HIGH_CORRELATION = ("redundancy_high_correlation", Severity.FATAL)
    REDUNDANCY_FAMILY_SATURATED = ("redundancy_family_saturated", Severity.HIGH)
    REDUNDANCY_SUBSPACE_CROWDED = ("redundancy_subspace_crowded", Severity.MEDIUM)
    REDUNDANCY_INCREMENTAL_IC_LOW = ("redundancy_incremental_ic_low", Severity.HIGH)

    # --- Feasibility ---
    FEASIBILITY_COVERAGE_LOW = ("feasibility_coverage_low", Severity.FATAL)
    FEASIBILITY_TURNOVER_HIGH = ("feasibility_turnover_high", Severity.HIGH)
    FEASIBILITY_COMPUTATION_SLOW = ("feasibility_computation_slow", Severity.MEDIUM)
    FEASIBILITY_DATA_DEPENDENCY = ("feasibility_data_dependency", Severity.MEDIUM)

    # --- Mechanism ---
    MECHANISM_NO_THESIS = ("mechanism_no_thesis", Severity.HIGH)
    MECHANISM_SIZE_PROXY = ("mechanism_size_proxy", Severity.HIGH)
    MECHANISM_STYLE_REPACKAGING = ("mechanism_style_repackaging", Severity.MEDIUM)
    MECHANISM_ALIGNMENT_WEAK = ("mechanism_alignment_weak", Severity.MEDIUM)

    # --- Policy ---
    POLICY_FORBIDDEN_PATTERN = ("policy_forbidden_pattern", Severity.FATAL)
    POLICY_HOLDOUT_CONTAMINATION = ("policy_holdout_contamination", Severity.FATAL)
    POLICY_SAMPLE_VIOLATION = ("policy_sample_violation", Severity.FATAL)
    POLICY_IMPLEMENTATION_BLOCKED = ("policy_implementation_blocked", Severity.HIGH)

    # --- Info ---
    INFO_NEAR_MISS = ("info_near_miss", Severity.INFO)
    INFO_BORDERLINE_STABILITY = ("info_borderline_stability", Severity.INFO)
    INFO_SUPPORT_WINDOW_WARNING = ("info_support_window_warning", Severity.INFO)
    INFO_HOLDOUT_REVIEW_RECOMMENDED = ("info_holdout_review_recommended", Severity.INFO)

    def __init__(self, code_str: str, severity: Severity) -> None:
        self.code_str = code_str
        self.severity = severity

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------

    @property
    def is_fatal(self) -> bool:
        return self.severity is Severity.FATAL

    @classmethod
    def fatal_codes(cls) -> List["ReasonCode"]:
        """Return all codes with FATAL severity."""
        return [rc for rc in cls if rc.severity is Severity.FATAL]


# ---------------------------------------------------------------------------
# Severity colour map (for reports / CLI output)
# ---------------------------------------------------------------------------

SEVERITY_COLOURS: Dict[Severity, str] = {
    Severity.FATAL: "red",
    Severity.HIGH: "orange",
    Severity.MEDIUM: "yellow",
    Severity.INFO: "grey",
}
