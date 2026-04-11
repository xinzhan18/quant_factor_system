"""Tests for yaml_io: load_yaml / load_yaml_unsafe / save_yaml.

Covers safe/unsafe load variants, atomic-write semantics, and crash-safety
(no leftover temp files on failure).
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from research.storage.yaml_io import (
    load_yaml,
    load_yaml_any,
    load_yaml_unsafe,
    save_yaml,
)


class TestLoadYamlSafe:
    """Verify safe load_yaml edge cases."""

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        assert load_yaml(tmp_path / "nope.yaml") == {}

    def test_empty_file_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / "empty.yaml"
        p.write_text("", encoding="utf-8")
        assert load_yaml(p) == {}

    def test_whitespace_only_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / "ws.yaml"
        p.write_text("   \n  \n", encoding="utf-8")
        assert load_yaml(p) == {}

    def test_null_content_returns_empty(self, tmp_path: Path) -> None:
        p = tmp_path / "null.yaml"
        p.write_text("null\n", encoding="utf-8")
        assert load_yaml(p) == {}

    def test_normal_dict(self, tmp_path: Path) -> None:
        p = tmp_path / "d.yaml"
        p.write_text("a: 1\nb: hello\n", encoding="utf-8")
        assert load_yaml(p) == {"a": 1, "b": "hello"}

    def test_non_dict_wrapped_in_raw(self, tmp_path: Path) -> None:
        p = tmp_path / "list.yaml"
        p.write_text("- one\n- two\n", encoding="utf-8")
        assert load_yaml(p) == {"_raw": ["one", "two"]}


class TestLoadYamlAny:
    """``load_yaml_any`` returns the raw parse without coercion."""

    def test_list_returned_raw(self, tmp_path: Path) -> None:
        p = tmp_path / "list.yaml"
        p.write_text("- one\n- two\n", encoding="utf-8")
        assert load_yaml_any(p) == ["one", "two"]

    def test_scalar_returned_raw(self, tmp_path: Path) -> None:
        p = tmp_path / "scalar.yaml"
        p.write_text("42\n", encoding="utf-8")
        assert load_yaml_any(p) == 42


class TestLoadYamlUnsafe:
    """Verify unsafe loading accepts pickled Python objects (result.yaml use case)."""

    def test_roundtrip_basic_dict(self, tmp_path: Path) -> None:
        p = tmp_path / "u.yaml"
        data = {"key": "value", "n": 1}
        save_yaml(p, data)
        assert load_yaml_unsafe(p) == data

    def test_missing_returns_empty(self, tmp_path: Path) -> None:
        assert load_yaml_unsafe(tmp_path / "missing.yaml") == {}

    def test_unsafe_can_load_python_tuple(self, tmp_path: Path) -> None:
        """safe_load cannot deserialize !!python/tuple; unsafe_load can."""
        p = tmp_path / "tup.yaml"
        # Write a YAML stream that safe_load would reject
        p.write_text(
            "items: !!python/tuple\n- 1\n- 2\n- 3\n",
            encoding="utf-8",
        )
        result = load_yaml_unsafe(p)
        assert result == {"items": (1, 2, 3)}

    def test_non_dict_wrapped_in_raw(self, tmp_path: Path) -> None:
        p = tmp_path / "list.yaml"
        p.write_text("- a\n- b\n", encoding="utf-8")
        assert load_yaml_unsafe(p) == {"_raw": ["a", "b"]}


class TestSaveYaml:
    """Verify save_yaml atomicity and correctness."""

    def test_basic_roundtrip(self, tmp_path: Path) -> None:
        p = tmp_path / "rt.yaml"
        data = {"key": "value", "number": 42}
        save_yaml(p, data)
        assert load_yaml(p) == data

    def test_creates_parent_dirs(self, tmp_path: Path) -> None:
        p = tmp_path / "a" / "b" / "c.yaml"
        save_yaml(p, {"x": 1})
        assert p.exists()
        assert load_yaml(p) == {"x": 1}

    def test_overwrite_existing(self, tmp_path: Path) -> None:
        p = tmp_path / "ow.yaml"
        save_yaml(p, {"v": 1})
        save_yaml(p, {"v": 2})
        assert load_yaml(p) == {"v": 2}

    def test_unicode_content(self, tmp_path: Path) -> None:
        p = tmp_path / "uni.yaml"
        data = {"name": "压缩突破", "notes": "中文注释"}
        save_yaml(p, data)
        assert load_yaml(p) == data

    def test_no_temp_files_left_on_success(self, tmp_path: Path) -> None:
        p = tmp_path / "clean.yaml"
        save_yaml(p, {"ok": True})
        tmp_files = list(tmp_path.glob(".tmp_*"))
        assert tmp_files == [], f"temp files left behind: {tmp_files}"

    def test_nested_structure(self, tmp_path: Path) -> None:
        p = tmp_path / "nested.yaml"
        data = {
            "level1": {"level2": [1, 2, 3], "flag": True},
            "items": [{"a": 1}, {"b": 2}],
        }
        save_yaml(p, data)
        assert load_yaml(p) == data

    def test_preserves_insertion_order(self, tmp_path: Path) -> None:
        """sort_keys=False means dict insertion order survives roundtrip."""
        p = tmp_path / "ord.yaml"
        save_yaml(p, {"z": 1, "a": 2, "m": 3})
        text = p.read_text(encoding="utf-8")
        # z should appear before a before m in the serialized form
        assert text.index("z:") < text.index("a:") < text.index("m:")

    def test_crash_mid_write_leaves_no_tempfile(self, tmp_path: Path) -> None:
        """If os.replace fails, the temp file must be cleaned up."""
        p = tmp_path / "crash.yaml"
        with patch("os.replace", side_effect=OSError("boom")):
            with pytest.raises(OSError, match="boom"):
                save_yaml(p, {"oops": 1})
        # Target never written
        assert not p.exists()
        # No leftover temp files in the directory
        leftover = list(tmp_path.glob(".tmp_*"))
        assert leftover == [], f"leftover temp files: {leftover}"

    def test_crash_never_corrupts_existing_file(self, tmp_path: Path) -> None:
        """If save fails mid-write, the original file remains untouched."""
        p = tmp_path / "existing.yaml"
        save_yaml(p, {"v": "original"})
        assert load_yaml(p) == {"v": "original"}

        with patch("os.replace", side_effect=OSError("boom")):
            with pytest.raises(OSError):
                save_yaml(p, {"v": "new"})

        # Original content still intact
        assert load_yaml(p) == {"v": "original"}
