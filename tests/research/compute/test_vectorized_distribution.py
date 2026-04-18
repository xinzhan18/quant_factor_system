"""Tests for vectorized_distribution.

Covers the happy path, sparse input, and verification that skew / kurt
match ``core.factor_stats.distribution_stats`` (the shared source).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from core.factor_stats import distribution_stats, multiindex_to_flat

from research.compute.vectorized_distribution import compute_distribution

FIXTURES = Path(__file__).parent / "_fixtures"
INPUTS = FIXTURES / "inputs"


@pytest.fixture(scope="module")
def candidate_mi() -> pd.DataFrame:
    df = pd.read_parquet(INPUTS / "candidate_signal.parquet")
    return df


class TestComputeDistribution:
    def test_matches_core_distribution_stats(
        self, candidate_mi: pd.DataFrame
    ) -> None:
        out = compute_distribution(candidate_mi)
        flat = multiindex_to_flat(candidate_mi)
        expected = distribution_stats(flat)
        assert out["skew"] == pytest.approx(expected["skew"], abs=1e-6)
        assert out["kurt"] == pytest.approx(expected["kurtosis"], abs=1e-6)

    def test_shape(self, candidate_mi: pd.DataFrame) -> None:
        out = compute_distribution(candidate_mi)
        assert set(out.keys()) == {"zero_ratio", "skew", "kurt", "extreme_ratio"}
        assert 0.0 <= out["zero_ratio"] <= 1.0
        assert 0.0 <= out["extreme_ratio"] <= 1.0

    def test_all_zeros(self) -> None:
        idx = pd.MultiIndex.from_product(
            [pd.date_range("2024-01-02", periods=30), list(range(20))],
            names=["datetime", "instrument"],
        )
        df = pd.DataFrame({"value": np.zeros(len(idx))}, index=idx)
        out = compute_distribution(df)
        assert out["zero_ratio"] == 1.0
        assert out["extreme_ratio"] == 0.0

    def test_sparse_input_returns_none(self) -> None:
        idx = pd.MultiIndex.from_tuples(
            [(pd.Timestamp("2024-01-02"), i) for i in range(3)],
            names=["datetime", "instrument"],
        )
        df = pd.DataFrame({"value": [1.0, 2.0, 3.0]}, index=idx)
        out = compute_distribution(df)
        assert out["skew"] is None
        assert out["kurt"] is None
