"""Golden-fixture tests for vectorized_stability."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from research.compute.vectorized_stability import (
    compute_expanding_window_ic,
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
        assert result["bucket"] == g["bucket"]
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
        assert result["bucket"] == "insufficient_splits"
        assert result["n_splits"] == 0


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

    def test_sign_ignored(self) -> None:
        """Ratio is |val| / |train| — sign doesn't matter."""
        assert compute_train_validation_decay(-0.10, 0.05) == pytest.approx(0.5)


class TestExpandingWindowSmoke:
    """Smoke test — expanding window is not in golden.yaml, so we just check
    it runs on the fixture inputs and produces the expected shape + a
    plausible pass/fail."""

    def test_expanding_window_runs(self) -> None:
        # Fixture spans 2018-01-02 to 2020-04-20 (600 business days).
        # Start at 2018-02 with 3-month steps → ~8 expansion points.
        fv = pd.read_parquet(INPUTS / "factor_values.parquet")
        fr = pd.read_parquet(INPUTS / "forward_returns.parquet")
        result = compute_expanding_window_ic(
            fv, fr, start="2018-02-01", step_months=3, min_obs=30
        )
        assert "path" in result
        assert "pass" in result
        assert isinstance(result["pass"], bool)
        # Should have at least 6 expansion points within the fixture span
        assert len(result["path"]) >= 6
        # The fixture factor has a strong stable signal, so sign_consistency
        # must be 1.0 (every expansion yields the same-sign IC)
        assert result["sign_consistency"] == pytest.approx(1.0)
        # Stability must be >= 0.3 (low coefficient of variation)
        assert result["stability"] >= 0.3
        # Both criteria met → pass must be True
        assert result["pass"] is True
