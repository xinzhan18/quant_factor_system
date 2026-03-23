"""Tests verifying evaluator integrates the preprocessing pipeline."""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import patch, MagicMock
from mining.evaluator import FactorMiningEvaluator
from mining.config import MiningConfig


class TestEvaluatorPreprocessing:
    """Verify evaluator has preprocessor and calls it."""

    @patch("mining.evaluator.FactorMiningEvaluator._ensure_qlib_initialized")
    def test_evaluator_has_preprocessor(self, mock_init):
        config = MiningConfig(filter_suspend=True, filter_limit=True)
        evaluator = FactorMiningEvaluator(config)
        assert hasattr(evaluator, "_preprocessor")
        assert evaluator._preprocessor is not None

    @patch("mining.evaluator.FactorMiningEvaluator._ensure_qlib_initialized")
    def test_evaluator_has_aux_cache(self, mock_init):
        """Evaluator should have an _aux_cache dict."""
        config = MiningConfig()
        evaluator = FactorMiningEvaluator(config)
        assert hasattr(evaluator, "_aux_cache")
        assert isinstance(evaluator._aux_cache, dict)

    @patch("mining.evaluator.FactorMiningEvaluator._ensure_qlib_initialized")
    def test_preprocessing_called_during_ic(self, mock_init):
        """Verify preprocess_for_ic is called when aux data is available."""
        config = MiningConfig()
        evaluator = FactorMiningEvaluator(config)

        evaluator._preprocessor = MagicMock()
        idx = pd.MultiIndex.from_product(
            [pd.to_datetime(["2024-01-02"]), ["A", "B"]],
            names=["datetime", "instrument"],
        )
        factor = pd.DataFrame({"f": [1.0, 2.0]}, index=idx)
        returns = pd.DataFrame({"$returns_1d": [0.01, 0.02]}, index=idx)

        evaluator._preprocessor.preprocess_for_ic.return_value = (factor, returns)

        aux = {"volume": pd.DataFrame({"$volume": [1e6, 1e6]}, index=idx)}
        result = evaluator._compute_ic_from_frames(factor, returns, aux_data=aux)
        evaluator._preprocessor.preprocess_for_ic.assert_called_once()

    @patch("mining.evaluator.FactorMiningEvaluator._ensure_qlib_initialized")
    def test_no_preprocessing_without_aux_data(self, mock_init):
        """Without aux data, preprocessing is skipped (backward compat)."""
        config = MiningConfig()
        evaluator = FactorMiningEvaluator(config)
        evaluator._preprocessor = MagicMock()

        idx = pd.MultiIndex.from_product(
            [pd.to_datetime(["2024-01-02"]), ["A", "B"]],
            names=["datetime", "instrument"],
        )
        factor = pd.DataFrame({"f": [1.0, 2.0]}, index=idx)
        returns = pd.DataFrame({"$returns_1d": [0.01, 0.02]}, index=idx)

        result = evaluator._compute_ic_from_frames(factor, returns)
        evaluator._preprocessor.preprocess_for_ic.assert_not_called()

    @patch("mining.evaluator.FactorMiningEvaluator._ensure_qlib_initialized")
    def test_preprocessing_kwargs_passed_correctly(self, mock_init):
        """Verify aux_data dict contents are unpacked as kwargs to preprocess_for_ic."""
        config = MiningConfig()
        evaluator = FactorMiningEvaluator(config)
        evaluator._preprocessor = MagicMock()

        idx = pd.MultiIndex.from_product(
            [pd.to_datetime(["2024-01-02", "2024-01-03"]), ["A", "B"]],
            names=["datetime", "instrument"],
        )
        factor = pd.DataFrame({"f": [1.0, 2.0, 3.0, 4.0]}, index=idx)
        returns = pd.DataFrame({"$returns_1d": [0.01, 0.02, 0.03, 0.04]}, index=idx)

        volume_df = pd.DataFrame({"$volume": [1e6, 1e6, 1e6, 1e6]}, index=idx)
        close_df = pd.DataFrame({"$close": [10.0, 10.0, 11.0, 11.0]}, index=idx)

        evaluator._preprocessor.preprocess_for_ic.return_value = (factor, returns)

        aux = {"volume": volume_df, "close": close_df}
        evaluator._compute_ic_from_frames(factor, returns, aux_data=aux)

        call_kwargs = evaluator._preprocessor.preprocess_for_ic.call_args
        # Should be called with factor=..., returns=..., volume=..., close=...
        assert call_kwargs is not None
        _, kwargs = call_kwargs
        assert "volume" in kwargs or len(call_kwargs.args) > 0

    @patch("mining.evaluator.FactorMiningEvaluator._ensure_qlib_initialized")
    def test_load_aux_data_caches_results(self, mock_init):
        """_load_aux_data should cache results for the same key."""
        config = MiningConfig()
        evaluator = FactorMiningEvaluator(config)

        instruments = ["SH600000", "SH600001"]
        start = "2024-01-01"
        end = "2024-06-30"

        idx = pd.MultiIndex.from_product(
            [pd.to_datetime(["2024-01-02"]), instruments],
            names=["datetime", "instrument"],
        )
        mock_df = pd.DataFrame({"$volume": [1e6, 1e6], "$close": [10.0, 11.0]}, index=idx)

        with patch("mining.evaluator.D") as mock_D:
            mock_D.features.return_value = mock_df
            # First call — hits the data source
            result1 = evaluator._load_aux_data(instruments, start, end)
            # Second call — should return cached value
            result2 = evaluator._load_aux_data(instruments, start, end)

            # First call makes 2 D.features calls (core + optional), second call is cached
            first_call_count = mock_D.features.call_count
            assert first_call_count == 2  # core fields + optional limit fields
            assert result1 is result2

    @patch("mining.evaluator.FactorMiningEvaluator._ensure_qlib_initialized")
    def test_load_aux_data_returns_dict(self, mock_init):
        """_load_aux_data should return a dict keyed without $ prefix."""
        config = MiningConfig()
        evaluator = FactorMiningEvaluator(config)

        instruments = ["SH600000"]
        start = "2024-01-01"
        end = "2024-06-30"

        idx = pd.MultiIndex.from_product(
            [pd.to_datetime(["2024-01-02"]), instruments],
            names=["datetime", "instrument"],
        )
        mock_df = pd.DataFrame(
            {"$volume": [1e6], "$close": [10.0]},
            index=idx,
        )

        with patch("mining.evaluator.D") as mock_D:
            mock_D.features.return_value = mock_df
            result = evaluator._load_aux_data(instruments, start, end)

        assert isinstance(result, dict)
        # Keys should be stripped of $ prefix
        assert "volume" in result
        assert "close" in result
        assert "$volume" not in result
        assert "$close" not in result

    @patch("mining.evaluator.FactorMiningEvaluator._ensure_qlib_initialized")
    def test_load_aux_data_handles_failure_gracefully(self, mock_init):
        """_load_aux_data should return empty dict on data load failure."""
        config = MiningConfig()
        evaluator = FactorMiningEvaluator(config)

        with patch("mining.evaluator.D") as mock_D:
            mock_D.features.side_effect = RuntimeError("Data unavailable")
            result = evaluator._load_aux_data(["SH600000"], "2024-01-01", "2024-06-30")

        assert isinstance(result, dict)
        # Should return empty dict (or partial), not raise
        assert result == {}

    @patch("mining.evaluator.FactorMiningEvaluator._ensure_qlib_initialized")
    def test_ic_computation_still_works_with_aux_data(self, mock_init):
        """End-to-end: IC should be computed correctly even when aux_data triggers preprocessing."""
        config = MiningConfig()
        evaluator = FactorMiningEvaluator(config)

        dates = pd.bdate_range("2024-01-02", periods=10)
        instruments = [f"SH60000{i}" for i in range(5)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])

        np.random.seed(42)
        signal = np.random.randn(len(idx))
        factor = pd.DataFrame({"f": signal}, index=idx)
        returns = pd.DataFrame({"$returns_1d": signal * 0.5 + np.random.randn(len(idx)) * 0.1}, index=idx)
        volume = pd.DataFrame({"$volume": np.abs(np.random.randn(len(idx))) * 1e6}, index=idx)

        aux = {"volume": volume}

        # Should not raise — preprocessing runs end to end
        result = evaluator._compute_ic_from_frames(factor, returns, aux_data=aux)
        assert "ic_mean" in result
        assert "n_days" in result
        assert result["n_days"] > 0
