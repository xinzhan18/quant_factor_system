"""Golden-fixture tests for vectorized_quintile."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from research.compute.vectorized_quintile import compute_quintile_returns

FIXTURES = Path(__file__).parent / "_fixtures"
INPUTS = FIXTURES / "inputs"
OUTPUTS = FIXTURES / "outputs"

TRAIN_END_IDX = 359
VAL_END_IDX = 599
START_DATE = "2018-01-02"
N_DAYS = 600

ATOL = 1e-10


@pytest.fixture(scope="module")
def factor_flat() -> pd.DataFrame:
    return pd.read_parquet(INPUTS / "factor_values.parquet")


@pytest.fixture(scope="module")
def returns_flat() -> pd.DataFrame:
    return pd.read_parquet(INPUTS / "forward_returns.parquet")


@pytest.fixture(scope="module")
def golden() -> dict:
    with open(OUTPUTS / "golden.yaml") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def val_slice(
    factor_flat: pd.DataFrame, returns_flat: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    dates = pd.bdate_range(start=START_DATE, periods=N_DAYS)
    val_start, val_end = dates[TRAIN_END_IDX + 1], dates[VAL_END_IDX]
    fv = factor_flat[
        (factor_flat["time"] >= val_start) & (factor_flat["time"] <= val_end)
    ]
    fr = returns_flat[
        (returns_flat["time"] >= val_start) & (returns_flat["time"] <= val_end)
    ]
    return fv, fr


class TestQuintileReturns:
    def test_quintile_buckets_match_golden(
        self,
        val_slice: tuple[pd.DataFrame, pd.DataFrame],
        golden: dict,
    ) -> None:
        fv, fr = val_slice
        result = compute_quintile_returns(fv, fr, n_quantiles=5, min_obs=30)

        g_q = golden["effect_strength"]["quintile_returns_validation"]
        for k in ("q1", "q2", "q3", "q4", "q5"):
            assert result["quintile_returns"][k] == pytest.approx(
                g_q[k], abs=ATOL
            ), f"{k} mismatch"

    def test_monotonicity_matches_golden(
        self,
        val_slice: tuple[pd.DataFrame, pd.DataFrame],
        golden: dict,
    ) -> None:
        fv, fr = val_slice
        result = compute_quintile_returns(fv, fr, n_quantiles=5, min_obs=30)
        assert result["monotonicity"] == pytest.approx(
            golden["effect_strength"]["monotonicity_validation"], abs=ATOL
        )

    def test_long_short_matches_golden(
        self,
        val_slice: tuple[pd.DataFrame, pd.DataFrame],
        golden: dict,
    ) -> None:
        fv, fr = val_slice
        result = compute_quintile_returns(fv, fr, n_quantiles=5, min_obs=30)
        g_es = golden["effect_strength"]
        assert result["long_short_n_days"] == g_es["long_short_n_days"]
        assert result["long_short_mean"] == pytest.approx(
            g_es["long_short_mean_validation"], abs=ATOL
        )

    def test_long_short_daily_matches_parquet(
        self,
        val_slice: tuple[pd.DataFrame, pd.DataFrame],
    ) -> None:
        fv, fr = val_slice
        result = compute_quintile_returns(fv, fr, n_quantiles=5, min_obs=30)
        golden_ls = pd.read_parquet(
            OUTPUTS / "long_short_daily_validation.parquet"
        )["ls"]
        np.testing.assert_array_almost_equal(
            np.array(result["long_short_daily"]),
            golden_ls.values,
            decimal=10,
        )
