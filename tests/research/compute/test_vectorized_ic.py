"""Golden-fixture equivalence tests for vectorized_ic.

Loads the P1.0 fixture inputs, runs the new ``research.compute.vectorized_ic``
API, and asserts the results match the pre-computed golden values (generated
by the OLD code path in ``tests/research/compute/_fixtures/generate_golden.py``)
within 1e-6 absolute tolerance.

If any assertion here fails, EITHER the new implementation has a bug OR
``generate_golden.py`` was regenerated with different inputs — in that
case re-run the fixture generator first and inspect the diff.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
import yaml

from research.compute.vectorized_ic import (
    compute_effect_strength,
    compute_ic_analytics,
    compute_ic_half_life,
    compute_ic_series,
    compute_ic_stats,
    compute_multi_horizon_ic,
)

FIXTURES = Path(__file__).parent / "_fixtures"
INPUTS = FIXTURES / "inputs"
OUTPUTS = FIXTURES / "outputs"

# From generate_golden.py — keep in sync if the generator constants change
TRAIN_END_IDX = 359
VAL_END_IDX = 599
START_DATE = "2018-01-02"
N_DAYS = 600

# Tolerance: golden yaml stores float64 with full precision; new code should
# match bit-for-bit on IC mean/std because the math is identical (both call
# core.factor_stats.daily_cross_sectional_ic). We use 1e-10 to catch any
# accidental algorithm drift while allowing for YAML serialization rounding.
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
def date_range() -> tuple[str, str, str, str]:
    """Return (train_start, train_end, val_start, val_end) as date strings."""
    dates = pd.bdate_range(start=START_DATE, periods=N_DAYS)
    train_start = str(dates[0].date())
    train_end = str(dates[TRAIN_END_IDX].date())
    val_start = str(dates[TRAIN_END_IDX + 1].date())
    val_end = str(dates[VAL_END_IDX].date())
    return train_start, train_end, val_start, val_end


class TestComputeIcSeries:
    def test_validation_slice_matches_golden(
        self,
        factor_flat: pd.DataFrame,
        returns_flat: pd.DataFrame,
        date_range: tuple[str, str, str, str],
    ) -> None:
        _, _, val_start, val_end = date_range
        mask_fv = (factor_flat["time"] >= pd.Timestamp(val_start)) & (
            factor_flat["time"] <= pd.Timestamp(val_end)
        )
        mask_fr = (returns_flat["time"] >= pd.Timestamp(val_start)) & (
            returns_flat["time"] <= pd.Timestamp(val_end)
        )

        ic = compute_ic_series(
            factor_flat[mask_fv], returns_flat[mask_fr], min_obs=30
        )

        golden_ic = pd.read_parquet(OUTPUTS / "ic_series_validation.parquet")["ic"]
        pd.testing.assert_series_equal(
            ic.rename("ic").sort_index(),
            golden_ic.sort_index(),
            atol=ATOL,
            check_names=False,
        )

    def test_train_slice_matches_golden(
        self,
        factor_flat: pd.DataFrame,
        returns_flat: pd.DataFrame,
        date_range: tuple[str, str, str, str],
    ) -> None:
        train_start, train_end, _, _ = date_range
        mask_fv = (factor_flat["time"] >= pd.Timestamp(train_start)) & (
            factor_flat["time"] <= pd.Timestamp(train_end)
        )
        mask_fr = (returns_flat["time"] >= pd.Timestamp(train_start)) & (
            returns_flat["time"] <= pd.Timestamp(train_end)
        )

        ic = compute_ic_series(
            factor_flat[mask_fv], returns_flat[mask_fr], min_obs=30
        )

        golden_ic = pd.read_parquet(OUTPUTS / "ic_series_train.parquet")["ic"]
        pd.testing.assert_series_equal(
            ic.rename("ic").sort_index(),
            golden_ic.sort_index(),
            atol=ATOL,
            check_names=False,
        )


class TestComputeEffectStrength:
    def test_effect_strength_matches_golden(
        self,
        factor_flat: pd.DataFrame,
        returns_flat: pd.DataFrame,
        date_range: tuple[str, str, str, str],
        golden: dict,
    ) -> None:
        train_start, train_end, val_start, val_end = date_range
        result = compute_effect_strength(
            factor_flat,
            returns_flat,
            train_range=(train_start, train_end),
            validation_range=(val_start, val_end),
            min_obs=30,
        )

        g = golden["effect_strength"]

        for field in ("ic_mean", "ic_std", "ic_ir", "ic_win_rate", "n_days"):
            assert result["train"][field] == pytest.approx(
                g["train"][field], abs=ATOL
            ), f"train.{field} mismatch"
            assert result["validation"][field] == pytest.approx(
                g["validation"][field], abs=ATOL
            ), f"validation.{field} mismatch"


class TestComputeIcAnalytics:
    def test_analytics_on_validation_ic(
        self,
        factor_flat: pd.DataFrame,
        returns_flat: pd.DataFrame,
        date_range: tuple[str, str, str, str],
    ) -> None:
        _, _, val_start, val_end = date_range
        mask_fv = (factor_flat["time"] >= pd.Timestamp(val_start)) & (
            factor_flat["time"] <= pd.Timestamp(val_end)
        )
        mask_fr = (returns_flat["time"] >= pd.Timestamp(val_start)) & (
            returns_flat["time"] <= pd.Timestamp(val_end)
        )
        ic = compute_ic_series(factor_flat[mask_fv], returns_flat[mask_fr])
        analytics = compute_ic_analytics(ic)

        assert set(analytics.keys()) == {
            "by_year",
            "autocorr_lag1",
            "cum_ic_max_drawdown",
            "best_quarter",
            "worst_quarter",
        }
        assert isinstance(analytics["by_year"], dict)
        assert analytics["autocorr_lag1"] is not None
        assert analytics["cum_ic_max_drawdown"] is not None
        assert analytics["best_quarter"] >= analytics["worst_quarter"]

    def test_empty_series(self) -> None:
        empty = pd.Series(dtype=float)
        empty.index = pd.DatetimeIndex([])
        out = compute_ic_analytics(empty)
        assert out["by_year"] == {}
        assert out["autocorr_lag1"] is None
        assert out["best_quarter"] is None


class TestComputeMultiHorizonIc:
    def test_multiple_horizons(
        self,
        factor_flat: pd.DataFrame,
        returns_flat: pd.DataFrame,
        date_range: tuple[str, str, str, str],
    ) -> None:
        train_start, train_end, val_start, val_end = date_range
        returns_by_h = {1: returns_flat, 5: returns_flat}
        out = compute_multi_horizon_ic(
            factor_flat,
            returns_by_h,
            train_range=(train_start, train_end),
            validation_range=(val_start, val_end),
        )
        assert set(out.keys()) == {1, 5}
        for h in (1, 5):
            for split in ("train", "validation"):
                for field in ("ic_mean", "ic_std", "ic_ir", "ic_win_rate", "n_days"):
                    assert field in out[h][split]
            assert isinstance(out[h]["ic_series_train"], pd.Series)
            assert isinstance(out[h]["ic_series_validation"], pd.Series)


class TestComputeIcHalfLife:
    def test_clean_decay(self) -> None:
        ic_means = {1: 0.02, 3: 0.015, 5: 0.01, 10: 0.005, 20: 0.002}
        hl = compute_ic_half_life(ic_means)
        assert hl is not None
        # target = 0.01, reached at h=5 → half-life exactly 5
        assert hl == pytest.approx(5.0, abs=1e-4)

    def test_insufficient_points(self) -> None:
        assert compute_ic_half_life({1: 0.02}) is None
        assert compute_ic_half_life({}) is None

    def test_nan_values_filtered(self) -> None:
        ic_means = {1: 0.02, 3: float("nan"), 5: 0.01}
        hl = compute_ic_half_life(ic_means)
        assert hl is not None
