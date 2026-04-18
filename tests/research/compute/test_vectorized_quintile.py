"""Golden-fixture tests for vectorized_quintile."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from research.compute.vectorized_quintile import (
    compute_long_short_stats,
    compute_quintile_returns,
)

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


class TestLongShortStats:
    def test_empty_returns_empty_dict(self) -> None:
        assert compute_long_short_stats([]) == {}

    def test_normal_series(self) -> None:
        daily = [0.001, -0.0005, 0.002, 0.0, -0.001, 0.0015]
        out = compute_long_short_stats(daily)
        expected_keys = {
            "mean", "std", "sharpe", "sortino", "calmar",
            "max_dd", "max_dd_duration", "tstat", "n_days",
        }
        assert set(out.keys()) == expected_keys
        assert out["n_days"] == 6
        assert out["mean"] == pytest.approx(float(np.mean(daily)), abs=1e-6)

    def test_nan_filtered(self) -> None:
        daily = [0.001, float("nan"), 0.002]
        out = compute_long_short_stats(daily)
        assert out["n_days"] == 2

    def test_zero_std(self) -> None:
        out = compute_long_short_stats([0.001, 0.001, 0.001])
        assert out["tstat"] == 0.0
