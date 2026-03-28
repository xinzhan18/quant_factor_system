"""Tests for EvolutionEngine."""

from __future__ import annotations

import pytest
from mining.config import MiningConfig
from mining.evolution import EvolutionEngine


@pytest.fixture
def engine(config):
    return EvolutionEngine(config)


# ---------------------------------------------------------------------------
# suggest_mode
# ---------------------------------------------------------------------------


class TestSuggestMode:
    def test_small_library_favors_genesis(self, engine):
        ratios = engine.suggest_mode(10)
        assert ratios["genesis"] > ratios["mutate"] > ratios["crossover"]

    def test_medium_library_balanced(self, engine):
        ratios = engine.suggest_mode(45)
        assert ratios["genesis"] == ratios["mutate"]

    def test_large_library_favors_mutation(self, engine):
        ratios = engine.suggest_mode(80)
        assert ratios["mutate"] > ratios["genesis"]

    def test_ratios_sum_to_one_small(self, engine):
        ratios = engine.suggest_mode(5)
        assert abs(sum(ratios.values()) - 1.0) < 1e-9

    def test_ratios_sum_to_one_medium(self, engine):
        ratios = engine.suggest_mode(45)
        assert abs(sum(ratios.values()) - 1.0) < 1e-9

    def test_ratios_sum_to_one_large(self, engine):
        ratios = engine.suggest_mode(100)
        assert abs(sum(ratios.values()) - 1.0) < 1e-9

    def test_boundary_at_30_is_medium(self, engine):
        """Library size exactly 30 should return medium ratios."""
        ratios = engine.suggest_mode(30)
        assert ratios["genesis"] == 0.4
        assert ratios["mutate"] == 0.4

    def test_boundary_at_60_is_medium(self, engine):
        """Library size exactly 60 should still return medium ratios."""
        ratios = engine.suggest_mode(60)
        assert ratios["genesis"] == 0.4
        assert ratios["mutate"] == 0.4

    def test_boundary_at_61_is_large(self, engine):
        """Library size 61 should return large ratios."""
        ratios = engine.suggest_mode(61)
        assert ratios["genesis"] == 0.2
        assert ratios["mutate"] == 0.5


# ---------------------------------------------------------------------------
# select_mutation_target
# ---------------------------------------------------------------------------


def _make_factor(fid, name, ic_mean=0.05, category="momentum"):
    return {"id": fid, "name": name, "ic_mean": ic_mean, "category": category}


class TestSelectMutationTarget:
    def test_select_target_returns_a_factor(self, engine):
        factors = [
            _make_factor("001", "f1", ic_mean=0.05),
            _make_factor("002", "f2", ic_mean=0.04),
        ]
        result = engine.select_mutation_target(factors, lineage={})
        assert result is not None
        assert result in factors

    def test_skip_exhausted_factor(self, engine):
        """Factors with mutation_count >= max_mutations_per_factor must be skipped."""
        max_m = engine._config.max_mutations_per_factor  # default 5
        factors = [
            _make_factor("001", "exhausted", ic_mean=0.05),
            _make_factor("002", "fresh", ic_mean=0.03),
        ]
        lineage = {"001": {"mutation_count": max_m, "success_count": 0}}
        # Run many times to ensure exhausted factor is never picked
        for _ in range(30):
            result = engine.select_mutation_target(factors, lineage)
            assert result is not None
            assert result["id"] != "001", "Exhausted factor should be skipped"

    def test_skip_all_exhausted_returns_none(self, engine):
        """When all factors are exhausted, return None."""
        max_m = engine._config.max_mutations_per_factor
        factors = [_make_factor("001", "f1")]
        lineage = {"001": {"mutation_count": max_m, "success_count": 0}}
        result = engine.select_mutation_target(factors, lineage)
        assert result is None

    def test_empty_factors_returns_none(self, engine):
        result = engine.select_mutation_target([], lineage={})
        assert result is None

    def test_high_ic_factor_selected_more_often(self, engine):
        """High-IC factor should be selected significantly more than low-IC one."""
        factors = [
            _make_factor("001", "strong", ic_mean=0.10),
            _make_factor("002", "weak", ic_mean=0.001),
        ]
        counts = {"001": 0, "002": 0}
        for _ in range(200):
            result = engine.select_mutation_target(factors, lineage={})
            counts[result["id"]] += 1
        # Strong factor should dominate
        assert counts["001"] > counts["002"]

    def test_discount_unsuccessful_mutations(self, engine):
        """Factors with failed mutations (mutation_count>0, success_count=0) should be
        discounted but not excluded (unless they hit the cap)."""
        factors = [
            _make_factor("001", "failed", ic_mean=0.05),
            _make_factor("002", "untried", ic_mean=0.05),
        ]
        lineage = {"001": {"mutation_count": 2, "success_count": 0}}
        counts = {"001": 0, "002": 0}
        for _ in range(200):
            result = engine.select_mutation_target(factors, lineage)
            counts[result["id"]] += 1
        # Both can be selected but "untried" should win more often
        assert counts["002"] > counts["001"]


