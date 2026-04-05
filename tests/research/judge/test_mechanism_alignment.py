"""Tests for MechanismAlignment -- 4-check alignment assessment."""
from research.judge.mechanism_alignment import (
    AlignmentEvidence,
    AlignmentResult,
    MechanismAlignment,
)


class TestMechanismAlignment:
    def setup_method(self):
        self.alignment = MechanismAlignment()

    def test_aligned_all_pass(self):
        """All 4 checks pass -> aligned."""
        ev = AlignmentEvidence(
            thesis_match=True,
            route_question_match=True,
            sign_behavior_match=True,
            non_style_only=True,
        )
        result = self.alignment.evaluate(ev)
        assert result.verdict == "aligned"
        assert result.checks_passed == 4
        assert result.reason_code == "mechanism_aligned"
        assert result.severity == "info"

    def test_aligned_three_pass(self):
        """3 of 4 checks pass (sign mismatch) -> aligned if non_style ok."""
        ev = AlignmentEvidence(
            thesis_match=True,
            route_question_match=True,
            sign_behavior_match=False,
            non_style_only=True,
        )
        result = self.alignment.evaluate(ev)
        assert result.verdict == "aligned"
        assert result.checks_passed == 3

    def test_drifted_style_only(self):
        """non_style_only False -> drifted regardless of other checks."""
        ev = AlignmentEvidence(
            thesis_match=True,
            route_question_match=True,
            sign_behavior_match=True,
            non_style_only=False,
        )
        result = self.alignment.evaluate(ev)
        assert result.verdict == "drifted"
        assert result.reason_code == "mechanism_drifted"
        assert result.severity == "fatal"

    def test_drifted_thesis_mismatch(self):
        """thesis_match False -> drifted."""
        ev = AlignmentEvidence(
            thesis_match=False,
            route_question_match=True,
            sign_behavior_match=True,
            non_style_only=True,
        )
        result = self.alignment.evaluate(ev)
        assert result.verdict == "drifted"

    def test_drifted_route_mismatch(self):
        """route_question_match False -> drifted."""
        ev = AlignmentEvidence(
            thesis_match=True,
            route_question_match=False,
            sign_behavior_match=True,
            non_style_only=True,
        )
        result = self.alignment.evaluate(ev)
        assert result.verdict == "drifted"

    def test_unclear_two_pass(self):
        """Both thesis and route match but sign mismatches -> still aligned (3/4).
        Need exactly 2 pass: thesis+route ok, sign+style fail impossible because
        style fail -> drifted. So: thesis+sign pass, route fail -> drifted.
        Actually: the only way to get 'unclear' is thesis+route ok, sign=False, style=True
        -> that's 3 pass -> aligned. Unclear needs thesis+route pass AND exactly 2 total.
        But thesis+route are required for non-drifted. So unclear can only happen
        if thesis+route pass but sign=False -> 3 pass. Actually unclear is impossible
        in the current implementation if thesis+route are both true.
        Let me re-check: if all 4 checks are considered and only 2 pass total
        AND thesis + route pass -> that's only 2 checks, but thesis + route = 2.
        So sign=false, style=true -> 3 pass. style=false -> drifted first.
        The only way to reach unclear is if thesis=True, route=True, sign=False, style=True
        -> 3 pass -> aligned. Or thesis=False -> drifted.
        Actually unclear is reachable only through an unusual path. Let me construct one:
        thesis=True, route=True, sign=False, style=True -> 3 pass -> aligned.
        The code returns 'unclear' when passed < 3 after the drifted checks pass.
        Since drifted is checked when thesis=False OR route=False OR style=False,
        and we need both thesis=True and route=True and style=True to pass those checks,
        that means sign=False gives us 3 pass -> still >= 3 -> aligned.
        So 'unclear' is actually NOT reachable with the current gate structure.
        That's fine -- it's a safety net. Let me test the edge directly.
        """
        # This should return aligned because 3/4 pass after gates
        ev = AlignmentEvidence(
            thesis_match=True,
            route_question_match=True,
            sign_behavior_match=False,
            non_style_only=True,
        )
        result = self.alignment.evaluate(ev)
        # With thesis+route+style passing and sign failing, that's 3/4 -> aligned
        assert result.verdict == "aligned"
        assert result.checks_passed == 3

    def test_to_dict(self):
        """Result serializes correctly."""
        ev = AlignmentEvidence(
            thesis_match=True,
            route_question_match=True,
            sign_behavior_match=True,
            non_style_only=True,
        )
        result = self.alignment.evaluate(ev)
        d = result.to_dict()
        assert d["verdict"] == "aligned"
        assert d["checks_passed"] == 4
        assert "thesis_match" in d["detail"]
