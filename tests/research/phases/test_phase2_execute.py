"""End-to-end Phase 2 orchestrator test on the P1.0 golden fixture.

Builds candidates from the fixture inputs, runs the full orchestrator, and
verifies:

- result.yaml has schema v3 with the new field layout
- primary-horizon IC matches expected range
- monotonicity / stability / uniqueness / feasibility / barra / distribution
  fields are populated at their canonical paths
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
    ) -> None:
        train_start, train_end, val_start, val_end = date_range

        cand_series = _align_series_time_index(candidate_mi)
        trad_series = _align_series_time_index(tradable_mi)

        inputs = Phase2Inputs(
            batch_id="batch_test001",
            candidates=[
                CandidateInputs(
                    candidate_id="C001",
                    expression="Corr($close, $volume, 20)",
                    source_type="dsl",
                    factor_series=cand_series,
                    tradable_mask=trad_series,
                ),
            ],
            forward_returns_by_horizon={1: forward_returns, 5: forward_returns},
            primary_horizon=1,
            style_matrix=style_matrix,
            library_signals=library_signals,
            amount_data=amount_data,
            market_cap=market_cap,
            train_range=(train_start, train_end),
            validation_range=(val_start, val_end),
            preprocess_config=PreprocessConfig(),
        )

        out_path = tmp_path / "result.yaml"
        result = run_phase2(inputs, out_path)

        # --- file written and re-readable ---
        assert out_path.exists()
        with open(out_path) as f:
            loaded = yaml.unsafe_load(f)

        # --- header ---
        assert loaded["batch_id"] == "batch_test001"
        assert loaded["universe"] == "csi1000"
        assert "schema_version" not in loaded
        assert "sample_policy_version" not in loaded
        assert "preprocess_version" not in loaded
        assert loaded["horizons"] == [1, 5]
        assert loaded["primary_horizon"] == 1
        assert loaded["n_candidates"] == 1
        assert loaded["n_ok"] == 1
        assert loaded["n_errors"] == 0
        assert len(loaded["candidates"]) == 1

        c = loaded["candidates"][0]
        assert c["candidate_id"] == "C001"
        assert c["compute_error"] is None
        assert c["expression_depth"] == 1
        assert c["multiple_testing_risk_bucket"] is None
        assert c["coverage"] > 0.5
        assert c["sign"] in (-1, 1)

        # --- Schema v3 canonical blocks (no report_card, no effect_strength) ---
        assert "report_card" not in c
        assert "effect_strength" not in c
        assert "redundancy" not in c
        assert "long_short_stats" not in c
        assert set(c.keys()) >= {
            "ic",
            "quintile",
            "stability",
            "uniqueness",
            "feasibility",
            "barra",
            "distribution",
        }

        # --- IC block ---
        ic = c["ic"]
        assert ic["train"]["n_days"] > 0
        assert ic["validation"]["n_days"] > 0
        assert ic["validation"]["ic_mean"] > 0.05, (
            f"expected strong positive IC on validation, got {ic['validation']}"
        )
        assert ic["validation"]["ic_ir"] > 0.5
        assert ic["sign_consistent"] is True
        assert isinstance(ic["by_year"], dict) and len(ic["by_year"]) > 0
        assert ic["autocorr_lag1"] is not None
        assert ic["best_quarter"] >= ic["worst_quarter"]
        assert set(ic["by_horizon"].keys()) == {1, 5}
        for h in (1, 5):
            assert "train" in ic["by_horizon"][h]
            assert "validation" in ic["by_horizon"][h]
            # Serialized form drops the raw pd.Series carriers
            assert "ic_series_train" not in ic["by_horizon"][h]

        # --- Quintile block ---
        qval = c["quintile"]["validation"]
        assert qval["monotonicity"] > 0.9
        assert qval["n_days"] > 0
        for k in ("q1", "q2", "q3", "q4", "q5"):
            assert k in qval
        ls = c["quintile"]["ls_stats"]["validation"]
        assert "sharpe" in ls and "max_dd" in ls and "tstat" in ls

        # --- Stability ---
        split = c["stability"]["split_stability"]
        assert "bucket" not in split
        assert split["sign_consistency"] is not None
        assert split["dispersion"] is not None
        assert split["n_splits"] > 0

        # --- Uniqueness (candidate === F001 → corr ≈ 1) ---
        uq = c["uniqueness"]
        assert uq["max_lib_corr"] >= 0.99
        assert uq["nearest_factor_id"] == "F001"
        assert "incremental_ic" in uq

        # --- Feasibility ---
        feas = c["feasibility"]
        assert "signal_half_life" in feas
        assert "signal_autocorr_lag1" in feas
        assert "holding_period" not in feas
        assert isinstance(feas["rebalance_stress"], float)

        # --- Barra ---
        assert c["barra"]["style_r_squared"] is not None

        # --- Distribution ---
        dist = c["distribution"]
        assert set(dist.keys()) == {"zero_ratio", "skew", "kurt", "extreme_ratio"}

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
            forward_returns_by_horizon={1: forward_returns},
            primary_horizon=1,
            style_matrix=style_matrix,
            library_signals=library_signals,
            amount_data=amount_data,
            market_cap=market_cap,
            train_range=(train_start, train_end),
            validation_range=(val_start, val_end),
        )

        out_path = tmp_path / "result.yaml"
        result = run_phase2(inputs, out_path)

        assert result["n_candidates"] == 2
        assert result["n_ok"] == 1
        assert result["n_errors"] == 1

        by_id = {c["candidate_id"]: c for c in result["candidates"]}
        assert by_id["C001"]["compute_error"] is None
        assert by_id["C002"]["compute_error"] is not None
        # Broken candidate has no metric fields populated
        assert "ic" not in by_id["C002"]
        assert "quintile" not in by_id["C002"]

    def test_diagnostics_parquet_written_when_paths_provided(
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
        from research.storage.paths import StoragePaths

        train_start, train_end, val_start, val_end = date_range
        cand_series = _align_series_time_index(candidate_mi)
        trad_series = _align_series_time_index(tradable_mi)

        paths = StoragePaths(tmp_path)
        paths.ensure_dirs()

        inputs = Phase2Inputs(
            batch_id="batch_diag001",
            candidates=[
                CandidateInputs(
                    candidate_id="C001",
                    expression="good",
                    source_type="dsl",
                    factor_series=cand_series,
                    tradable_mask=trad_series,
                ),
            ],
            forward_returns_by_horizon={1: forward_returns},
            primary_horizon=1,
            style_matrix=style_matrix,
            library_signals=library_signals,
            amount_data=amount_data,
            market_cap=market_cap,
            train_range=(train_start, train_end),
            validation_range=(val_start, val_end),
            paths=paths,
        )

        out_path = tmp_path / "result.yaml"
        result = run_phase2(inputs, out_path)

        c = result["candidates"][0]
        assert c["diagnostics_relpath"] is not None
        diag_dir = paths.candidate_diagnostics_dir("batch_diag001", "C001")
        assert diag_dir.exists()
        for name in (
            "quantile_daily_train.parquet",
            "quantile_daily_validation.parquet",
            "long_short_daily.parquet",
            "ic_daily.parquet",
            "coverage_daily.parquet",
            "factor_hist.parquet",
        ):
            assert (diag_dir / name).exists(), f"missing {name}"

        q_val = pd.read_parquet(diag_dir / "quantile_daily_validation.parquet")
        assert list(q_val.columns) == ["q1", "q2", "q3", "q4", "q5"]
        assert len(q_val) > 0

    def test_persist_diagnostics_writes_coverage_daily(
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
        from research.storage.paths import StoragePaths

        train_start, train_end, val_start, val_end = date_range
        cand_series = _align_series_time_index(candidate_mi)
        trad_series = _align_series_time_index(tradable_mi)

        paths = StoragePaths(tmp_path)
        paths.ensure_dirs()

        inputs = Phase2Inputs(
            batch_id="batch_diag002",
            candidates=[
                CandidateInputs(
                    candidate_id="C001",
                    expression="good",
                    source_type="dsl",
                    factor_series=cand_series,
                    tradable_mask=trad_series,
                ),
            ],
            forward_returns_by_horizon={1: forward_returns},
            primary_horizon=1,
            style_matrix=style_matrix,
            library_signals=library_signals,
            amount_data=amount_data,
            market_cap=market_cap,
            train_range=(train_start, train_end),
            validation_range=(val_start, val_end),
            paths=paths,
        )

        out_path = tmp_path / "result.yaml"
        result = run_phase2(inputs, out_path)

        diag_dir = paths.candidate_diagnostics_dir("batch_diag002", "C001")
        cov = pd.read_parquet(diag_dir / "coverage_daily.parquet")
        assert cov.columns.tolist() == ["coverage"]
        assert cov.index.name == "datetime"
        assert (cov["coverage"] >= 0).all() and (cov["coverage"] <= 1).all()
        assert len(cov) > 0

    def test_persist_diagnostics_writes_factor_hist(
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
        from research.storage.paths import StoragePaths

        train_start, train_end, val_start, val_end = date_range
        cand_series = _align_series_time_index(candidate_mi)
        trad_series = _align_series_time_index(tradable_mi)

        paths = StoragePaths(tmp_path)
        paths.ensure_dirs()

        inputs = Phase2Inputs(
            batch_id="batch_diag003",
            candidates=[
                CandidateInputs(
                    candidate_id="C001",
                    expression="good",
                    source_type="dsl",
                    factor_series=cand_series,
                    tradable_mask=trad_series,
                ),
            ],
            forward_returns_by_horizon={1: forward_returns},
            primary_horizon=1,
            style_matrix=style_matrix,
            library_signals=library_signals,
            amount_data=amount_data,
            market_cap=market_cap,
            train_range=(train_start, train_end),
            validation_range=(val_start, val_end),
            paths=paths,
        )

        out_path = tmp_path / "result.yaml"
        result = run_phase2(inputs, out_path)

        diag_dir = paths.candidate_diagnostics_dir("batch_diag003", "C001")
        hist = pd.read_parquet(diag_dir / "factor_hist.parquet")
        assert set(hist.columns) == {"bin_edge_lo", "bin_edge_hi", "is_freq", "oos_freq"}
        assert len(hist) == 50  # 50 bins
        assert (hist["is_freq"] >= 0).all()
        assert (hist["oos_freq"] >= 0).all()
        assert abs(hist["is_freq"].sum() - 1.0) < 0.01
        assert abs(hist["oos_freq"].sum() - 1.0) < 0.01
        # Edges should be increasing
        assert (hist["bin_edge_hi"] > hist["bin_edge_lo"]).all()
