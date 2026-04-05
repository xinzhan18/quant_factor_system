"""Candidate judge -- 6-dimension verdict for individual factor candidates.

Dimensions:
    1. mechanism_alignment  (aligned / unclear / drifted)
    2. statistical_strength (strong / borderline / weak)
    3. stability            (good / borderline / poor)
    4. redundancy           (low / acceptable / high)
    5. feasibility          (ok / borderline / poor)
    6. risk_model_review    (acceptable / borderline / poor)

Verdicts: admit / reserve / reject / replace
    Each verdict includes reason_codes with severity levels.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from research.judge.mechanism_alignment import (
    AlignmentEvidence,
    AlignmentResult,
    MechanismAlignment,
)
from research.judge.replace_protocol import (
    DiscreteComparison,
    HardConditions,
    ReplaceProtocol,
    ReplaceResult,
)


# ------------------------------------------------------------------
# Severity constants
# ------------------------------------------------------------------
FATAL = "fatal"
HIGH = "high"
MEDIUM = "medium"
INFO = "info"

# Reason-code catalog with default severities
REASON_CODES: Dict[str, str] = {
    # Strength
    "strong_validation_effect": INFO,
    "borderline_validation_effect": MEDIUM,
    "weak_validation_effect": HIGH,
    # Stability
    "good_split_stability": INFO,
    "poor_split_stability": HIGH,
    "regime_instability": MEDIUM,
    "sign_flip_detected": FATAL,
    # Redundancy
    "high_pairwise_overlap": HIGH,
    "high_family_overlap": HIGH,
    "high_subspace_redundancy": HIGH,
    "low_incremental_value": HIGH,
    # Feasibility
    "feasibility_ok": INFO,
    "feasibility_borderline": MEDIUM,
    "feasibility_poor": HIGH,
    # Risk model review
    "risk_model_acceptable": INFO,
    "moderate_style_exposure": MEDIUM,
    "style_dominance_detected": HIGH,
    # Mechanism
    "mechanism_aligned": INFO,
    "mechanism_unclear": MEDIUM,
    "mechanism_drifted": FATAL,
    # Policy
    "known_bad_pattern": FATAL,
    "implementation_too_complex": MEDIUM,
    "holdout_review_required": MEDIUM,
    "high_data_mining_risk": MEDIUM,
}


@dataclass
class CandidateEvidence:
    """Structured evidence bundle for a single candidate."""

    candidate_id: str = ""

    # Mechanism alignment inputs
    mechanism: AlignmentEvidence = field(default_factory=AlignmentEvidence)

    # Statistical strength: strong / borderline / weak
    statistical_strength: str = "borderline"

    # Stability: good / borderline / poor
    stability: str = "borderline"
    sign_flip: bool = False

    # Redundancy: low / acceptable / high
    redundancy: str = "acceptable"

    # Feasibility: ok / borderline / poor
    feasibility: str = "ok"

    # Risk model review: acceptable / borderline / poor
    risk_model_review: str = "acceptable"

    # Execution gate
    execution_gate_passed: bool = True

    # Expanding window
    expanding_window_pass: bool = True

    # Known bad pattern match
    known_bad_pattern: bool = False

    # Multiple testing risk bucket
    multiple_testing_risk_bucket: str = "low"  # low / medium / high

    # Support window warning
    support_window_warning: str = "none"  # none / some / repeated_sign_flip

    # Replace context (optional -- only when a replace candidate exists)
    replace_hard: Optional[HardConditions] = None
    replace_comparison: Optional[DiscreteComparison] = None
    replace_target_id: Optional[str] = None

    @classmethod
    def from_judge_packet_brief(cls, brief: Dict[str, Any]) -> "CandidateEvidence":
        """Construct CandidateEvidence from a judge packet candidate brief.

        This closes the brief→evidence mapping in code rather than
        relying on LLM skill prompts.
        """
        return cls(
            candidate_id=brief.get("candidate_id", ""),
            statistical_strength=brief.get("validation_effect_bucket", "borderline"),
            stability=brief.get("stability_bucket", "borderline"),
            redundancy=brief.get("redundancy_bucket", "acceptable"),
            feasibility=brief.get("feasibility_bucket", "ok"),
            risk_model_review=brief.get("risk_model_review_bucket", "acceptable"),
            execution_gate_passed=brief.get("execution_gate_status") == "pass",
            support_window_warning=brief.get("support_window_warning", "none"),
        )


@dataclass
class CandidateVerdict:
    """Verdict for a single candidate factor."""

    candidate_id: str
    verdict: str  # admit / reserve / reject / replace
    reason_codes: List[Tuple[str, str]] = field(default_factory=list)
    evidence_summary: Dict[str, str] = field(default_factory=dict)
    holdout_review_required: bool = False
    replace_target_id: Optional[str] = None
    replace_result: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "candidate_id": self.candidate_id,
            "verdict": self.verdict,
            "reason_codes": [
                {"code": code, "severity": sev} for code, sev in self.reason_codes
            ],
            "evidence_summary": dict(self.evidence_summary),
            "holdout_review_required": self.holdout_review_required,
        }
        if self.replace_target_id is not None:
            result["replace_target_id"] = self.replace_target_id
        if self.replace_result is not None:
            result["replace_result"] = self.replace_result
        return result


class CandidateJudge:
    """Judge a candidate factor across 6 evidence dimensions."""

    def __init__(self) -> None:
        self._alignment = MechanismAlignment()
        self._replace = ReplaceProtocol()

    def judge(self, evidence: CandidateEvidence) -> CandidateVerdict:
        """Produce a structured verdict for a single candidate.

        The verdict is driven by hard gates and dimension evidence,
        NOT by composite scores.
        """
        codes: List[Tuple[str, str]] = []
        summary: Dict[str, str] = {}

        # 1. Execution gate
        if not evidence.execution_gate_passed:
            codes.append(("execution_gate_fail", FATAL))
            return CandidateVerdict(
                candidate_id=evidence.candidate_id,
                verdict="reject",
                reason_codes=codes,
                evidence_summary={"execution_gate": "fail"},
            )

        # 2. Known bad pattern
        if evidence.known_bad_pattern:
            codes.append(("known_bad_pattern", FATAL))
            return CandidateVerdict(
                candidate_id=evidence.candidate_id,
                verdict="reject",
                reason_codes=codes,
                evidence_summary={"known_bad_pattern": "true"},
            )

        # 3. Mechanism alignment
        alignment = self._alignment.evaluate(evidence.mechanism)
        codes.append((alignment.reason_code, alignment.severity))
        summary["mechanism_alignment"] = alignment.verdict

        if alignment.verdict == "drifted":
            return CandidateVerdict(
                candidate_id=evidence.candidate_id,
                verdict="reject",
                reason_codes=codes,
                evidence_summary=summary,
            )

        # 4. Sign flip -- fatal
        if evidence.sign_flip:
            codes.append(("sign_flip_detected", FATAL))
            return CandidateVerdict(
                candidate_id=evidence.candidate_id,
                verdict="reject",
                reason_codes=codes,
                evidence_summary=summary,
            )

        # 5. Collect dimension evidence
        # Statistical strength
        strength_map = {
            "strong": ("strong_validation_effect", INFO),
            "borderline": ("borderline_validation_effect", MEDIUM),
            "weak": ("weak_validation_effect", HIGH),
        }
        s_code, s_sev = strength_map.get(
            evidence.statistical_strength,
            ("borderline_validation_effect", MEDIUM),
        )
        codes.append((s_code, s_sev))
        summary["statistical_strength"] = evidence.statistical_strength

        # Stability
        stab_map = {
            "good": ("good_split_stability", INFO),
            "borderline": ("regime_instability", MEDIUM),
            "poor": ("poor_split_stability", HIGH),
        }
        st_code, st_sev = stab_map.get(
            evidence.stability, ("regime_instability", MEDIUM)
        )
        codes.append((st_code, st_sev))
        summary["stability"] = evidence.stability

        # Redundancy
        red_map = {
            "low": ("feasibility_ok", INFO),  # no redundancy issue
            "acceptable": ("high_family_overlap", MEDIUM),
            "high": ("high_subspace_redundancy", HIGH),
        }
        r_code, r_sev = red_map.get(
            evidence.redundancy, ("high_family_overlap", MEDIUM)
        )
        codes.append((r_code, r_sev))
        summary["redundancy"] = evidence.redundancy

        # Feasibility
        feas_map = {
            "ok": ("feasibility_ok", INFO),
            "borderline": ("feasibility_borderline", MEDIUM),
            "poor": ("feasibility_poor", HIGH),
        }
        f_code, f_sev = feas_map.get(
            evidence.feasibility, ("feasibility_borderline", MEDIUM)
        )
        codes.append((f_code, f_sev))
        summary["feasibility"] = evidence.feasibility

        # Risk model review
        risk_map = {
            "acceptable": ("risk_model_acceptable", INFO),
            "borderline": ("moderate_style_exposure", MEDIUM),
            "poor": ("style_dominance_detected", HIGH),
        }
        r_code, r_sev = risk_map.get(
            evidence.risk_model_review, ("risk_model_acceptable", INFO)
        )
        codes.append((r_code, r_sev))
        summary["risk_model_review"] = evidence.risk_model_review

        # Support window warning
        summary["support_window_warning"] = evidence.support_window_warning

        # 6. Check for replace scenario
        if (
            evidence.replace_hard is not None
            and evidence.replace_comparison is not None
        ):
            replace_result = self._replace.evaluate(
                evidence.replace_hard, evidence.replace_comparison
            )
            if replace_result.decision == "replace":
                return CandidateVerdict(
                    candidate_id=evidence.candidate_id,
                    verdict="replace",
                    reason_codes=codes,
                    evidence_summary=summary,
                    replace_target_id=evidence.replace_target_id,
                    replace_result=replace_result.to_dict(),
                )
            if replace_result.decision == "reserve_for_review":
                codes.append(("holdout_review_required", MEDIUM))
                return CandidateVerdict(
                    candidate_id=evidence.candidate_id,
                    verdict="reserve",
                    reason_codes=codes,
                    evidence_summary=summary,
                    holdout_review_required=True,
                    replace_target_id=evidence.replace_target_id,
                    replace_result=replace_result.to_dict(),
                )

        # 7. Verdict logic (hard-gate driven, not score driven)
        has_fatal = any(sev == FATAL for _, sev in codes)
        has_high = any(sev == HIGH for _, sev in codes)

        # Reject: any fatal, or weak + poor stability
        if has_fatal:
            return CandidateVerdict(
                candidate_id=evidence.candidate_id,
                verdict="reject",
                reason_codes=codes,
                evidence_summary=summary,
            )
        if evidence.statistical_strength == "weak" and evidence.stability == "poor":
            return CandidateVerdict(
                candidate_id=evidence.candidate_id,
                verdict="reject",
                reason_codes=codes,
                evidence_summary=summary,
            )
        if evidence.feasibility == "poor":
            return CandidateVerdict(
                candidate_id=evidence.candidate_id,
                verdict="reject",
                reason_codes=codes,
                evidence_summary=summary,
            )

        # Holdout review conditions
        holdout_needed = (
            evidence.multiple_testing_risk_bucket == "high"
            or evidence.support_window_warning == "repeated_sign_flip"
        )

        # Reserve: borderline evidence or high-severity issues
        if has_high or holdout_needed:
            return CandidateVerdict(
                candidate_id=evidence.candidate_id,
                verdict="reserve",
                reason_codes=codes,
                evidence_summary=summary,
                holdout_review_required=holdout_needed,
            )

        # Expanding window gate
        if not evidence.expanding_window_pass:
            codes.append(("expanding_window_fail", HIGH))
            return CandidateVerdict(
                candidate_id=evidence.candidate_id,
                verdict="reserve",
                reason_codes=codes,
                evidence_summary=summary,
            )

        # Admit: no fatal, no high, expanding pass, not holdout-required
        return CandidateVerdict(
            candidate_id=evidence.candidate_id,
            verdict="admit",
            reason_codes=codes,
            evidence_summary=summary,
        )
