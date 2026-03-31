"""Tests for vectorized preprocessing equivalence and edge-case guards."""
import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch

from mining.config import MiningConfig
from mining.preprocessing import FactorPreprocessor


def _make_factor(dates, instruments, values, col="factor"):
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    return pd.DataFrame({col: values}, index=idx)


@pytest.fixture
def config():
    return MiningConfig(
        winsorize_method="mad", winsorize_n=5.0, standardize_method="zscore",
        neutralize_mode="none", filter_suspend=False, filter_limit=False,
    )


@pytest.fixture
def preprocessor(config):
    return FactorPreprocessor(config)


class TestCleanFactorValuesVectorized:

    def test_output_shape_unchanged(self, preprocessor):
        dates = pd.bdate_range("2023-01-02", periods=20)
        instruments = [f"S{i:03d}" for i in range(50)]
        np.random.seed(0)
        vals = np.random.randn(len(dates) * len(instruments))
        df = _make_factor(dates, instruments, vals)
        result = preprocessor.clean_factor_values(df)
        assert result.shape == df.shape

    def test_sparse_date_guard_preserved(self, preprocessor):
        """Dates with < 3 valid values must be left unchanged."""
        dates = pd.bdate_range("2023-01-02", periods=3)
        instruments = ["A", "B", "C", "D"]
        # date 1: only 1 valid (< 3) — must be left as-is
        vals = [1.0, 2.0, 3.0, 4.0,
                100.0, np.nan, np.nan, np.nan,
                1.0, 2.0, 3.0, 4.0]
        df = _make_factor(dates, instruments, vals)
        result = preprocessor.clean_factor_values(df)
        assert result.loc[(dates[1], "A"), "factor"] == pytest.approx(100.0)

    def test_inf_replaced_with_nan(self, preprocessor):
        dates = pd.bdate_range("2023-01-02", periods=2)
        instruments = [f"S{i}" for i in range(10)]
        vals = np.random.randn(20)
        vals[5] = np.inf
        vals[12] = -np.inf
        df = _make_factor(dates, instruments, vals)
        result = preprocessor.clean_factor_values(df)
        assert result["factor"].isna().sum() >= 2

    def test_mad_zero_does_not_crash(self, preprocessor):
        """Constant cross-section (MAD=0) must not crash."""
        dates = pd.bdate_range("2023-01-02", periods=2)
        instruments = [f"S{i}" for i in range(10)]
        vals = [5.0] * 10 + list(np.random.randn(10))
        df = _make_factor(dates, instruments, vals)
        assert preprocessor.clean_factor_values(df) is not None

    def test_output_approximately_zscore(self, preprocessor):
        """After cleaning, values per date should be ~zero-mean unit-variance."""
        dates = pd.bdate_range("2023-01-02", periods=10)
        instruments = [f"S{i:03d}" for i in range(100)]
        np.random.seed(42)
        vals = np.random.randn(len(dates) * len(instruments))
        df = _make_factor(dates, instruments, vals)
        result = preprocessor.clean_factor_values(df)
        for dt in dates:
            day_vals = result.xs(dt, level="datetime")["factor"].dropna()
            if len(day_vals) >= 3:
                assert abs(day_vals.mean()) < 0.1
                assert abs(day_vals.std() - 1.0) < 0.15

    def test_vectorized_matches_legacy(self, preprocessor):
        """Vectorized output must match _clean_factor_values_legacy on same input."""
        dates = pd.bdate_range("2023-01-02", periods=30)
        instruments = [f"S{i:03d}" for i in range(60)]
        np.random.seed(7)
        vals = np.random.randn(len(dates) * len(instruments))
        vals[10] = 50.0
        vals[200] = np.nan
        vals[500] = -30.0
        df = _make_factor(dates, instruments, vals)
        new_result = preprocessor.clean_factor_values(df)
        old_result = preprocessor._clean_factor_values_legacy(df)
        pd.testing.assert_frame_equal(
            new_result.dropna(), old_result.dropna(), check_exact=False, atol=1e-6,
        )