# ---------------------------------------------------------------------------
# select_crossover_pair
# ---------------------------------------------------------------------------


class TestSelectCrossoverPair:
    def test_returns_two_factors(self, engine):
        factors = [
            _make_factor("001", "f1", category="momentum"),
            _make_factor("002", "f2", category="volatility"),
            _make_factor("003", "f3", category="volume"),
        ]
        pair = engine.select_crossover_pair(factors)
        assert len(pair) == 2

    def test_returns_different_factors(self, engine):
        factors = [
            _make_factor("001", "f1", category="momentum"),
            _make_factor("002", "f2", category="volatility"),
        ]
        pair = engine.select_crossover_pair(factors)
        assert pair[0]["id"] != pair[1]["id"]

    def test_prefers_different_categories(self, engine):
        """When multiple categories exist, the pair should come from different ones."""
        factors = [
            _make_factor("001", "f1", category="momentum"),
            _make_factor("002", "f2", category="volatility"),
            _make_factor("003", "f3", category="momentum"),
        ]
        category_pairs = set()
        for _ in range(50):
            pair = engine.select_crossover_pair(factors)
            cats = tuple(sorted(f["category"] for f in pair))
            category_pairs.add(cats)
        # Should see cross-category pairs
        assert ("momentum", "volatility") in category_pairs

    def test_fallback_single_category(self, engine):
        """If only one category exists, still return two distinct factors."""
        factors = [
            _make_factor("001", "f1", category="momentum"),
            _make_factor("002", "f2", category="momentum"),
        ]
        pair = engine.select_crossover_pair(factors)
        assert len(pair) == 2
        assert pair[0]["id"] != pair[1]["id"]

    def test_fewer_than_two_factors_returns_empty(self, engine):
        result = engine.select_crossover_pair([_make_factor("001", "f1")])
        assert result == []

    def test_empty_factors_returns_empty(self, engine):
        result = engine.select_crossover_pair([])
        assert result == []


# ---------------------------------------------------------------------------
# format_lineage_tree
# ---------------------------------------------------------------------------


class TestFormatLineageTree:
    def test_produces_non_empty_string(self, engine):
        factors = [_make_factor("001", "root_factor")]
        result = engine.format_lineage_tree(factors)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_empty_factors_returns_fallback(self, engine):
        result = engine.format_lineage_tree([])
        assert "(no factors)" in result

    def test_single_factor_contains_name(self, engine):
        factors = [_make_factor("001", "my_factor", ic_mean=0.042)]
        result = engine.format_lineage_tree(factors)
        assert "001" in result
        assert "my_factor" in result

    def test_tree_shows_parent_child_relationship(self, engine):
        """Child factor should be indented under its parent."""
        factors = [
            {"id": "001", "name": "parent_factor", "ic_mean": 0.05, "category": "momentum", "lineage": {"parents": []}},
            {"id": "002", "name": "child_factor", "ic_mean": 0.06, "category": "momentum", "lineage": {"parents": ["001"]}},
        ]
        result = engine.format_lineage_tree(factors)
        lines = result.splitlines()
        # Parent line should come before child line
        parent_line_idx = next(i for i, l in enumerate(lines) if "001" in l)
        child_line_idx = next(i for i, l in enumerate(lines) if "002" in l)
        assert parent_line_idx < child_line_idx
        # Child line should have more leading whitespace than parent
        parent_indent = len(lines[parent_line_idx]) - len(lines[parent_line_idx].lstrip())
        child_indent = len(lines[child_line_idx]) - len(lines[child_line_idx].lstrip())
        assert child_indent > parent_indent

    def test_ic_shown_in_label(self, engine):
        factors = [_make_factor("001", "f1", ic_mean=0.055)]
        result = engine.format_lineage_tree(factors)
        assert "0.055" in result

    def test_multi_root_tree(self, engine):
        """Multiple root factors should all appear at top level (no indent)."""
        factors = [
            _make_factor("001", "root_a"),
            _make_factor("002", "root_b"),
        ]
        result = engine.format_lineage_tree(factors)
        lines = result.splitlines()
        assert len(lines) == 2
        for line in lines:
            assert not line.startswith(" "), f"Expected no indent for root, got: {line!r}"
