"""Tests for yaml_io load/save."""

from __future__ import annotations

from pathlib import Path

from research.storage.yaml_io import load_yaml, save_yaml


class TestLoadYaml:
    """Verify load_yaml edge cases."""

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
        result = load_yaml(p)
        assert result == {"_raw": ["one", "two"]}


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
        data = {"name": "compression breakout", "notes": "hello"}
        save_yaml(p, data)
        assert load_yaml(p) == data

    def test_no_temp_files_left(self, tmp_path: Path) -> None:
        p = tmp_path / "clean.yaml"
        save_yaml(p, {"ok": True})
        tmp_files = list(tmp_path.glob(".tmp_*"))
        assert tmp_files == [], f"temp files left behind: {tmp_files}"

    def test_nested_structure(self, tmp_path: Path) -> None:
        p = tmp_path / "nested.yaml"
        data = {
            "level1": {
                "level2": [1, 2, 3],
                "flag": True,
            },
            "items": [{"a": 1}, {"b": 2}],
        }
        save_yaml(p, data)
        assert load_yaml(p) == data
