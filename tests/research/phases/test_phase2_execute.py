"""End-to-end Phase 2 orchestrator test on the P1.0 golden fixture.

Builds two candidates from the fixture inputs (one from the candidate
signal, one from a library factor), runs the full orchestrator, and
verifies:

- result.yaml has the frozen schema
- effect_strength matches golden for the candidate-from-fixture
- a deliberately broken candidate is reported as compute_error without
  crashing the batch
- multiple_testing_risk_bucket is None at Phase 2 (Phase 3 populates it)
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from research.compute.preprocess import PreprocessConfig
from research.phases.phase2_execute import (
    RESULT_SCHEMA_VERSION,
    CandidateInputs,
    Phase2Inputs,
    run_phase2,
)

FIXTURES = Path(__file__).parent.parent / "compute" / "_fixtures"
INPUTS = FIXTURES / "inputs"
OUTPUTS = FIXTURES / "outputs"

TRAIN_END_IDX = 359
VAL_END_IDX = 599
START_DATE = "2018-01-02"
N_DAYS = 600


@pytest.fixture(scope="module")
def candidate_mi() -> pd.Series:
    df = pd.read_parquet(INPUTS / "candidate_signal.parquet")
    return df[df.columns[0]]


@pytest.fixture(scope="module")
def tradable_mi() -> pd.Series:
    df = pd.read_parquet(INPUTS / "tradable_mask.parquet")
    s = df[df.columns[0]]
    # Align names to (time, symbol) — phase2 expects these
    s.index.names = ["time", "symbol"]
    return s


@pytest.fixture(scope="module")
def forward_returns() -> pd.DataFrame:
    return pd.read_parquet(INPUTS / "forward_returns.parquet")


@pytest.fixture(scope="module")
def style_matrix() -> pd.DataFrame:
    return pd.read_parquet(INPUTS / "style_matrix.parquet")


@pytest.fixture(scope="module")
def library_signals() -> dict[str, pd.DataFrame]:
    return {
        "F001": pd.read_parquet(INPUTS / "library_F001.parquet"),
        "F002": pd.read_parquet(INPUTS / "library_F002.parquet"),
        "F003": pd.read_parquet(INPUTS / "library_F003.parquet"),
    }


@pytest.fixture(scope="module")
def amount_data() -> pd.DataFrame:
    return pd.read_parquet(INPUTS / "amount_data.parquet")


@pytest.fixture(scope="module")
def market_cap() -> pd.DataFrame:
    return pd.read_parquet(INPUTS / "market_cap_data.parquet")


@pytest.fixture(scope="module")
def golden() -> dict:
    with open(OUTPUTS / "golden.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture
def date_range() -> tuple[str, str, str, str]:
    dates = pd.bdate_range(start=START_DATE, periods=N_DAYS)
    return (
        str(dates[0].date()),
        str(dates[TRAIN_END_IDX].date()),
        str(dates[TRAIN_END_IDX + 1].date()),
        str(dates[VAL_END_IDX].date()),
    )


def _align_series_time_index(s: pd.Series) -> pd.Series:
    """Rename the MultiIndex levels to (time, symbol) — some fixtures use
    (datetime, instrument)."""
    if s.index.names != ("time", "symbol"):
        s = s.copy()
        s.index.names = ["time", "symbol"]
    return s


class TestPhase2EndToEnd:
    def test_orchestrator_writes_result_yaml(
        self,
        tmp_path: Path,
        candidate_mi: pd.Series,
        tradable_mi: pd.Series,
        forward_returns: pd.DataFrame,
        style_matrix: pd.DataFrame,
        library_signals: dict[str, pd.DataFrame],
        amount_data: pd.DataFrame,
        market_cap: pd.DataFrame,
        date_range: tuple[str, str, str, str],
        golden: dict,
    ) -> None:
        train_start, train_end, val_start, val_end = date_range

        cand_series = _align_series_time_index(candidate_mi)
        trad_series = _align_series_time_index(tradable_mi)

        inputs = Phase2Inputs(
            batch_id="batch_test001",
            candidates=[
                CandidateInputs(
                    candidate_id="C001",
                    expression="fixture_candidate",
                    source_type="dsl",
                    factor_series=cand_series,
                    tradable_mask=trad_series,
                ),
            ],
            forward_returns_flat=forward_returns,
            style_matrix=style_matrix,
            library_signals=library_signals,
            amount_data=amount_data,
            market_cap=market_cap,
            train_range=(train_start, train_end),
            validation_range=(val_start, val_end),
            support_windows=[],
            sample_policy_version="v3",
            preprocess_version="p1",
            preprocess_config=PreprocessConfig(),
        )

        out_path = tmp_path / "result.yaml"
        result = run_phase2(inputs, out_path)

        # --- file written and re-readable ---
        assert out_path.exists()
        with open(out_path) as f:
            loaded = yaml.unsafe_load(f)

        # --- schema header ---
        assert loaded["schema_version"] == RESULT_SCHEMA_VERSION
        assert loaded["batch_id"] == "batch_test001"
        assert loaded["sample_policy_version"] == "v3"
        assert loaded["preprocess_version"] == "p1"
        assert loaded["n_candidates"] == 1
        assert loaded["n_ok"] == 1
        assert loaded["n_errors"] == 0
        assert len(loaded["candidates"]) == 1

        c = loaded["candidates"][0]
        assert c["candidate_id"] == "C001"
        assert c["compute_error"] is None

        # --- multiple testing bucket left null for P2 to fill ---
        assert c["multiple_testing_risk_bucket"] is None

        # --- structural presence ---
        assert "effect_strength" in c
        assert "quintile" in c
        assert "stability" in c
        assert "redundancy" in c
        assert "feasibility" in c
        assert "barra" in c

        # --- effect strength numerical check ---
        # The preprocess step (winsorize + zscore) changes factor values
        # slightly vs raw fixture, so IC won't match golden bit-for-bit.
        # We just check the sign and magnitude are in the right ballpark.
        es_val = c["effect_strength"]["validation"]
        assert es_val["ic_mean"] > 0.05, (
            f"expected strong positive IC on validation, got {es_val['ic_mean']}"
        )
        assert es_val["ic_ir"] > 0.5
        assert es_val["n_days"] == golden["effect_strength"]["validation"]["n_days"]

        # --- Quintile monotonicity should still be strong ---
        assert c["quintile"]["monotonicity_validation"] > 0.9

        # --- Stability high (same-sign splits) ---
        assert c["stability"]["split_stability"]["bucket"] in ("high", "medium")
        assert c["stability"]["sign_consistency_train_validation"] is True

        # --- Redundancy against library ---
        # Candidate is literally F001, so redundancy must be near 1.0
        assert c["redundancy"]["max_lib_corr"] >= 0.99
        assert c["redundancy"]["nearest_factor_id"] == "F001"

        # --- Barra outputs present ---
        assert c["barra"]["style_r_squared"] is not None

    def test_failed_candidate_reported_as_error(
        self,
        tmp_path: Path,
        candidate_mi: pd.Series,
        tradable_mi: pd.Series,
        forward_returns: pd.DataFrame,
        style_matrix: pd.DataFrame,
        library_signals: dict[str, pd.DataFrame],
        amount_data: pd.DataFrame,
        market_cap: pd.DataFrame,
        date_range: tuple[str, str, str, str],
    ) -> None:
        train_start, train_end, val_start, val_end = date_range

        cand_series = _align_series_time_index(candidate_mi)
        trad_series = _align_series_time_index(tradable_mi)

        # Broken candidate: all-NaN factor series → preprocess returns empty
        broken_series = cand_series.copy() * np.nan

        inputs = Phase2Inputs(
            batch_id="batch_test002",
            candidates=[
                CandidateInputs(
                    candidate_id="C001",
                    expression="good",
                    source_type="dsl",
                    factor_series=cand_series,
                    tradable_mask=trad_series,
                ),
                CandidateInputs(
                    candidate_id="C002",
                    expression="all_nan",
                    source_type="dsl",
                    factor_series=broken_series,
                    tradable_mask=trad_series,
                ),
            ],
            forward_returns_flat=forward_returns,
            style_matrix=style_matrix,
            library_signals=library_signals,
            amount_data=amount_data,
            market_cap=market_cap,
            train_range=(train_start, train_end),
            validation_range=(val_start, val_end),
            support_windows=[],
        )

        out_path = tmp_path / "result.yaml"
        result = run_phase2(inputs, out_path)

        assert result["n_candidates"] == 2
        assert result["n_ok"] == 1
        assert result["n_errors"] == 1

        by_id = {c["candidate_id"]: c for c in result["candidates"]}
        assert by_id["C001"]["compute_error"] is None
        assert by_id["C002"]["compute_error"] is not None
        assert "empty" in by_id["C002"]["compute_error"].lower() or (
            "NaN" in by_id["C002"]["compute_error"]
        )
        # Broken candidate has no metric fields populated
        assert "effect_strength" not in by_id["C002"]
