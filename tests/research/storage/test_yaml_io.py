"""Tests for research.storage.yaml_io."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from research.storage.yaml_io import load_yaml, load_yaml_unsafe, save_yaml


class TestLoadYaml:
    """Tests for load_yaml (safe)."""

    def test_missing_file_returns_empty(self, tmp_path: Path):
        result = load_yaml(tmp_path / "nope.yaml")
        assert result == {}

    def test_empty_file_returns_empty(self, tmp_path: Path):
        f = tmp_path / "empty.yaml"
        f.write_text("", encoding="utf-8")
        assert load_yaml(f) == {}

    def test_whitespace_only_returns_empty(self, tmp_path: Path):
        f = tmp_path / "ws.yaml"
        f.write_text("   \n\n  ", encoding="utf-8")
        assert load_yaml(f) == {}

    def test_non_dict_returns_empty(self, tmp_path: Path):
        f = tmp_path / "list.yaml"
        f.write_text("- a\n- b\n", encoding="utf-8")
        assert load_yaml(f) == {}

    def test_round_trip(self, tmp_path: Path):
        data = {"key": "value", "nested": {"x": 1}}
        f = tmp_path / "data.yaml"
        f.write_text(yaml.safe_dump(data), encoding="utf-8")
        assert load_yaml(f) == data

    def test_unicode(self, tmp_path: Path):
        data = {"name": "compression_breakout"}
        f = tmp_path / "uni.yaml"
        f.write_text(yaml.safe_dump(data, allow_unicode=True), encoding="utf-8")
        assert load_yaml(f) == data


class TestSaveYaml:
    """Tests for save_yaml (atomic)."""

    def test_creates_parent_dirs(self, tmp_path: Path):
        target = tmp_path / "a" / "b" / "c.yaml"
        save_yaml(target, {"hello": "world"})
        assert target.exists()
        assert load_yaml(target) == {"hello": "world"}

    def test_overwrites_existing(self, tmp_path: Path):
        f = tmp_path / "overwrite.yaml"
        save_yaml(f, {"v": 1})
        save_yaml(f, {"v": 2})
        assert load_yaml(f) == {"v": 2}

    def test_no_temp_file_left_on_success(self, tmp_path: Path):
        f = tmp_path / "clean.yaml"
        save_yaml(f, {"ok": True})
        temps = list(tmp_path.glob(".clean.yaml.*"))
        assert temps == []

    def test_atomic_on_error(self, tmp_path: Path):
        """If something goes wrong during dump, the original file stays."""
        f = tmp_path / "orig.yaml"
        save_yaml(f, {"original": True})

        # Attempt to save an object that yaml.safe_dump cannot handle.
        class Unpicklable:
            pass

        try:
            save_yaml(f, {"bad": Unpicklable()})
        except Exception:
            pass

        # Original must still be intact.
        assert load_yaml(f) == {"original": True}


class TestLoadYamlUnsafe:
    """Tests for load_yaml_unsafe."""

    def test_missing_file_returns_empty(self, tmp_path: Path):
        assert load_yaml_unsafe(tmp_path / "nope.yaml") == {}

    def test_loads_standard_dict(self, tmp_path: Path):
        f = tmp_path / "data.yaml"
        f.write_text(yaml.safe_dump({"a": 1}), encoding="utf-8")
        assert load_yaml_unsafe(f) == {"a": 1}
