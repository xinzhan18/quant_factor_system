"""Tests for CandidateJudge -- 6-dimension candidate verdict."""
from research.judge.candidate_judge import (
    CandidateEvidence,
    CandidateJudge,
    CandidateVerdict,
)
from research.judge.mechanism_alignment import AlignmentEvidence
from research.judge.replace_protocol import DiscreteComparison, HardConditions


class TestCandidateJudgeReject:
    def setup_method(self):
        self.judge = CandidateJudge()

    def test_reject_execution_gate_fail(self):
        ev = CandidateEvidence(
            candidate_id="C001",
            execution_gate_passed=False,
        )
        v = self.judge.judge(ev)
        assert v.verdict == "reject"
        assert any(c == "execution_gate_fail" for c, _ in v.reason_codes)

    def test_reject_known_bad_pattern(self):
        ev = CandidateEvidence(
            candidate_id="C002",
            known_bad_pattern=True,
        )
        v = self.judge.judge(ev)
        assert v.verdict == "reject"
        assert any(c == "known_bad_pattern" for c, _ in v.reason_codes)

    def test_reject_mechanism_drifted(self):
        ev = CandidateEvidence(
            candidate_id="C003",
            mechanism=AlignmentEvidence(
                thesis_match=False,
                route_question_match=True,
                sign_behavior_match=True,
                non_style_only=True,
            ),
        )
        v = self.judge.judge(ev)
        assert v.verdict == "reject"
        assert v.evidence_summary["mechanism_alignment"] == "drifted"

    def test_reject_sign_flip(self):
        ev = CandidateEvidence(
            candidate_id="C004",
            mechanism=AlignmentEvidence(
                thesis_match=True,
                route_question_match=True,
                sign_behavior_match=True,
                non_style_only=True,
            ),
            sign_flip=True,
        )
        v = self.judge.judge(ev)
        assert v.verdict == "reject"
        assert any(c == "sign_flip_detected" for c, _ in v.reason_codes)

    def test_reject_weak_and_poor_stability(self):
        ev = CandidateEvidence(
            candidate_id="C005",
            mechanism=AlignmentEvidence(
                thesis_match=True,
                route_question_match=True,
                sign_behavior_match=True,
                non_style_only=True,
            ),
            statistical_strength="weak",
            stability="poor",
        )
        v = self.judge.judge(ev)
        assert v.verdict == "reject"

    def test_reject_poor_feasibility(self):
        ev = CandidateEvidence(
            candidate_id="C006",
            mechanism=AlignmentEvidence(
                thesis_match=True,
                route_question_match=True,
                sign_behavior_match=True,
                non_style_only=True,
            ),
            feasibility="poor",
        )
        v = self.judge.judge(ev)
        assert v.verdict == "reject"


class TestCandidateJudgeAdmit:
    def setup_method(self):
        self.judge = CandidateJudge()

    def test_admit_strong_evidence(self):
        ev = CandidateEvidence(
            candidate_id="C010",
            mechanism=AlignmentEvidence(
                thesis_match=True,
                route_question_match=True,
                sign_behavior_match=True,
                non_style_only=True,
            ),
            statistical_strength="strong",
            stability="good",
            redundancy="low",
            feasibility="ok",
            risk_model_review="acceptable",
            expanding_window_pass=True,
        )
        v = self.judge.judge(ev)
        assert v.verdict == "admit"
        assert not v.holdout_review_required

    def test_admit_borderline_strength_good_stability(self):
        ev = CandidateEvidence(
            candidate_id="C011",
            mechanism=AlignmentEvidence(
                thesis_match=True,
                route_question_match=True,
                sign_behavior_match=True,
                non_style_only=True,
            ),
            statistical_strength="borderline",
            stability="good",
            redundancy="low",
            feasibility="ok",
        )
        v = self.judge.judge(ev)
        assert v.verdict == "admit"


