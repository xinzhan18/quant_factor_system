"""Golden-fixture tests for vectorized_redundancy."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from core.factor_stats import multiindex_to_flat

from research.compute.vectorized_redundancy import (
    compute_incremental_ic,
    compute_pairwise_redundancy,
)

FIXTURES = Path(__file__).parent / "_fixtures"
INPUTS = FIXTURES / "inputs"
OUTPUTS = FIXTURES / "outputs"

ATOL = 1e-6


@pytest.fixture(scope="module")
def candidate_signal() -> pd.DataFrame:
    return pd.read_parquet(INPUTS / "candidate_signal.parquet")


@pytest.fixture(scope="module")
def library_signals() -> dict[str, pd.DataFrame]:
    return {
        "F001": pd.read_parquet(INPUTS / "library_F001.parquet"),
        "F002": pd.read_parquet(INPUTS / "library_F002.parquet"),
        "F003": pd.read_parquet(INPUTS / "library_F003.parquet"),
    }


@pytest.fixture(scope="module")
def golden() -> dict:
    with open(OUTPUTS / "golden.yaml") as f:
        return yaml.safe_load(f)


class TestComputePairwiseRedundancy:
    def test_matches_golden(
        self,
        candidate_signal: pd.DataFrame,
        library_signals: dict[str, pd.DataFrame],
        golden: dict,
    ) -> None:
        result = compute_pairwise_redundancy(
            candidate_signal, library_signals, threshold=0.7
        )
        g = golden["redundancy"]

        assert result["max_lib_corr"] == pytest.approx(
            g["max_lib_corr"], abs=ATOL
        )
        assert result["nearest_factor_id"] == g["nearest_factor_id"]
        assert result["is_near_duplicate"] == g["is_near_duplicate"]
        assert result["exceeds_threshold"] == g["exceeds_threshold"]

        for fid, g_corr in g["all_correlations"].items():
            assert result["all_correlations"][fid] == pytest.approx(
                g_corr, abs=ATOL
            ), f"correlation with {fid} mismatch"

    def test_empty_library(
        self, candidate_signal: pd.DataFrame
    ) -> None:
        result = compute_pairwise_redundancy(candidate_signal, {})
        assert result["max_lib_corr"] == 0.0
        assert result["nearest_factor_id"] is None
        assert result["is_near_duplicate"] is False
        assert result["exceeds_threshold"] is False

    def test_series_input_accepted(
        self,
        candidate_signal: pd.DataFrame,
        library_signals: dict[str, pd.DataFrame],
    ) -> None:
        """Both DataFrame and Series candidate inputs should work."""
        cand_series = candidate_signal.iloc[:, 0]
        result = compute_pairwise_redundancy(cand_series, library_signals)
        # The same candidate as DataFrame must give identical output
        result_df = compute_pairwise_redundancy(
            candidate_signal, library_signals
        )
        assert result["max_lib_corr"] == result_df["max_lib_corr"]
        assert result["nearest_factor_id"] == result_df["nearest_factor_id"]


class TestComputeIncrementalIC:
    def test_returns_none_for_empty_library(
        self, candidate_signal: pd.DataFrame
    ) -> None:
        # Construct a minimal returns frame aligned with candidate
        cand_flat = multiindex_to_flat(candidate_signal)
        ret_flat = cand_flat.copy()
        ret_flat["value"] = 0.001  # trivial constant returns
        assert compute_incremental_ic(cand_flat, ret_flat, {}) is None

    def test_runs_over_library(
        self,
        candidate_signal: pd.DataFrame,
        library_signals: dict[str, pd.DataFrame],
    ) -> None:
        cand_flat = multiindex_to_flat(candidate_signal)
        # Build synthetic forward-returns correlated with the candidate
        ret_flat = cand_flat.copy()
        ret_flat["value"] = cand_flat["value"] * 0.01 + 0.0005
        lib_flat = {
            fid: multiindex_to_flat(df) for fid, df in library_signals.items()
        }
        result = compute_incremental_ic(cand_flat, ret_flat, lib_flat)
        # Returns either None (degenerate) or a finite float
        assert result is None or isinstance(result, float)
