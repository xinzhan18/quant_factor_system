"""Tests for MiningConfig."""

from mining.config import MiningConfig


def test_default_config():
    cfg = MiningConfig()
    assert cfg.ic_threshold == 0.03
    assert cfg.correlation_threshold == 0.7
    assert cfg.replacement_ic_ratio == 1.3
    assert cfg.candidates_per_batch == 8
    assert cfg.universe == "all"
    assert cfg.custom_universe is None
    assert cfg.max_expression_depth == 10


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
