"""Tests for research.storage.registry_store.RegistryStore."""

from __future__ import annotations

from pathlib import Path

from research.storage.paths import StoragePaths
from research.storage.registry_store import RegistryStore


def _make_store(tmp_path: Path) -> RegistryStore:
    paths = StoragePaths(root=str(tmp_path / "store"))
    paths.ensure_dirs()
    return RegistryStore(paths)


class TestFactorIndex:

    def test_load_empty(self, tmp_path: Path):
        store = _make_store(tmp_path)
        assert store.list_factors() == []

    def test_upsert_insert(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.save_factor_index({"factors": []})
        store.upsert_factor_entry({"factor_id": "F001", "name": "std_returns_20"})
        factors = store.list_factors()
        assert len(factors) == 1
        assert factors[0]["factor_id"] == "F001"

    def test_upsert_update(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.save_factor_index({
            "factors": [{"factor_id": "F001", "name": "old_name"}]
        })
        store.upsert_factor_entry({"factor_id": "F001", "name": "new_name"})
        factors = store.list_factors()
        assert len(factors) == 1
        assert factors[0]["name"] == "new_name"

    def test_remove_existing(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.save_factor_index({
            "factors": [
                {"factor_id": "F001"},
                {"factor_id": "F002"},
            ]
        })
        removed = store.remove_factor_entry("F001")
        assert removed is True
        assert len(store.list_factors()) == 1
        assert store.list_factors()[0]["factor_id"] == "F002"

    def test_remove_nonexistent(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.save_factor_index({"factors": []})
        assert store.remove_factor_entry("F999") is False


class TestFactorDetail:

    def test_round_trip(self, tmp_path: Path):
        store = _make_store(tmp_path)
        detail = {
            "factor_id": "F001",
            "name": "std_returns_20",
            "metrics": {"ic_mean_oos": 0.013},
        }
        store.save_factor_detail("001", detail)
        loaded = store.load_factor_detail("001")
        assert loaded == detail

    def test_list_detail_ids(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.save_factor_detail("001", {"factor_id": "F001"})
        store.save_factor_detail("002", {"factor_id": "F002"})
        ids = store.list_factor_detail_ids()
        assert ids == ["001", "002"]


class TestFamilyRegistry:

    def test_load_empty(self, tmp_path: Path):
        store = _make_store(tmp_path)
        assert store.list_families() == []

    def test_upsert_family(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.save_family_registry({"families": []})
        store.upsert_family({"family_id": "FM_breakout", "name": "breakout"})
        families = store.list_families()
        assert len(families) == 1
        assert families[0]["family_id"] == "FM_breakout"

    def test_upsert_family_update(self, tmp_path: Path):
        store = _make_store(tmp_path)
        store.save_family_registry({
            "families": [{"family_id": "FM_breakout", "count": 0}]
        })
        store.upsert_family({"family_id": "FM_breakout", "count": 3})
        families = store.list_families()
        assert len(families) == 1
        assert families[0]["count"] == 3
