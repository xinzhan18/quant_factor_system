"""Tests for MiningConfig."""

import pytest
from mining.config import MiningConfig


def test_default_config():
    cfg = MiningConfig()
    assert cfg.ic_threshold == 0.01
    assert cfg.correlation_threshold == 0.7
    assert cfg.replacement_ic_ratio == 1.3
    assert cfg.candidates_per_batch == 8
    assert cfg.universe == "all"
    assert cfg.custom_universe is None
    assert cfg.max_expression_depth == 10
    # Time window defaults
    assert cfg.train_end == "2023-12-31"
    assert cfg.test_start == "2024-01-01"
    assert cfg.test_end == "2024-12-31"


def test_time_window_overlap_raises():
    """test_start must be after train_end."""
    with pytest.raises(ValueError, match="must be after"):
        MiningConfig(train_end="2024-12-31", test_start="2024-07-01")


def test_time_window_start_exceeds_end_raises():
    """test_start must not exceed test_end."""
    with pytest.raises(ValueError, match="must not exceed"):
        MiningConfig(train_end="2023-12-31", test_start="2025-01-01",
                     test_end="2024-12-31")


def test_valid_time_window_ok():
    cfg = MiningConfig(train_end="2023-12-31", test_start="2024-01-01",
                       test_end="2024-12-31")
    assert cfg.train_end == "2023-12-31"
    assert cfg.test_start == "2024-01-01"
    assert cfg.test_end == "2024-12-31"


def test_custom_config():
    cfg = MiningConfig(ic_threshold=0.05, universe="custom", custom_universe=["SH600000", "SZ000001"])
    assert cfg.ic_threshold == 0.05
    assert cfg.universe == "custom"
    assert len(cfg.custom_universe) == 2


def test_categories():
    cfg = MiningConfig()
    assert "vwap" in cfg.categories
    assert "momentum" in cfg.categories
    assert "other" in cfg.categories
    assert len(cfg.categories) == 11


def test_base_fields():
    cfg = MiningConfig()
    assert "$close" in cfg.base_fields
    assert "$vwap" in cfg.base_fields
    assert "$returns" in cfg.base_fields


class TestNewConfigFields:
    def test_construction(self):
        cfg = MiningConfig()
        assert cfg is not None

    def test_optuna_defaults(self):
        cfg = MiningConfig()
        assert cfg.optuna_trials == 30
        assert cfg.optuna_timeout == 600

    def test_sandbox_defaults(self):
        cfg = MiningConfig()
        assert cfg.sandbox_timeout == 60
        assert cfg.sandbox_memory_limit_gb == 4

    def test_evolution_defaults(self):
        cfg = MiningConfig()
        assert cfg.max_mutations_per_factor == 5
        assert cfg.ast_similarity_threshold == 0.8

    def test_storage_path_defaults(self):
        cfg = MiningConfig()
        assert cfg.logic_dir == "storage/mining/logic"
        assert cfg.python_factors_dir == "storage/mining/python_factors"
        assert cfg.forbidden_file == "storage/mining/memory/forbidden.yaml"
        assert cfg.library_dir == "storage/registry"
        assert cfg.memory_dir == "storage/mining/memory"
        assert cfg.candidates_dir == "storage/mining/candidates"
        assert cfg.vault_dir == "storage/evidence/vault"
        assert cfg.lib_cache_dir == "storage/runtime/cache/lib_factors"

    def test_custom_values(self):
        cfg = MiningConfig(
            optuna_trials=50,
            optuna_timeout=300,
            sandbox_timeout=120,
            sandbox_memory_limit_gb=8,
            max_mutations_per_factor=10,
            ast_similarity_threshold=0.9,
            logic_dir="custom/logic",
            python_factors_dir="custom/python_factors",
            forbidden_file="custom/forbidden.yaml",
        )
        assert cfg.optuna_trials == 50
        assert cfg.optuna_timeout == 300
        assert cfg.sandbox_timeout == 120
        assert cfg.sandbox_memory_limit_gb == 8
        assert cfg.max_mutations_per_factor == 10
        assert cfg.ast_similarity_threshold == 0.9
        assert cfg.logic_dir == "custom/logic"
        assert cfg.python_factors_dir == "custom/python_factors"
        assert cfg.forbidden_file == "custom/forbidden.yaml"
