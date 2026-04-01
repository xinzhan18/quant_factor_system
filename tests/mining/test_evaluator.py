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
        r = BatchResult(screened=[], rejected=[], replacements=[])
        assert r.screened == []
        assert r.admitted == []  # backward-compat alias

    def test_admitted_alias(self):
        data = [{"name": "F1"}]
        r = BatchResult(screened=data, rejected=[], replacements=[])
        assert r.admitted is r.screened

    def test_to_dict_uses_screened_key(self):
        r = BatchResult(screened=[{"name": "F1", "expression": "X", "category": "other"}],
                        rejected=[], replacements=[])
        d = r.to_dict()
        assert "screened" in d
        assert len(d["screened"]) == 1


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
             patch.object(evaluator, "_get_full_universe", return_value=instruments), \
             patch.object(evaluator, "_stage1_window", return_value=("2022-01-01", "2022-12-31")):
            mock_factor.return_value = pd.DataFrame({"factor": signal}, index=idx)
            mock_returns.return_value = pd.DataFrame({"$returns_1d": signal + np.random.randn(len(idx)) * 0.2}, index=idx)
            passed = evaluator._fast_ic_screening(candidates)
            assert len(passed) == 1
            assert abs(passed[0]["stage1"]["ic_mean"]) >= evaluator.config.ic_threshold

    def test_rejects_low_ic_factor(self, evaluator):
        candidates = [{"name": "F_bad", "expression": "Rank($close)", "category": "momentum"}]
        # Use 200 dates × 50 instruments so random IC reliably stays below 0.01
        dates = pd.bdate_range("2020-01-02", periods=200)
        instruments = [f"SH60000{i}" for i in range(50)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        factor_vals = np.random.RandomState(0).randn(len(idx))
        returns_vals = np.random.RandomState(1).randn(len(idx)) * 0.01
        with patch.object(evaluator, "_compute_factor_qlib") as mock_factor, \
             patch.object(evaluator, "_get_returns_qlib") as mock_returns, \
             patch.object(evaluator, "_get_full_universe", return_value=instruments), \
             patch.object(evaluator, "_stage1_window", return_value=("2022-01-01", "2022-12-31")):
            mock_factor.return_value = pd.DataFrame({"factor": factor_vals}, index=idx)
            mock_returns.return_value = pd.DataFrame({"$returns_1d": returns_vals}, index=idx)
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
             patch.object(evaluator, "_get_full_universe", return_value=instruments), \
             patch.object(evaluator, "_stage1_window", return_value=("2022-01-01", "2022-12-31")):
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
        evaluator._lib_values_cache = {}

        returns_is = pd.DataFrame({"$returns_1d": signal_is * 0.5 + np.random.randn(len(idx_is)) * 0.1}, index=idx_is)
        returns_oos = pd.DataFrame({"$returns_1d": signal_oos * 0.5 + np.random.randn(len(idx_oos)) * 0.1}, index=idx_oos)

        def mock_factor_side_effect(expr, instruments, start, end):
            """Return OOS factor values or multi-horizon returns."""
            if "Ref($close" in expr:
                return returns_is  # multi-horizon returns (approximate)
            return pd.DataFrame({"factor": signal_oos}, index=idx_oos)

        with patch.object(evaluator, "_get_returns_qlib") as mock_returns, \
             patch.object(evaluator, "_compute_factor_qlib", side_effect=mock_factor_side_effect), \
             patch.object(evaluator, "_load_aux_data", return_value={}), \
             patch.object(evaluator, "_get_full_universe", return_value=instruments):
            mock_returns.side_effect = [returns_is, returns_oos]
            validated, errors = evaluator._compute_report_cards([candidate])
            assert len(validated) == 1
            assert len(errors) == 0

            # Check backward-compatible stage3 keys
            s3 = validated[0]["stage3"]
            assert "ic_mean_is" in s3
            assert "ic_mean_oos" in s3
            assert "quantile_returns" in s3
            assert "ls_return" in s3
            assert "monotonicity" in s3

            # Check new report_card key
            rc = validated[0]["report_card"]
            assert isinstance(rc, dict)
            assert "ic_mean" in rc
            assert "ic_ir" in rc
            assert "oos_decay_ratio" in rc
            assert "coverage" in rc
            assert "expression_depth" in rc


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


class TestTransientKeys:
    """Verify _factor_values, _factor_values_oos are attached after Stage 3."""

    def test_admitted_factors_have_transient_values(self, config, sample_factor_values, sample_returns):
        from mining.evaluator import FactorMiningEvaluator

        evaluator = FactorMiningEvaluator.__new__(FactorMiningEvaluator)
        evaluator.config = config
        evaluator._factor_cache = {"Rank($close)": sample_factor_values}
        evaluator._subset_factor_cache = {}
        evaluator._aux_cache = {}
        evaluator._lib_values_cache = {}
        evaluator._preprocessor = MagicMock()

        def mock_compute(expr, instruments, start, end):
            if "Ref($close" in expr:
                return sample_returns.rename(columns={sample_returns.columns[0]: expr})
            return sample_factor_values

        with patch.object(evaluator, '_get_full_universe', return_value=["SH600000"]):
            with patch.object(evaluator, '_get_returns_qlib', return_value=sample_returns):
                with patch.object(evaluator, '_compute_factor_qlib', side_effect=mock_compute):
                    with patch.object(evaluator, '_load_aux_data', return_value={}):
                        candidates = [{"name": "Test", "expression": "Rank($close)", "category": "momentum"}]
                        validated, errors = evaluator._compute_report_cards(candidates)

        assert len(validated) == 1
        c = validated[0]
        assert "_factor_values" in c
        assert "_factor_values_oos" in c
        assert isinstance(c["_factor_values"], pd.DataFrame)
        assert isinstance(c["_factor_values_oos"], pd.DataFrame)
        assert "report_card" in c
        assert isinstance(c["report_card"], dict)


class TestOptunaOptimization:
    def test_optimize_params_no_param_space(self, evaluator):
        """Candidates without param_space pass through unchanged (same object returned)."""
        c = {"name": "test", "type": "dsl", "expression": "Std($close, 20)", "category": "vol"}
        result = evaluator._optimize_params(c)
        assert result is c  # Same object, unchanged

    def test_optimize_params_method_exists(self):
        """Method exists on FactorMiningEvaluator."""
        from mining.evaluator import FactorMiningEvaluator
        assert hasattr(FactorMiningEvaluator, "_optimize_params")

    def test_optimize_params_returns_dict_with_params(self, evaluator):
        """When param_space present, _optimize_params returns a dict with 'params' key."""
        candidate = {
            "name": "py_opt",
            "source": "python",
            "code": "return df['close'].rolling(params['window']).std()",
            "category": "volatility",
            "param_space": {"window": [5, 30]},
        }
        # Mock the underlying computation so we don't need Qlib data
        import optuna

        def fake_objective(trial):
            trial.suggest_int("window", 5, 30)
            return 0.05

        with patch.object(evaluator, "_get_fast_screening_universe", return_value=["SH600000"]):
            with patch("optuna.create_study") as mock_study_fn:
                mock_study = MagicMock()
                mock_study.best_value = 0.05
                mock_study.best_params = {"window": 20}
                mock_study_fn.return_value = mock_study
                result = evaluator._optimize_params(candidate)

        assert "params" in result
        assert result["params"]["window"] == 20

    def test_optimize_params_returns_original_on_zero_best_value(self, evaluator):
        """If all Optuna trials return 0, original candidate is returned unchanged."""
        candidate = {
            "name": "py_noop",
            "source": "python",
            "code": "return df['close']",
            "category": "momentum",
            "param_space": {"window": [5, 20]},
        }
        with patch.object(evaluator, "_get_fast_screening_universe", return_value=["SH600000"]):
            with patch("optuna.create_study") as mock_study_fn:
                mock_study = MagicMock()
                mock_study.best_value = 0.0
                mock_study_fn.return_value = mock_study
                result = evaluator._optimize_params(candidate)

        # best_value == 0.0 → original candidate returned
        assert result is candidate


class TestPythonFactorDispatch:
    """Tests for dual-dispatch: DSL vs Python factor evaluation paths."""

    def test_clean_factor_dict_allows_new_keys(self):
        """New Python/logic-guided keys survive _clean_factor_dict."""
        from mining.evaluator import _clean_factor_dict
        candidate = {
            "name": "test",
            "expression": "Rank($close)",
            "category": "momentum",
            "source": "python",
            "code": "return df['close'].rank()",
            "code_path": "storage/python_factors/logic_001/v1.py",
            "type": "python",
            "params": {"window": 20},
            "param_space": {"window": [10, 20, 30]},
            "logic_id": "logic_001",
            "lineage": ["logic_001_v0", "logic_001_v1"],
            # These should be stripped
            "_factor_values": "should_be_removed",
            "_lib_correlations": "should_be_removed",
        }
        cleaned = _clean_factor_dict(candidate)
        # All new keys present
        for key in ["source", "code", "code_path", "type", "params",
                     "param_space", "logic_id", "lineage"]:
            assert key in cleaned, f"Key '{key}' missing from cleaned dict"
        # Internal keys stripped
        assert "_factor_values" not in cleaned
        assert "_lib_correlations" not in cleaned

    def test_is_python_candidate_source(self):
        """_is_python_candidate detects source='python'."""
        from mining.evaluator import _is_python_candidate
        assert _is_python_candidate({"source": "python", "code": "x"}) is True
        assert _is_python_candidate({"source": "dsl", "expression": "X"}) is False

    def test_is_python_candidate_type(self):
        """_is_python_candidate detects type='python'."""
        from mining.evaluator import _is_python_candidate
        assert _is_python_candidate({"type": "python", "code": "x"}) is True
        assert _is_python_candidate({"type": "dsl", "expression": "X"}) is False

    def test_is_python_candidate_dsl_default(self):
        """DSL candidates (no source/type) are not Python."""
        from mining.evaluator import _is_python_candidate
        assert _is_python_candidate({"expression": "Rank($close)"}) is False

    def test_candidate_cache_key_dsl(self):
        """DSL candidates use expression as cache key."""
        from mining.evaluator import _candidate_cache_key
        c = {"expression": "Rank($close)", "name": "test"}
        assert _candidate_cache_key(c) == "Rank($close)"

    def test_candidate_cache_key_python(self):
        """Python candidates use first 100 chars of code as cache key."""
        from mining.evaluator import _candidate_cache_key
        code = "return df['close'].rolling(20).std()"
        c = {"source": "python", "code": code, "name": "test"}
        assert _candidate_cache_key(c) == code

    def test_candidate_cache_key_python_long_code(self):
        """Long Python code is truncated to 100 chars for cache key."""
        from mining.evaluator import _candidate_cache_key
        code = "x" * 200
        c = {"source": "python", "code": code, "name": "test"}
        assert len(_candidate_cache_key(c)) == 100

    def test_python_candidate_validation_valid(self, evaluator):
        """Python candidate with valid code passes validation in evaluate_batch."""
        candidates = [{
            "name": "py_factor",
            "source": "python",
            "code": "return df['close'].rolling(20).std()",
            "category": "volatility",
        }]
        # Mock all pipeline stages since we only test validation dispatch
        with patch.object(evaluator, "_fast_ic_screening", return_value=candidates) as mock_s1, \
             patch.object(evaluator, "_batch_dedup", return_value=candidates), \
             patch.object(evaluator, "_correlation_check", return_value=(candidates, [])), \
             patch.object(evaluator, "_replacement_check", return_value=[]), \
             patch.object(evaluator, "_compute_report_cards", return_value=(candidates, [])):
            result = evaluator.evaluate_batch(candidates)
            # Should pass validation (not rejected as invalid)
            assert len(result.screened) == 1
            assert result.screened[0]["name"] == "py_factor"

    def test_python_candidate_validation_syntax_error(self, evaluator):
        """Python candidate with syntax error fails validation."""
        candidates = [{
            "name": "bad_py",
            "source": "python",
            "code": "def broken(:\n  return x",
            "category": "other",
        }]
        result = evaluator.evaluate_batch(candidates)
        # Should be rejected with validation_error
        assert len(result.rejected) == 1
        assert "validation_error" in result.rejected[0]

    def test_python_candidate_validation_forbidden_import(self, evaluator):
        """Python candidate with forbidden import fails validation."""
        candidates = [{
            "name": "unsafe_py",
            "source": "python",
            "code": "import os\nreturn df['close']",
            "category": "other",
        }]
        result = evaluator.evaluate_batch(candidates)
        assert len(result.rejected) == 1
        assert "validation_error" in result.rejected[0]

    def test_compute_factor_dispatches_to_qlib(self, evaluator):
        """_compute_factor routes DSL candidates to _compute_factor_qlib."""
        candidate = {"name": "F1", "expression": "Rank($close)", "category": "momentum"}
        mock_df = pd.DataFrame({"factor": [1, 2, 3]})
        with patch.object(evaluator, "_compute_factor_qlib", return_value=mock_df) as mock_qlib:
            result = evaluator._compute_factor(candidate, ["SH600000"], "2023-01-01", "2023-12-31")
            mock_qlib.assert_called_once_with("Rank($close)", ["SH600000"], "2023-01-01", "2023-12-31")
            assert result is mock_df

    def test_compute_factor_dispatches_to_python(self, evaluator):
        """_compute_factor routes Python candidates to _compute_factor_python."""
        candidate = {
            "name": "F1", "source": "python",
            "code": "return df['close']", "category": "momentum",
        }
        mock_df = pd.DataFrame({"factor": [1, 2, 3]})
        with patch.object(evaluator, "_compute_factor_python", return_value=mock_df) as mock_py:
            result = evaluator._compute_factor(candidate, ["SH600000"], "2023-01-01", "2023-12-31")
            mock_py.assert_called_once_with(candidate, ["SH600000"], "2023-01-01", "2023-12-31")
            assert result is mock_df

    def test_mixed_batch_validation(self, evaluator):
        """Batch with both DSL and Python candidates validates each correctly."""
        candidates = [
            {"name": "dsl_ok", "expression": "Rank($close)", "category": "momentum"},
            {"name": "py_ok", "source": "python", "code": "return df['close']", "category": "momentum"},
            {"name": "py_bad", "source": "python", "code": "def bad(:", "category": "other"},
        ]
        # Mock pipeline stages for candidates that pass validation
        with patch.object(evaluator, "_fast_ic_screening", side_effect=lambda c: c), \
             patch.object(evaluator, "_batch_dedup", side_effect=lambda c: c), \
             patch.object(evaluator, "_correlation_check", return_value=([], [])), \
             patch.object(evaluator, "_replacement_check", return_value=[]), \
             patch.object(evaluator, "_compute_report_cards", return_value=([], [])):
            result = evaluator.evaluate_batch(candidates)
            # py_bad should be rejected at validation; dsl_ok and py_ok should pass
            rejected_names = [c["name"] for c in result.rejected if "validation_error" in c]
            assert "py_bad" in rejected_names

    def test_optimize_params_wired_into_evaluate_batch(self, evaluator):
        """evaluate_batch calls _optimize_params for Python candidates with param_space."""
        candidate = {
            "name": "py_opt",
            "source": "python",
            "code": "return df['close'].rolling(params['window']).std()",
            "category": "volatility",
            "param_space": {"window": [5, 30]},
        }
        optimized = {**candidate, "params": {"window": 20}}

        with patch.object(evaluator, "_optimize_params", return_value=optimized) as mock_opt, \
             patch.object(evaluator, "_fast_ic_screening", return_value=[optimized]), \
             patch.object(evaluator, "_batch_dedup", return_value=[optimized]), \
             patch.object(evaluator, "_correlation_check", return_value=([optimized], [])), \
             patch.object(evaluator, "_replacement_check", return_value=[]), \
             patch.object(evaluator, "_compute_report_cards", return_value=([optimized], [])):
            result = evaluator.evaluate_batch([candidate])
            mock_opt.assert_called_once()
            assert result.screened[0].get("params", {}).get("window") == 20

    def test_optimize_params_skipped_for_dsl(self, evaluator):
        """evaluate_batch does NOT call _optimize_params for DSL candidates."""
        candidate = {
            "name": "dsl_f",
            "expression": "Rank($close)",
            "category": "momentum",
            "param_space": {"window": [5, 30]},  # param_space present but DSL
        }

        with patch.object(evaluator, "_optimize_params") as mock_opt, \
             patch.object(evaluator, "_fast_ic_screening", return_value=[candidate]), \
             patch.object(evaluator, "_batch_dedup", return_value=[candidate]), \
             patch.object(evaluator, "_correlation_check", return_value=([candidate], [])), \
             patch.object(evaluator, "_replacement_check", return_value=[]), \
             patch.object(evaluator, "_compute_report_cards", return_value=([candidate], [])):
            evaluator.evaluate_batch([candidate])
            mock_opt.assert_not_called()

    def test_stage1_uses_compute_factor_for_python(self, evaluator):
        """Stage 1 calls _compute_factor (not _compute_factor_qlib) for Python candidates."""
        dates = pd.bdate_range("2023-01-02", periods=20)
        instruments = [f"SH60000{i}" for i in range(5)]
        idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
        np.random.seed(42)
        signal = np.random.randn(len(idx))

        candidates = [{
            "name": "py_f", "source": "python",
            "code": "return df['close']", "category": "momentum",
        }]

        with patch.object(evaluator, "_compute_factor") as mock_cf, \
             patch.object(evaluator, "_get_returns_qlib") as mock_ret, \
             patch.object(evaluator, "_get_full_universe", return_value=instruments), \
             patch.object(evaluator, "_stage1_window", return_value=("2022-01-01", "2022-12-31")):
            mock_cf.return_value = pd.DataFrame({"factor": signal}, index=idx)
            mock_ret.return_value = pd.DataFrame(
                {"$returns_1d": signal + np.random.randn(len(idx)) * 0.2}, index=idx)
            evaluator._fast_ic_screening(candidates)
            # Verify _compute_factor was called with the full candidate dict
            mock_cf.assert_called_once()
            call_args = mock_cf.call_args
            assert call_args[0][0] is candidates[0]  # candidate dict
