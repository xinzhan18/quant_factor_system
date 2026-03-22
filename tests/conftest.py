"""Shared test fixtures for mining tests."""

import os
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from mining.config import MiningConfig


@pytest.fixture
def tmp_mining_dir(tmp_path):
    """Create temporary mining directory structure."""
    memory_dir = tmp_path / "memory" / "history"
    memory_dir.mkdir(parents=True)
    library_dir = tmp_path / "library" / "factors"
    library_dir.mkdir(parents=True)
    candidates_dir = tmp_path / "candidates"
    candidates_dir.mkdir(parents=True)
    return tmp_path


@pytest.fixture
def config(tmp_mining_dir):
    """MiningConfig pointing to temp directories."""
    return MiningConfig(
        memory_dir=str(tmp_mining_dir / "memory"),
        library_dir=str(tmp_mining_dir / "library"),
        candidates_dir=str(tmp_mining_dir / "candidates"),
        train_start="2023-01-01",
        train_end="2023-12-31",
        test_start="2024-01-01",
        test_end="2024-06-30",
    )


@pytest.fixture
def sample_factor_values():
    """Sample factor values DataFrame (date x instrument MultiIndex)."""
    dates = pd.bdate_range("2023-01-02", periods=60)
    instruments = [f"SH60000{i}" for i in range(10)]
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    np.random.seed(42)
    return pd.DataFrame({"factor": np.random.randn(len(idx))}, index=idx)


@pytest.fixture
def sample_returns():
    """Sample returns DataFrame matching sample_factor_values index."""
    dates = pd.bdate_range("2023-01-02", periods=60)
    instruments = [f"SH60000{i}" for i in range(10)]
    idx = pd.MultiIndex.from_product([dates, instruments], names=["datetime", "instrument"])
    np.random.seed(123)
    return pd.DataFrame({"$returns_1d": np.random.randn(len(idx)) * 0.02}, index=idx)
