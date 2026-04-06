"""Tests for research.execute.batch_runner — YAML manifest loading and execution."""

import pytest
import yaml

from research.execute.batch_runner import BatchRunner, _strip_non_serializable


# ===================================================================
# _strip_non_serializable
# ===================================================================
class TestStripNonSerializable:
    def test_basic_types_pass_through(self):
        data = {"a": 1, "b": "hello", "c": True, "d": None, "e": 3.14}
        assert _strip_non_serializable(data) == data

    def test_nested_dicts(self):
        data = {"outer": {"inner": 42}}
        assert _strip_non_serializable(data) == data

    def test_lists(self):
        data = [1, "two", [3, 4]]
        assert _strip_non_serializable(data) == data

    def test_non_serializable_becomes_string(self):
        class Foo:
            def __str__(self):
                return "Foo()"
        result = _strip_non_serializable({"x": Foo()})
        assert result["x"] == "Foo()"


# ===================================================================
# Helpers for full callable injection
# ===================================================================

def _noop_signal(candidate, profile):
    return {
        "base_signal": None,
        "diagnostics": {"base_valid_ratio": 0.0, "base_variance": 0.0,
                        "base_outlier_ratio": 0.0, "base_skew": 0.0, "base_kurtosis": 0.0},
    }


def _noop_preprocess(base_result, profile):
    return {"evaluation_ready_signal": None, "factor_flat": None}


def _noop_stat(signal, sample_policy):
    return {
        "ic_mean_train": 0.0, "ic_ir_train": 0.0,
        "ic_mean_validation": 0.0, "ic_ir_validation": 0.0,
        "ic_win_rate_validation": 0.5, "monotonicity_validation": 0.0,
        "sign_consistency": True, "train_validation_decay_ratio": 1.0,
        "split_stability": "medium", "regime_stability": "medium",
        "horizon_consistency": "medium",
        "expanding_window_ic_stability": 0.5, "expanding_window_sign_consistency": 0.5,
        "expanding_window_pass": True,
        "bootstrap_stability_score": None, "bootstrap_sign_consistency": None,
        "purged_walk_forward_score": None, "purged_walk_forward_status": None,
        "multiple_testing_risk_bucket": "low", "search_adjusted_strength_bucket": "medium",
        "support_window_checks": [],
    }


def _noop_redundancy(signal, candidate):
    return {"max_lib_corr": 0.0, "nearest_factor_id": None,
            "is_near_duplicate": False,
            "family_overlap_score": 0.0, "subspace_redundancy_score": 0.0,
            "residual_incremental_ic": 0.0, "replacement_candidate_hint": False,
            "family_redundancy_view": {}, "subspace_redundancy_view": {}}


def _noop_feasibility(signal):
    return {"turnover": 0.3, "coverage": 0.9, "half_life": 5.0,
            "holding_period_proxy": "medium", "liquidity_coverage_ratio": 0.9,
            "tail_trade_concentration": 0.15, "small_cap_concentration": 0.25,
            "rebalance_stress_proxy": "low"}


def _mock_runner(batches_dir=None, **overrides):
    """Create a BatchRunner with all callables mocked (no Qlib needed)."""
    defaults = dict(
        compute_signal=_noop_signal,
        preprocess_signal=_noop_preprocess,
        compute_stat_evidence=_noop_stat,
        compute_redundancy=_noop_redundancy,
        compute_feasibility=_noop_feasibility,
    )
    defaults.update(overrides)
    return BatchRunner(batches_dir=batches_dir, **defaults)


# ===================================================================
# BatchRunner
# ===================================================================
class TestBatchRunner:
    def _write_manifest(self, tmp_path, batch_id="batch_001", candidates=None):
        if candidates is None:
            candidates = [
                {
                    "candidate_id": "C001",
                    "source_type": "dsl",
                    "expression": "Rank($close)",
                    "logic_id": "L001",
                    "route_id": "R001",
                    "family_id": "FM_test",
                    "route_type": "genesis",
                },
            ]
        manifest = {"batch_id": batch_id, "candidates": candidates}
        path = tmp_path / f"{batch_id}.yaml"
        with open(path, "w") as f:
            yaml.dump(manifest, f)
        return path

    def test_run_basic(self, tmp_path):
        path = self._write_manifest(tmp_path)
        runner = _mock_runner()
        result = runner.run(path)
        assert result["batch_id"] == "batch_001"
        assert len(result["candidate_results"]) == 1
        assert "judge_packet" in result

    def test_run_saves_results(self, tmp_path):
        batches_dir = tmp_path / "batches"
        path = self._write_manifest(tmp_path)
        runner = _mock_runner(batches_dir=str(batches_dir))
        runner.run(path)
        assert (batches_dir / "batch_001" / "research_result.yaml").exists()
        assert (batches_dir / "batch_001" / "judge_packet.yaml").exists()

    def test_run_with_search_context(self, tmp_path):
        path = self._write_manifest(tmp_path)
        ctx = {"validation_window_id": "val_2022_2023"}
        runner = _mock_runner()
        result = runner.run(path, search_context=ctx)
        assert result["candidate_results"][0]["search_context"] == ctx

    def test_run_empty_candidates(self, tmp_path):
        path = self._write_manifest(tmp_path, candidates=[])
        runner = _mock_runner()
        result = runner.run(path)
        assert result["summary"]["total_candidates"] == 0

    def test_missing_manifest_raises(self, tmp_path):
        runner = _mock_runner()
        with pytest.raises(FileNotFoundError):
            runner.run(tmp_path / "nonexistent.yaml")

    def test_manifest_missing_candidates_key_raises(self, tmp_path):
        path = tmp_path / "bad.yaml"
        with open(path, "w") as f:
            yaml.dump({"batch_id": "bad"}, f)
        runner = _mock_runner()
        with pytest.raises(ValueError, match="missing 'candidates' key"):
            runner.run(path)

    def test_multiple_candidates(self, tmp_path):
        candidates = [
            {
                "candidate_id": f"C{i:03d}",
                "source_type": "dsl",
                "expression": "Rank($close)",
                "logic_id": "L001",
                "route_id": "R001",
                "family_id": "FM_test",
                "route_type": "genesis",
            }
            for i in range(5)
        ]
        path = self._write_manifest(tmp_path, candidates=candidates)
        runner = _mock_runner()
        result = runner.run(path)
        assert len(result["candidate_results"]) == 5

    def test_batch_id_from_filename(self, tmp_path):
        manifest = {
            "candidates": [
                {
                    "candidate_id": "C001",
                    "source_type": "dsl",
                    "expression": "Rank($close)",
                }
            ]
        }
        path = tmp_path / "my_batch.yaml"
        with open(path, "w") as f:
            yaml.dump(manifest, f)
        runner = _mock_runner()
        result = runner.run(path)
        assert result["batch_id"] == "my_batch"

    def test_custom_compute_injected(self, tmp_path):
        """Verify that injected compute callables reach the pipeline."""
        called = {"signal": False, "stat": False}

        def custom_signal(candidate, profile):
            called["signal"] = True
            return _noop_signal(candidate, profile)

        def custom_stat(signal, sample_policy):
            called["stat"] = True
            return _noop_stat(signal, sample_policy)

        path = self._write_manifest(tmp_path)
        runner = _mock_runner(
            compute_signal=custom_signal,
            compute_stat_evidence=custom_stat,
        )
        runner.run(path)
        assert called["signal"]
        assert called["stat"]
