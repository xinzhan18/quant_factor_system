"""Golden-fixture tests for vectorized_redundancy."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from research.compute.vectorized_redundancy import (
    batch_dedup,
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


class TestBatchDedup:
    def test_detects_self_duplicate(
        self,
        candidate_signal: pd.DataFrame,
        library_signals: dict[str, pd.DataFrame],
    ) -> None:
        # Candidate and library_F001 are identical in the fixture
        # (F001 is a copy of the candidate)
        candidates = {
            "C001": candidate_signal,
            "C002": library_signals["F001"],
        }
        pairs = batch_dedup(candidates, threshold=0.9)
        assert len(pairs) == 1
        id_a, id_b, corr = pairs[0]
        assert {id_a, id_b} == {"C001", "C002"}
        assert corr >= 0.99

    def test_no_duplicates_below_threshold(
        self,
        library_signals: dict[str, pd.DataFrame],
    ) -> None:
        # F001 / F002 / F003 have correlations 1.0 / 0.56 / 0.005 with
        # the candidate, but pairwise with each other they should be
        # mostly independent. Threshold 0.9 → only F001↔F001 duplicates.
        candidates = {
            "CA": library_signals["F002"],
            "CB": library_signals["F003"],
        }
        pairs = batch_dedup(candidates, threshold=0.9)
        assert pairs == []
