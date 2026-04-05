"""Tests for ReplaceProtocol -- 5-dimension discrete comparison."""
import pytest

from research.judge.replace_protocol import (
    DiscreteComparison,
    HardConditions,
    ReplaceProtocol,
    ReplaceResult,
)


class TestHardConditions:
    def setup_method(self):
        self.protocol = ReplaceProtocol()

    def test_low_similarity_blocks(self):
        """Fails hard gate if similarity is low."""
        hard = HardConditions(high_similarity=False, no_sign_flip=True, residual_ic_not_worse=True)
        comp = DiscreteComparison()
        result = self.protocol.evaluate(hard, comp)
        assert result.decision == "no_replace"
        assert not result.hard_conditions_passed
        assert result.hard_failure_reason == "low_similarity"

    def test_sign_flip_blocks(self):
        """Fails hard gate if sign flip detected."""
        hard = HardConditions(high_similarity=True, no_sign_flip=False, residual_ic_not_worse=True)
        comp = DiscreteComparison()
        result = self.protocol.evaluate(hard, comp)
        assert result.decision == "no_replace"
        assert not result.hard_conditions_passed
        assert result.hard_failure_reason == "sign_flip_detected"

    def test_residual_ic_regression_blocks(self):
        """Fails hard gate if residual IC is worse."""
        hard = HardConditions(high_similarity=True, no_sign_flip=True, residual_ic_not_worse=False)
        comp = DiscreteComparison()
        result = self.protocol.evaluate(hard, comp)
        assert result.decision == "no_replace"
        assert result.hard_failure_reason == "residual_ic_regression"


class TestDiscreteComparison:
    def setup_method(self):
        self.protocol = ReplaceProtocol()
        self.hard_ok = HardConditions(high_similarity=True, no_sign_flip=True, residual_ic_not_worse=True)

    def test_replace_two_main_better(self):
        """Replace when 2 main dimensions are better, no worse."""
        comp = DiscreteComparison(
            stability_compare="better",
            redundancy_compare="better",
            mechanism_cleanliness_compare="similar",
        )
        result = self.protocol.evaluate(self.hard_ok, comp)
        assert result.decision == "replace"
        assert result.hard_conditions_passed
        assert result.main_better_count == 2

    def test_replace_three_main_better(self):
        """Replace when all 3 main dimensions are better."""
        comp = DiscreteComparison(
            stability_compare="better",
            redundancy_compare="better",
            mechanism_cleanliness_compare="better",
        )
        result = self.protocol.evaluate(self.hard_ok, comp)
        assert result.decision == "replace"
        assert result.main_better_count == 3

    def test_no_replace_main_worse(self):
        """No replace when any main dimension is worse."""
        comp = DiscreteComparison(
            stability_compare="better",
            redundancy_compare="worse",
            mechanism_cleanliness_compare="better",
        )
        result = self.protocol.evaluate(self.hard_ok, comp)
        assert result.decision == "no_replace"
        assert result.main_worse_count == 1

    def test_no_replace_materially_worse_aux(self):
        """No replace when auxiliary is materially worse."""
        comp = DiscreteComparison(
            stability_compare="better",
            redundancy_compare="better",
            mechanism_cleanliness_compare="similar",
            feasibility_materially_worse=True,
        )
        result = self.protocol.evaluate(self.hard_ok, comp)
        assert result.decision == "no_replace"
        assert result.has_materially_worse_aux

    def test_reserve_one_main_better(self):
        """Reserve when only 1 main dimension is better."""
        comp = DiscreteComparison(
            stability_compare="better",
            redundancy_compare="similar",
            mechanism_cleanliness_compare="similar",
        )
        result = self.protocol.evaluate(self.hard_ok, comp)
        assert result.decision == "reserve_for_review"
        assert result.main_better_count == 1

    def test_reserve_all_similar_with_aux_improvement(self):
        """Reserve when all main similar but aux has improvement."""
        comp = DiscreteComparison(
            stability_compare="similar",
            redundancy_compare="similar",
            mechanism_cleanliness_compare="similar",
            statistical_strength_compare="better",
        )
        result = self.protocol.evaluate(self.hard_ok, comp)
        assert result.decision == "reserve_for_review"

    def test_no_replace_all_similar_no_aux_improvement(self):
        """No replace when all dimensions are similar."""
        comp = DiscreteComparison()  # all default to similar
        result = self.protocol.evaluate(self.hard_ok, comp)
        assert result.decision == "no_replace"

    def test_invalid_comparison_value(self):
        """Raises ValueError for invalid comparison string."""
        with pytest.raises(ValueError, match="must be one of"):
            DiscreteComparison(stability_compare="excellent")

    def test_to_dict(self):
        """Result serializes correctly."""
        comp = DiscreteComparison(
            stability_compare="better",
            redundancy_compare="better",
            mechanism_cleanliness_compare="similar",
        )
        result = self.protocol.evaluate(self.hard_ok, comp)
        d = result.to_dict()
        assert d["decision"] == "replace"
        assert d["hard_conditions_passed"] is True
        assert isinstance(d["reason_codes"], list)