class TestCandidateJudgeReserve:
    def setup_method(self):
        self.judge = CandidateJudge()

    def test_reserve_high_redundancy(self):
        ev = CandidateEvidence(
            candidate_id="C020",
            mechanism=AlignmentEvidence(
                thesis_match=True,
                route_question_match=True,
                sign_behavior_match=True,
                non_style_only=True,
            ),
            statistical_strength="strong",
            stability="good",
            redundancy="high",
            feasibility="ok",
        )
        v = self.judge.judge(ev)
        assert v.verdict == "reserve"

    def test_reserve_high_multiple_testing(self):
        ev = CandidateEvidence(
            candidate_id="C021",
            mechanism=AlignmentEvidence(
                thesis_match=True,
                route_question_match=True,
                sign_behavior_match=True,
                non_style_only=True,
            ),
            statistical_strength="strong",
            stability="good",
            redundancy="low",
            feasibility="ok",
            multiple_testing_risk_bucket="high",
        )
        v = self.judge.judge(ev)
        assert v.verdict == "reserve"
        assert v.holdout_review_required

    def test_reserve_repeated_sign_flip_warning(self):
        ev = CandidateEvidence(
            candidate_id="C022",
            mechanism=AlignmentEvidence(
                thesis_match=True,
                route_question_match=True,
                sign_behavior_match=True,
                non_style_only=True,
            ),
            statistical_strength="strong",
            stability="good",
            redundancy="low",
            feasibility="ok",
            support_window_warning="repeated_sign_flip",
        )
        v = self.judge.judge(ev)
        assert v.verdict == "reserve"
        assert v.holdout_review_required

    def test_reserve_expanding_window_fail(self):
        ev = CandidateEvidence(
            candidate_id="C023",
            mechanism=AlignmentEvidence(
                thesis_match=True,
                route_question_match=True,
                sign_behavior_match=True,
                non_style_only=True,
            ),
            statistical_strength="strong",
            stability="good",
            redundancy="low",
            feasibility="ok",
            expanding_window_pass=False,
        )
        v = self.judge.judge(ev)
        assert v.verdict == "reserve"


class TestCandidateJudgeReplace:
    def setup_method(self):
        self.judge = CandidateJudge()

    def test_replace_verdict(self):
        ev = CandidateEvidence(
            candidate_id="C030",
            mechanism=AlignmentEvidence(
                thesis_match=True,
                route_question_match=True,
                sign_behavior_match=True,
                non_style_only=True,
            ),
            statistical_strength="strong",
            stability="good",
            redundancy="low",
            feasibility="ok",
            replace_hard=HardConditions(
                high_similarity=True,
                no_sign_flip=True,
                residual_ic_not_worse=True,
            ),
            replace_comparison=DiscreteComparison(
                stability_compare="better",
                redundancy_compare="better",
                mechanism_cleanliness_compare="similar",
            ),
            replace_target_id="F042",
        )
        v = self.judge.judge(ev)
        assert v.verdict == "replace"
        assert v.replace_target_id == "F042"
        assert v.replace_result is not None

    def test_replace_marginal_becomes_reserve(self):
        ev = CandidateEvidence(
            candidate_id="C031",
            mechanism=AlignmentEvidence(
                thesis_match=True,
                route_question_match=True,
                sign_behavior_match=True,
                non_style_only=True,
            ),
            statistical_strength="strong",
            stability="good",
            redundancy="low",
            feasibility="ok",
            replace_hard=HardConditions(
                high_similarity=True,
                no_sign_flip=True,
                residual_ic_not_worse=True,
            ),
            replace_comparison=DiscreteComparison(
                stability_compare="better",
                redundancy_compare="similar",
                mechanism_cleanliness_compare="similar",
            ),
            replace_target_id="F042",
        )
        v = self.judge.judge(ev)
        assert v.verdict == "reserve"
        assert v.holdout_review_required

    def test_to_dict_structure(self):
        ev = CandidateEvidence(
            candidate_id="C040",
            mechanism=AlignmentEvidence(
                thesis_match=True,
                route_question_match=True,
                sign_behavior_match=True,
                non_style_only=True,
            ),
        )
        v = self.judge.judge(ev)
        d = v.to_dict()
        assert "candidate_id" in d
        assert "verdict" in d
        assert "reason_codes" in d
        assert isinstance(d["reason_codes"], list)
        assert "evidence_summary" in d
