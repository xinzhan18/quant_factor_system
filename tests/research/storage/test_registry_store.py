"""Tests for RegistryStore (factor index, factor detail, family registry)."""

from __future__ import annotations

from pathlib import Path

from research.storage.paths import StoragePaths
from research.storage.registry_store import RegistryStore


def _make_store(tmp_path: Path) -> RegistryStore:
    sp = StoragePaths(tmp_path / "s")
    sp.ensure_dirs()
    return RegistryStore(sp)


class TestFactorIndex:

    def test_empty_index(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        assert store.load_factor_index() == {}

    def test_upsert_insert(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.upsert_factor_entry("F013", {"name": "breakout_10", "logic_id": "L021"})
        index = store.load_factor_index()
        assert len(index["factors"]) == 1
        assert index["factors"][0]["factor_id"] == "F013"
        assert index["factors"][0]["name"] == "breakout_10"

    def test_upsert_update(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.upsert_factor_entry("F013", {"name": "v1"})
        store.upsert_factor_entry("F013", {"name": "v2"})
        index = store.load_factor_index()
        assert len(index["factors"]) == 1
        assert index["factors"][0]["name"] == "v2"

    def test_remove_entry(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.upsert_factor_entry("F013", {"name": "a"})
        store.upsert_factor_entry("F014", {"name": "b"})
        store.remove_factor_entry("F013")
        assert store.list_factor_ids() == ["F014"]

    def test_list_factor_ids(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.upsert_factor_entry("F001", {"name": "a"})
        store.upsert_factor_entry("F002", {"name": "b"})
        assert store.list_factor_ids() == ["F001", "F002"]


class TestFactorDetail:

    def test_save_and_load(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        detail = {
            "name": "compression_rank_breakout_10",
            "logic_id": "L021",
            "metrics": {"ic_mean_oos": 0.013},
        }
        store.save_factor_detail("F013", detail)
        loaded = store.load_factor_detail("F013")
        assert loaded["factor_id"] == "F013"
        assert loaded["metrics"]["ic_mean_oos"] == 0.013

    def test_delete(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.save_factor_detail("F013", {"name": "test"})
        store.delete_factor_detail("F013")
        assert store.load_factor_detail("F013") == {}

    def test_delete_nonexistent(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.delete_factor_detail("F999")  # should not raise


class TestFamilyRegistry:

    def test_empty_registry(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        assert store.load_family_registry() == {}

    def test_upsert_family(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.upsert_family("FM_breakout", {"name": "breakout", "logic_ids": ["L021"]})
        reg = store.load_family_registry()
        assert len(reg["families"]) == 1
        assert reg["families"][0]["family_id"] == "FM_breakout"

    def test_upsert_updates_existing(self, tmp_path: Path) -> None:
        store = _make_store(tmp_path)
        store.upsert_family("FM_breakout", {"name": "v1"})
        store.upsert_family("FM_breakout", {"name": "v2"})
        reg = store.load_family_registry()
        assert len(reg["families"]) == 1
        assert reg["families"][0]["name"] == "v2"
