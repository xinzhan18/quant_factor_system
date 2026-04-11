"""Tests for FactorValueCache — content-addressed parquet cache."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from research.compute.cache import FactorValueCache


@pytest.fixture
def cache(tmp_path: Path) -> FactorValueCache:
    return FactorValueCache(tmp_path / "fv_cache")


@pytest.fixture
def sample_df() -> pd.DataFrame:
    idx = pd.MultiIndex.from_tuples(
        [
            (pd.Timestamp("2024-01-02"), "SH600000"),
            (pd.Timestamp("2024-01-02"), "SH600001"),
            (pd.Timestamp("2024-01-03"), "SH600000"),
            (pd.Timestamp("2024-01-03"), "SH600001"),
        ],
        names=["datetime", "instrument"],
    )
    return pd.DataFrame({"value": [1.0, 2.0, 3.0, 4.0]}, index=idx)


class TestMakeKey:
    def test_deterministic(self) -> None:
        k1 = FactorValueCache.make_key("Std($close,20)", "v3", "p1")
        k2 = FactorValueCache.make_key("Std($close,20)", "v3", "p1")
        assert k1 == k2

    def test_length_16_hex(self) -> None:
        k = FactorValueCache.make_key("Std($close,20)", "v3", "p1")
        assert len(k) == 16
        assert all(c in "0123456789abcdef" for c in k)

    def test_expression_changes_key(self) -> None:
        k1 = FactorValueCache.make_key("Std($close,20)", "v3", "p1")
        k2 = FactorValueCache.make_key("Std($close,30)", "v3", "p1")
        assert k1 != k2

    def test_sample_policy_version_changes_key(self) -> None:
        k1 = FactorValueCache.make_key("Std($close,20)", "v3", "p1")
        k2 = FactorValueCache.make_key("Std($close,20)", "v4", "p1")
        assert k1 != k2

    def test_preprocess_version_changes_key(self) -> None:
        k1 = FactorValueCache.make_key("Std($close,20)", "v3", "p1")
        k2 = FactorValueCache.make_key("Std($close,20)", "v3", "p2")
        assert k1 != k2


class TestCrud:
    def test_miss_returns_none(self, cache: FactorValueCache) -> None:
        assert cache.get("abcdef1234567890") is None

    def test_contains_on_miss(self, cache: FactorValueCache) -> None:
        assert cache.contains("abcdef1234567890") is False

    def test_put_get_roundtrip(
        self, cache: FactorValueCache, sample_df: pd.DataFrame
    ) -> None:
        key = FactorValueCache.make_key("Std($close,20)", "v3", "p1")
        cache.put(key, sample_df)
        loaded = cache.get(key)
        assert loaded is not None
        pd.testing.assert_frame_equal(loaded, sample_df)

    def test_contains_after_put(
        self, cache: FactorValueCache, sample_df: pd.DataFrame
    ) -> None:
        key = FactorValueCache.make_key("X", "v", "p")
        assert cache.contains(key) is False
        cache.put(key, sample_df)
        assert cache.contains(key) is True

    def test_invalidate_existing(
        self, cache: FactorValueCache, sample_df: pd.DataFrame
    ) -> None:
        key = FactorValueCache.make_key("X", "v", "p")
        cache.put(key, sample_df)
        assert cache.invalidate(key) is True
        assert cache.get(key) is None

    def test_invalidate_missing(self, cache: FactorValueCache) -> None:
        assert cache.invalidate("nonexistent") is False

    def test_clear_removes_all(
        self, cache: FactorValueCache, sample_df: pd.DataFrame
    ) -> None:
        for i in range(3):
            cache.put(FactorValueCache.make_key(f"X{i}", "v", "p"), sample_df)
        assert cache.size() == 3
        assert cache.clear() == 3
        assert cache.size() == 0

    def test_size_tracks_entries(
        self, cache: FactorValueCache, sample_df: pd.DataFrame
    ) -> None:
        assert cache.size() == 0
        cache.put(FactorValueCache.make_key("A", "v", "p"), sample_df)
        assert cache.size() == 1
        cache.put(FactorValueCache.make_key("B", "v", "p"), sample_df)
        assert cache.size() == 2


class TestAtomicWrite:
    def test_put_leaves_no_temp_file(
        self,
        cache: FactorValueCache,
        sample_df: pd.DataFrame,
    ) -> None:
        key = FactorValueCache.make_key("X", "v", "p")
        cache.put(key, sample_df)
        leftover = list(cache.cache_dir.glob("*.tmp"))
        assert leftover == []

    def test_overwrite_existing(
        self,
        cache: FactorValueCache,
        sample_df: pd.DataFrame,
    ) -> None:
        key = FactorValueCache.make_key("X", "v", "p")
        cache.put(key, sample_df)
        df2 = sample_df * 10
        cache.put(key, df2)
        loaded = cache.get(key)
        pd.testing.assert_frame_equal(loaded, df2)


class TestCacheDir:
    def test_creates_dir_on_construction(self, tmp_path: Path) -> None:
        target = tmp_path / "new" / "nested" / "cache"
        assert not target.exists()
        FactorValueCache(target)
        assert target.exists()
        assert target.is_dir()
