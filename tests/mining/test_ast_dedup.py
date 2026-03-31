"""Tests for compute_structural_similarity (AST structural dedup)."""

import pytest

from mining.evaluator import compute_structural_similarity


class TestStructuralSimilarity:
    def test_identical_ops(self):
        c1 = "return ops.cs_rank(ops.std(df['close'], 20))"
        c2 = "return ops.cs_rank(ops.std(df['high'], 10))"
        sim = compute_structural_similarity(c1, c2)
        assert sim == 1.0  # Same ops: {cs_rank, std}

    def test_different_ops(self):
        c1 = "return ops.cs_rank(ops.std(df['close'], 20))"
        c2 = "return ops.hhi(df['volume'], 10)"
        sim = compute_structural_similarity(c1, c2)
        assert sim == 0.0  # No overlap

    def test_partial_overlap(self):
        c1 = "return ops.cs_rank(ops.std(df['close'], 20))"
        c2 = "return ops.cs_rank(ops.hhi(df['volume'], 10))"
        sim = compute_structural_similarity(c1, c2)
        assert 0.0 < sim < 1.0  # Partial overlap: {cs_rank}

    def test_no_ops(self):
        c1 = "return df['close'].pct_change(5)"
        c2 = "return df['volume'].rolling(10).mean()"
        sim = compute_structural_similarity(c1, c2)
        assert sim == 0.0

    def test_one_with_ops_one_without(self):
        c1 = "return ops.std(df['close'], 20)"
        c2 = "return df['close'].pct_change(5)"
        sim = compute_structural_similarity(c1, c2)
        assert sim == 0.0
