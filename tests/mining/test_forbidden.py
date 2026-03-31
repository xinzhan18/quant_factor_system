"""Tests for ExperienceMemory forbidden-region methods."""

from __future__ import annotations

import pytest

from mining.memory import ExperienceMemory


@pytest.fixture
def memory(tmp_path):
    mem_dir = tmp_path / "memory"
    mem_dir.mkdir()
    (mem_dir / "history").mkdir()
    (mem_dir / "directions").mkdir()
    (mem_dir / "state.yaml").write_text("library:\n  size: 0\n")
    (mem_dir / "directions.yaml").write_text("directions: []\n")
    (mem_dir / "forbidden.yaml").write_text("forbidden_regions: []\n")
    from mining.config import MiningConfig
    config = MiningConfig(memory_dir=str(mem_dir))
    return ExperienceMemory(config)


def test_read_empty(memory):
    """read_forbidden returns an empty list when no regions have been added."""
    assert memory.read_forbidden() == []


def test_add_and_read(memory):
    """add_forbidden persists a region that is returned by read_forbidden."""
    memory.add_forbidden("Std($volume, *) / Mean($volume, *)", "volume_cv saturated")
    regions = memory.read_forbidden()
    assert len(regions) == 1
    assert regions[0]["pattern"] == "Std($volume, *) / Mean($volume, *)"
    assert regions[0]["reason"] == "volume_cv saturated"
    assert "added" in regions[0]


def test_add_multiple(memory):
    """Multiple forbidden regions accumulate correctly."""
    memory.add_forbidden("Std($volume, *) / Mean($volume, *)", "volume_cv saturated")
    memory.add_forbidden("Corr($close, $volume, *)", "pv_corr saturated")
    regions = memory.read_forbidden()
    assert len(regions) == 2


def test_check_match(memory):
    """check_forbidden returns the reason when expression matches a pattern."""
    memory.add_forbidden("Std($volume, *) / Mean($volume, *)", "volume_cv saturated")
    reason = memory.check_forbidden("Std($volume, 20) / Mean($volume, 20)")
    assert reason == "volume_cv saturated"


def test_check_no_match(memory):
    """check_forbidden returns None when expression does not match any pattern."""
    memory.add_forbidden("Std($volume, *) / Mean($volume, *)", "volume_cv saturated")
    result = memory.check_forbidden("Corr($close, $volume, 20)")
    assert result is None


def test_check_python_pattern(memory):
    """check_forbidden works with Python-style expressions."""
    memory.add_forbidden(
        "ts_std($volume, *) / ts_mean($volume, *)",
        "python volume_cv saturated",
    )
    result = memory.check_forbidden("ts_std($volume, 20) / ts_mean($volume, 20)")
    assert result == "python volume_cv saturated"


def test_check_no_false_positive(memory):
    """Wildcard in pattern does not match across operator boundaries."""
    memory.add_forbidden("Std($volume, *)", "std volume forbidden")
    # A completely unrelated expression should not match
    result = memory.check_forbidden("Mean($close, 5)")
    assert result is None
