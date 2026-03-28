"""Tests for direction file management in ExperienceMemory."""

import tempfile
from pathlib import Path

import pytest
import yaml


def _make_memory(tmp_path):
    """Create ExperienceMemory with temp directory."""
    from mining.config import MiningConfig
    from mining.memory import ExperienceMemory

    config = MiningConfig(memory_dir=str(tmp_path))
    return ExperienceMemory(config)


def test_list_directions_empty(tmp_path):
    mem = _make_memory(tmp_path)
    assert mem.list_directions() == []


def test_write_and_read_direction(tmp_path):
    mem = _make_memory(tmp_path)
    mem.write_direction("test_dir", {
        "name": "test_dir",
        "status": "new",
        "category": "volatility",
        "source": "manual",
        "parent_factor": None,
        "attempts": 0,
        "best_ic": None,
        "last_batch": None,
        "priority": "medium",
        "created": "2026-03-28",
    }, body="Test direction.\n\n## Rationale\nTesting.\n")

    dirs = mem.list_directions()
    assert len(dirs) == 1
    assert dirs[0]["name"] == "test_dir"
    assert dirs[0]["status"] == "new"

    meta, body = mem.read_direction("test_dir")
    assert meta["status"] == "new"
    assert meta["category"] == "volatility"
    assert "## Rationale" in body


def test_update_direction_frontmatter(tmp_path):
    mem = _make_memory(tmp_path)
    mem.write_direction("test_dir", {
        "name": "test_dir",
        "status": "new",
        "category": "volatility",
        "source": "manual",
        "attempts": 0,
        "best_ic": None,
        "last_batch": None,
        "priority": "medium",
        "created": "2026-03-28",
    }, body="Initial body.\n")

    mem.update_direction("test_dir", status="active", attempts=1, best_ic=-0.045)

    meta, body = mem.read_direction("test_dir")
    assert meta["status"] == "active"
    assert meta["attempts"] == 1
    assert meta["best_ic"] == -0.045
    assert "Initial body" in body


def test_append_to_direction_body(tmp_path):
    mem = _make_memory(tmp_path)
    mem.write_direction("test_dir", {
        "name": "test_dir",
        "status": "active",
        "category": "volatility",
        "source": "manual",
        "attempts": 0,
        "best_ic": None,
        "last_batch": None,
        "priority": "medium",
        "created": "2026-03-28",
    }, body="Body.\n\n## Probe Records\n")

    mem.append_to_direction("test_dir", "\n- batch_019: IC=-0.038, probed 2026-03-28\n")

    _, body = mem.read_direction("test_dir")
    assert "batch_019: IC=-0.038" in body


def test_directions_yaml_index_sync(tmp_path):
    mem = _make_memory(tmp_path)
    mem.write_direction("dir_a", {
        "name": "dir_a", "status": "active", "category": "vol",
        "source": "manual", "attempts": 2, "best_ic": -0.04,
        "last_batch": "batch_019", "priority": "high", "created": "2026-03-28",
    }, body="A")
    mem.write_direction("dir_b", {
        "name": "dir_b", "status": "dead", "category": "trend",
        "source": "search", "attempts": 5, "best_ic": -0.008,
        "last_batch": "batch_017", "priority": "none", "created": "2026-03-28",
    }, body="B")

    index = mem.list_directions()
    assert len(index) == 2
    names = {d["name"] for d in index}
    assert names == {"dir_a", "dir_b"}
