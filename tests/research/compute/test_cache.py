"""Tests for FactorValueCache -- parquet disk cache."""

from __future__ import annotations

import pandas as pd
import numpy as np
import pytest

from research.compute.cache import FactorValueCache


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


@pytest.fixture
def cache(tmp_path):
    """Create a FactorValueCache in a temp directory."""
    return FactorValueCache(cache_dir=str(tmp_path / "cache"))


@pytest.fixture
def sample_df():
    """Small DataFrame for cache round-trip tests."""
    idx = pd.MultiIndex.from_tuples(
        [
            (pd.Timestamp("2024-01-02"), "SH600000"),
            (pd.Timestamp("2024-01-02"), "SH600001"),
            (pd.Timestamp("2024-01-03"), "SH600000"),
            (pd.Timestamp("2024-01-03"), "SH600001"),
        ],
        names=["datetime", "instrument"],
    )
    return pd.DataFrame({"factor": [1.0, 2.0, 3.0, 4.0]}, index=idx)


# -----------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------


class TestFactorValueCache:
    def test_make_key_deterministic(self):
        k1 = FactorValueCache.make_key("Rank($close)", "2020-01-01", "2024-12-31")
        k2 = FactorValueCache.make_key("Rank($close)", "2020-01-01", "2024-12-31")
        assert k1 == k2
        assert len(k1) == 32  # MD5 hex digest

    def test_make_key_different_inputs(self):
        k1 = FactorValueCache.make_key("Rank($close)", "2020-01-01", "2024-12-31")
        k2 = FactorValueCache.make_key("Std($close, 20)", "2020-01-01", "2024-12-31")
        assert k1 != k2

    def test_get_miss(self, cache):
        result = cache.get("nonexistent_key")
        assert result is None

    def test_put_and_get(self, cache, sample_df):
        key = "test_key_123"
        cache.put(key, sample_df)
        result = cache.get(key)
        assert result is not None
        pd.testing.assert_frame_equal(result, sample_df)

    def test_invalidate_existing(self, cache, sample_df):
        key = "to_delete"
        cache.put(key, sample_df)
        assert cache.invalidate(key) is True
        assert cache.get(key) is None

    def test_invalidate_nonexistent(self, cache):
        assert cache.invalidate("never_stored") is False

    def test_clear(self, cache, sample_df):
        cache.put("a", sample_df)
        cache.put("b", sample_df)
        count = cache.clear()
        assert count == 2
        assert cache.get("a") is None
        assert cache.get("b") is None

    def test_size(self, cache, sample_df):
        assert cache.size() == 0
        cache.put("x", sample_df)
        assert cache.size() == 1
        cache.put("y", sample_df)
        assert cache.size() == 2

    def test_corrupt_file_removed(self, cache, tmp_path):
        """A corrupt parquet file should be removed and return None."""
        cache_dir = tmp_path / "cache"
        corrupt_path = cache_dir / "corrupt_key.parquet"
        corrupt_path.write_text("not a parquet file")
        result = cache.get("corrupt_key")
        assert result is None
        assert not corrupt_path.exists()

    def test_creates_directory(self, tmp_path):
        new_dir = tmp_path / "deeply" / "nested" / "cache"
        c = FactorValueCache(cache_dir=str(new_dir))
        assert new_dir.exists()
