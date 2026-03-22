"""Tests for FactorMiningEvaluator."""

from unittest.mock import patch, MagicMock

import numpy as np
import pandas as pd
import pytest
import yaml
from pathlib import Path
from scipy.stats import spearmanr

from mining.config import MiningConfig
from mining.evaluator import FactorMiningEvaluator, BatchResult
from mining.library import FactorLibrary


@pytest.fixture
def evaluator(config):
    """Evaluator with Qlib init mocked."""
    with patch.object(FactorMiningEvaluator, "_ensure_qlib_initialized"):
        return FactorMiningEvaluator(config)


class TestBatchResult:
    def test_dataclass(self):
        r = BatchResult(admitted=[], rejected=[], replacements=[])
        assert r.admitted == []


class TestComputeIC:
    def test_positive_ic(self, evaluator):
        dates = pd.bdate_range("2023-01-02", periods=20)
        instruments = [f"SH60000{i}" for i in range(10)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        np.random.seed(42)
        signal = np.random.randn(len(idx))
        noise = np.random.randn(len(idx)) * 0.3
        factor_df = pd.DataFrame({"factor": signal}, index=idx)
        returns_df = pd.DataFrame({"$returns_1d": signal + noise}, index=idx)
        ic_stats = evaluator._compute_ic_from_frames(factor_df, returns_df)
        assert ic_stats["ic_mean"] > 0.5
        assert ic_stats["n_days"] == 20

    def test_zero_ic(self, evaluator):
        dates = pd.bdate_range("2023-01-02", periods=50)
        instruments = [f"SH60000{i}" for i in range(20)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        np.random.seed(42)
        factor_df = pd.DataFrame({"factor": np.random.randn(len(idx))}, index=idx)
        np.random.seed(999)
        returns_df = pd.DataFrame({"$returns_1d": np.random.randn(len(idx)) * 0.02}, index=idx)
        ic_stats = evaluator._compute_ic_from_frames(factor_df, returns_df)
        assert abs(ic_stats["ic_mean"]) < 0.15
        assert ic_stats["n_days"] == 50

    def test_ic_stats_keys(self, evaluator, sample_factor_values, sample_returns):
        ic_stats = evaluator._compute_ic_from_frames(sample_factor_values, sample_returns)
        assert "ic_mean" in ic_stats
        assert "ic_std" in ic_stats
        assert "ic_ir" in ic_stats
        assert "ic_win_rate" in ic_stats
        assert "n_days" in ic_stats


class TestStage1FastIC:
    def test_passes_high_ic_factor(self, evaluator):
        candidates = [{"name": "F1", "expression": "Rank($close)", "category": "momentum"}]
        dates = pd.bdate_range("2023-01-02", periods=30)
        instruments = [f"SH60000{i}" for i in range(10)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        np.random.seed(42)
        signal = np.random.randn(len(idx))
        with patch.object(evaluator, "_compute_factor_qlib") as mock_factor, \
             patch.object(evaluator, "_get_returns_qlib") as mock_returns, \
             patch.object(evaluator, "_get_fast_screening_universe", return_value=instruments):
            mock_factor.return_value = pd.DataFrame({"factor": signal}, index=idx)
            mock_returns.return_value = pd.DataFrame({"$returns_1d": signal + np.random.randn(len(idx)) * 0.2}, index=idx)
            passed = evaluator._fast_ic_screening(candidates)
            assert len(passed) == 1
            assert abs(passed[0]["stage1"]["ic_mean"]) >= evaluator.config.ic_threshold

    def test_rejects_low_ic_factor(self, evaluator):
        candidates = [{"name": "F_bad", "expression": "Rank($close)", "category": "momentum"}]
        dates = pd.bdate_range("2023-01-02", periods=30)
        instruments = [f"SH60000{i}" for i in range(10)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        with patch.object(evaluator, "_compute_factor_qlib") as mock_factor, \
             patch.object(evaluator, "_get_returns_qlib") as mock_returns, \
             patch.object(evaluator, "_get_fast_screening_universe", return_value=instruments):
            np.random.seed(42)
            mock_factor.return_value = pd.DataFrame({"factor": np.random.randn(len(idx))}, index=idx)
            np.random.seed(999)
            mock_returns.return_value = pd.DataFrame({"$returns_1d": np.random.randn(len(idx)) * 0.01}, index=idx)
            passed = evaluator._fast_ic_screening(candidates)
            assert len(passed) == 0


class TestStage15BatchDedup:
    def test_dedup_removes_correlated(self, evaluator):
        dates = pd.bdate_range("2023-01-02", periods=20)
        instruments = [f"SH60000{i}" for i in range(10)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        np.random.seed(42)
        signal = np.random.randn(len(idx))
        candidates = [
            {"name": "F1", "expression": "Rank($close)", "stage1": {"ic_mean": 0.06}},
            {"name": "F2", "expression": "Rank($close) + 0.001", "stage1": {"ic_mean": 0.04}},
        ]
        with patch.object(evaluator, "_compute_factor_qlib") as mock_factor, \
             patch.object(evaluator, "_get_fast_screening_universe", return_value=instruments):
            mock_factor.side_effect = [
                pd.DataFrame({"factor": signal}, index=idx),
                pd.DataFrame({"factor": signal + np.random.randn(len(idx)) * 0.01}, index=idx),
            ]
            result = evaluator._batch_dedup(candidates)
            assert len(result) == 1
            assert result[0]["name"] == "F1"

    def test_dedup_keeps_uncorrelated(self, evaluator):
        dates = pd.bdate_range("2023-01-02", periods=20)
        instruments = [f"SH60000{i}" for i in range(10)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        candidates = [
            {"name": "F1", "expression": "Rank($close)", "stage1": {"ic_mean": 0.06}},
            {"name": "F2", "expression": "Rank($volume)", "stage1": {"ic_mean": 0.05}},
        ]
        with patch.object(evaluator, "_compute_factor_qlib") as mock_factor, \
             patch.object(evaluator, "_get_fast_screening_universe", return_value=instruments):
            np.random.seed(42)
            mock_factor.side_effect = [
                pd.DataFrame({"factor": np.random.randn(len(idx))}, index=idx),
                pd.DataFrame({"factor": np.random.randn(len(idx))}, index=idx),
            ]
            result = evaluator._batch_dedup(candidates)
            assert len(result) == 2


class TestStage2CorrelationCheck:
    def test_passes_uncorrelated_factor(self, evaluator, tmp_mining_dir, config):
        lib_dir = Path(config.library_dir)
        (lib_dir / "library.yaml").write_text(yaml.dump({"thresholds": {"ic_min": 0.03, "correlation_max": 0.5}, "factors": []}))
        dates = pd.bdate_range("2023-01-02", periods=20)
        instruments = [f"SH60000{i}" for i in range(10)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        np.random.seed(42)
        candidates = [{"name": "F1", "expression": "Rank($close)", "category": "momentum", "stage1": {"ic_mean": 0.05}}]
        signal = np.random.randn(len(idx))
        with patch.object(evaluator, "_compute_factor_qlib") as mock_factor, \
             patch.object(evaluator, "_get_returns_qlib") as mock_returns, \
             patch.object(evaluator, "_get_full_universe", return_value=instruments):
            mock_factor.return_value = pd.DataFrame({"factor": signal}, index=idx)
            mock_returns.return_value = pd.DataFrame({"$returns_1d": signal + np.random.randn(len(idx)) * 0.3}, index=idx)
            passed, rejected = evaluator._correlation_check(candidates)
            assert len(passed) == 1
            assert len(rejected) == 0


class TestStage25Replacement:
    def test_replacement_condition(self, evaluator):
        candidate = {
            "name": "Better_F", "expression": "Rank(Div($close, $vwap))",
            "full_ic": {"ic_mean": 0.08},
            "stage2": {"max_corr": 0.6, "max_corr_factor": "001", "passed": False},
        }
        with patch.object(evaluator, "_get_library_factor_ic", return_value=0.04), \
             patch.object(evaluator, "_count_library_conflicts", return_value=1):
            replacements = evaluator._replacement_check([candidate])
            assert len(replacements) == 1
            assert replacements[0]["replaces"] == "001"

    def test_no_replacement_if_multi_conflict(self, evaluator):
        candidate = {
            "name": "F", "expression": "X",
            "full_ic": {"ic_mean": 0.08},
            "stage2": {"max_corr": 0.6, "max_corr_factor": "001", "passed": False},
        }
        with patch.object(evaluator, "_get_library_factor_ic", return_value=0.04), \
             patch.object(evaluator, "_count_library_conflicts", return_value=2):
            replacements = evaluator._replacement_check([candidate])
            assert len(replacements) == 0


class TestStage3FullValidation:
    def test_full_metrics(self, evaluator):
        dates_is = pd.bdate_range("2023-01-02", periods=30)
        dates_oos = pd.bdate_range("2024-01-02", periods=15)
        instruments = [f"SH60000{i}" for i in range(20)]
        idx_is = pd.MultiIndex.from_product([dates_is, instruments], names=["datetime", "instrument"])
        idx_oos = pd.MultiIndex.from_product([dates_oos, instruments], names=["datetime", "instrument"])
        np.random.seed(42)
        signal_is = np.random.randn(len(idx_is))
        signal_oos = np.random.randn(len(idx_oos))
        candidate = {"name": "F1", "expression": "Rank($close)", "stage1": {"ic_mean": 0.05}}
        evaluator._factor_cache["Rank($close)"] = pd.DataFrame({"factor": signal_is}, index=idx_is)
        with patch.object(evaluator, "_get_returns_qlib") as mock_returns, \
             patch.object(evaluator, "_compute_factor_qlib") as mock_factor, \
             patch.object(evaluator, "_get_full_universe", return_value=instruments):
            mock_returns.side_effect = [
                pd.DataFrame({"$returns_1d": signal_is * 0.5 + np.random.randn(len(idx_is)) * 0.1}, index=idx_is),
                pd.DataFrame({"$returns_1d": signal_oos * 0.5 + np.random.randn(len(idx_oos)) * 0.1}, index=idx_oos),
            ]
            mock_factor.return_value = pd.DataFrame({"factor": signal_oos}, index=idx_oos)
            validated, errors = evaluator._full_validation([candidate])
            assert len(validated) == 1
            assert len(errors) == 0
            s3 = validated[0]["stage3"]
            assert "ic_mean_is" in s3
            assert "ic_mean_oos" in s3
            assert "quantile_returns" in s3
            assert "ls_return" in s3
            assert "monotonicity" in s3


class TestEvaluateBatch:
    def test_full_pipeline(self, evaluator):
        dates = pd.bdate_range("2023-01-02", periods=30)
        instruments = [f"SH60000{i}" for i in range(10)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        np.random.seed(42)
        signal = np.random.randn(len(idx))
        candidates = [{"name": "Good_F", "expression": "Rank($close)", "category": "momentum"}]
        with patch.object(evaluator, "_ensure_qlib_initialized"), \
             patch.object(evaluator, "_compute_factor_qlib") as mock_factor, \
             patch.object(evaluator, "_get_returns_qlib") as mock_returns, \
             patch.object(evaluator, "_get_fast_screening_universe", return_value=instruments), \
             patch.object(evaluator, "_get_full_universe", return_value=instruments), \
             patch.object(evaluator, "_load_library") as mock_lib:
            mock_factor.return_value = pd.DataFrame({"factor": signal}, index=idx)
            mock_returns.return_value = pd.DataFrame({"$returns_1d": signal + np.random.randn(len(idx)) * 0.2}, index=idx)
            mock_lib_obj = MagicMock()
            mock_lib_obj.list_factors.return_value = []
            mock_lib.return_value = mock_lib_obj
            result = evaluator.evaluate_batch(candidates)
            assert isinstance(result, BatchResult)
            total = len(result.admitted) + len(result.rejected) + len(result.replacements)
            assert total >= 1
