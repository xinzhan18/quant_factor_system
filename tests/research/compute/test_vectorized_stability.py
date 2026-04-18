"""Golden-fixture tests for vectorized_stability."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from research.compute.vectorized_stability import (
    compute_sign_consistency,
    compute_split_stability,
    compute_train_validation_decay,
)

FIXTURES = Path(__file__).parent / "_fixtures"
INPUTS = FIXTURES / "inputs"
OUTPUTS = FIXTURES / "outputs"


@pytest.fixture(scope="module")
def ic_val() -> pd.Series:
    return pd.read_parquet(OUTPUTS / "ic_series_validation.parquet")["ic"]


@pytest.fixture(scope="module")
def ic_train() -> pd.Series:
    return pd.read_parquet(OUTPUTS / "ic_series_train.parquet")["ic"]


@pytest.fixture(scope="module")
def golden() -> dict:
    with open(OUTPUTS / "golden.yaml") as f:
        return yaml.safe_load(f)


class TestSplitStability:
    def test_matches_golden(
        self, ic_val: pd.Series, golden: dict
    ) -> None:
        result = compute_split_stability(ic_val, n_splits=4, min_days=40)
        g = golden["stability"]["split_stability"]

        assert result["n_splits"] == g["n_splits"]
        assert "bucket" not in result
        assert result["sign_consistency"] == pytest.approx(
            g["sign_consistency"], abs=1e-6
        )
        assert result["dispersion"] == pytest.approx(g["dispersion"], abs=1e-6)
        np.testing.assert_array_almost_equal(
            result["split_ic_means"],
            g["split_ic_means"],
            decimal=10,
        )

    def test_insufficient_days_returns_sentinel(self) -> None:
        ic = pd.Series(
            [0.01, 0.02],
            index=pd.DatetimeIndex(["2024-01-02", "2024-01-03"]),
        )
        result = compute_split_stability(ic, n_splits=4, min_days=60)
        assert result["n_splits"] == 0
        assert result["sign_consistency"] is None
        assert result["dispersion"] is None


class TestSignConsistency:
    def test_same_sign_returns_true(
        self, ic_train: pd.Series, ic_val: pd.Series
    ) -> None:
        # golden shows both train and val are positive
        assert compute_sign_consistency(ic_train, ic_val) is True

    def test_opposite_sign_returns_false(self) -> None:
        t = pd.Series([0.01, 0.02, 0.015])
        v = pd.Series([-0.01, -0.005, -0.02])
        assert compute_sign_consistency(t, v) is False

    def test_near_zero_returns_false(self) -> None:
        t = pd.Series([1e-15, -1e-15])
        v = pd.Series([0.01, 0.02])
        assert compute_sign_consistency(t, v) is False


class TestTrainValidationDecay:
    def test_equal_gives_ratio_one(self) -> None:
        assert compute_train_validation_decay(0.05, 0.05) == pytest.approx(1.0)

    def test_decay_below_one(self) -> None:
        assert compute_train_validation_decay(0.10, 0.05) == pytest.approx(0.5)

    def test_zero_train_returns_nan(self) -> None:
        result = compute_train_validation_decay(0.0, 0.05)
        assert np.isnan(result)

    def test_sign_flip_yields_negative_ratio(self) -> None:
        """Signed ratio: opposite signs produce a negative decay."""
        assert compute_train_validation_decay(0.10, -0.05) == pytest.approx(-0.5)

    def test_both_negative_positive_ratio(self) -> None:
        assert compute_train_validation_decay(-0.10, -0.05) == pytest.approx(0.5)
