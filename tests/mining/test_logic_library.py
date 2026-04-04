"""Tests for MarketLogicLibrary."""

import pytest
import yaml
from pathlib import Path

from mining.logic import MarketLogicLibrary


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def logic_dir(tmp_path):
    """Fresh temporary directory for logic YAML files."""
    d = tmp_path / "logic"
    d.mkdir()
    return d


@pytest.fixture
def library(logic_dir):
    return MarketLogicLibrary(str(logic_dir))


def _make_hypothesis():
    return {
        "condition": "Volume contracts while price range narrows",
        "behavior": "Subsequent breakout with volume expansion",
        "timeframe": "5-20 trading days",
        "direction": "long_on_breakout",
    }


def _make_constraints():
    return {
        "required_fields": ["volume", "close", "high", "low"],
        "suggested_ops": ["Std", "Mean", "CsRank"],
        "window_range": [5, 60],
    }


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCreateLogic:
    def test_create_logic_returns_record(self, library):
        record = library.create(
            name="volume_breakout",
            category="volume_price",
            hypothesis=_make_hypothesis(),
            constraints=_make_constraints(),
        )
        assert record["id"] == "L001"
        assert record["name"] == "volume_breakout"
        assert record["status"] == "active"
        assert record["category"] == "volume_price"
        assert "created" in record
        assert record["hypothesis"] == _make_hypothesis()
        assert record["constraints"] == _make_constraints()

    def test_create_logic_initializes_stats(self, library):
        record = library.create("vol_breakout", "volume_price", _make_hypothesis())
        stats = record["stats"]
        assert stats["factors_generated"] == 0
        assert stats["factors_admitted"] == 0
        assert stats["best_ic"] == 0.0
        assert stats["rounds_without_admit"] == 0

    def test_create_logic_persists_yaml_file(self, logic_dir, library):
        library.create("vol_breakout", "volume_price", _make_hypothesis())
        yaml_path = logic_dir / "L001.yaml"
        assert yaml_path.exists()
        with open(yaml_path, "r") as f:
            data = yaml.safe_load(f)
        assert data["id"] == "L001"

    def test_create_logic_without_constraints(self, library):
        record = library.create("minimal_logic", "volatility", _make_hypothesis())
        assert record["constraints"] == {}

    def test_create_logic_sequential_ids(self, library):
        r1 = library.create("logic_a", "volume_price", _make_hypothesis())
        r2 = library.create("logic_b", "volatility", _make_hypothesis())
        r3 = library.create("logic_c", "market_structure", _make_hypothesis())
        assert r1["id"] == "L001"
        assert r2["id"] == "L002"
        assert r3["id"] == "L003"


class TestGetLogic:
    def test_get_existing(self, library):
        library.create("vol_breakout", "volume_price", _make_hypothesis())
        record = library.get("L001")
        assert record is not None
        assert record["id"] == "L001"
        assert record["name"] == "vol_breakout"

    def test_get_nonexistent(self, library):
        result = library.get("L999")
        assert result is None


class TestListLogics:
    def test_list_logics_empty(self, library):
        assert library.list_logics() == []

    def test_list_logics_all(self, library):
        library.create("logic_a", "volume_price", _make_hypothesis())
        library.create("logic_b", "volatility", _make_hypothesis())
        result = library.list_logics()
        assert len(result) == 2

    def test_list_by_status_active(self, library):
        library.create("logic_a", "volume_price", _make_hypothesis())
        library.create("logic_b", "volatility", _make_hypothesis())
        library.update_status("L002", "exhausted")
        active = library.list_logics(status="active")
        assert len(active) == 1
        assert active[0]["id"] == "L001"

    def test_list_by_status_exhausted(self, library):
        library.create("logic_a", "volume_price", _make_hypothesis())
        library.create("logic_b", "volatility", _make_hypothesis())
        library.update_status("L001", "exhausted")
        library.update_status("L002", "exhausted")
        exhausted = library.list_logics(status="exhausted")
        assert len(exhausted) == 2

    def test_list_by_status_dead(self, library):
        library.create("logic_a", "volume_price", _make_hypothesis())
        dead = library.list_logics(status="dead")
        assert dead == []


class TestUpdateStats:
    def test_update_stats_single_field(self, library):
        library.create("vol_breakout", "volume_price", _make_hypothesis())
        library.update_stats("L001", factors_generated=5)
        record = library.get("L001")
        assert record["stats"]["factors_generated"] == 5

    def test_update_stats_multiple_fields(self, library):
        library.create("vol_breakout", "volume_price", _make_hypothesis())
        library.update_stats("L001", factors_generated=10, factors_admitted=3, best_ic=0.045)
        record = library.get("L001")
        assert record["stats"]["factors_generated"] == 10
        assert record["stats"]["factors_admitted"] == 3
        assert record["stats"]["best_ic"] == pytest.approx(0.045)

    def test_update_stats_incremental(self, library):
        library.create("vol_breakout", "volume_price", _make_hypothesis())
        library.update_stats("L001", rounds_without_admit=1)
        library.update_stats("L001", rounds_without_admit=2)
        record = library.get("L001")
        assert record["stats"]["rounds_without_admit"] == 2

    def test_update_stats_nonexistent_raises(self, library):
        with pytest.raises(KeyError):
            library.update_stats("L999", factors_generated=1)


class TestUpdateStatus:
    def test_update_status_transitions(self, library):
        library.create("vol_breakout", "volume_price", _make_hypothesis())
        library.update_status("L001", "exhausted")
        record = library.get("L001")
        assert record["status"] == "exhausted"

    def test_update_status_to_dead(self, library):
        library.create("vol_breakout", "volume_price", _make_hypothesis())
        library.update_status("L001", "dead")
        record = library.get("L001")
        assert record["status"] == "dead"

    def test_update_status_invalid_raises(self, library):
        library.create("vol_breakout", "volume_price", _make_hypothesis())
        with pytest.raises(ValueError):
            library.update_status("L001", "unknown_status")

    def test_update_status_nonexistent_raises(self, library):
        with pytest.raises(KeyError):
            library.update_status("L999", "active")


class TestCoverageMap:
    def test_coverage_map_empty(self, library):
        assert library.coverage_map() == {}

    def test_coverage_map_counts_active(self, library):
        library.create("logic_a", "volume_price", _make_hypothesis())
        library.create("logic_b", "volume_price", _make_hypothesis())
        library.create("logic_c", "volatility", _make_hypothesis())
        cmap = library.coverage_map()
        assert cmap["volume_price"] == 2
        assert cmap["volatility"] == 1

    def test_coverage_map_excludes_non_active(self, library):
        library.create("logic_a", "volume_price", _make_hypothesis())
        library.create("logic_b", "volume_price", _make_hypothesis())
        library.create("logic_c", "volatility", _make_hypothesis())
        library.update_status("L002", "exhausted")
        library.update_status("L003", "dead")
        cmap = library.coverage_map()
        assert cmap.get("volume_price") == 1
        assert "volatility" not in cmap

    def test_coverage_map_multiple_categories(self, library):
        categories = [
            "market_structure", "volume_price", "volatility",
            "microstructure", "cross_sectional",
        ]
        for cat in categories:
            library.create(f"logic_{cat}", cat, _make_hypothesis())
        cmap = library.coverage_map()
        for cat in categories:
            assert cmap[cat] == 1
