"""Tests for conftest fixtures."""

from mining.config import MiningConfig


def test_config_fixture(config):
    """Test that config fixture is properly set up."""
    assert isinstance(config, MiningConfig)
    assert config.train_start == "2023-01-01"
    assert config.train_end == "2023-12-31"
    assert config.test_start == "2024-01-01"
    assert config.test_end == "2024-06-30"
    assert "memory" in config.memory_dir
    assert "library" in config.library_dir
    assert "candidates" in config.candidates_dir


def test_tmp_mining_dir_fixture(tmp_mining_dir):
    """Test that tmp_mining_dir fixture creates proper structure."""
    assert (tmp_mining_dir / "memory" / "history").exists()
    assert (tmp_mining_dir / "library" / "factors").exists()
    assert (tmp_mining_dir / "candidates").exists()


def test_sample_factor_values(sample_factor_values):
    """Test that sample_factor_values fixture provides correct shape."""
    assert len(sample_factor_values) == 600  # 60 dates * 10 instruments
    assert "factor" in sample_factor_values.columns
    assert sample_factor_values.index.nlevels == 2
    assert sample_factor_values.index.names == ["datetime", "instrument"]


def test_sample_returns(sample_returns):
    """Test that sample_returns fixture provides correct shape."""
    assert len(sample_returns) == 600  # 60 dates * 10 instruments
    assert "$returns_1d" in sample_returns.columns
    assert sample_returns.index.nlevels == 2
    assert sample_returns.index.names == ["datetime", "instrument"]
