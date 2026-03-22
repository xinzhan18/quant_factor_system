"""Tests for ExperienceMemory."""

import yaml
import pytest
from pathlib import Path
from mining.memory import ExperienceMemory


@pytest.fixture
def memory(tmp_mining_dir, config):
    mem_dir = Path(config.memory_dir)
    (mem_dir / "state.yaml").write_text(yaml.dump({
        "library": {"size": 0, "target_size": 100, "avg_ic": 0.0, "avg_correlation": 0.0},
        "domain_saturation": {"vwap": {"count": 0, "saturation": "low"}},
        "mining": {"total_batches": 0, "total_candidates": 0, "total_admitted": 0, "total_rejected": 0, "yield_rate": 0.0, "last_batch_time": None},
    }))
    (mem_dir / "patterns.yaml").write_text(yaml.dump({
        "recommended_directions": [{"pattern": "Test Pattern", "description": "desc", "success_rate": "high", "example_factors": []}],
        "forbidden_regions": [],
    }))
    (mem_dir / "insights.yaml").write_text(yaml.dump({
        "insights": [{"insight": "Test insight", "confidence": "high", "source": "test"}],
    }))
    return ExperienceMemory(config)


class TestReadState:
    def test_read_state(self, memory):
        state = memory.read_state()
        assert state["library"]["size"] == 0

    def test_read_patterns(self, memory):
        patterns = memory.read_patterns()
        assert len(patterns["recommended_directions"]) == 1
        assert patterns["recommended_directions"][0]["pattern"] == "Test Pattern"

    def test_read_insights(self, memory):
        insights = memory.read_insights()
        assert len(insights["insights"]) == 1


class TestWriteState:
    def test_update_state(self, memory):
        state = memory.read_state()
        state["library"]["size"] = 5
        state["mining"]["total_batches"] = 1
        memory.write_state(state)
        reloaded = memory.read_state()
        assert reloaded["library"]["size"] == 5

    def test_add_pattern(self, memory):
        patterns = memory.read_patterns()
        patterns["recommended_directions"].append({"pattern": "New Pattern", "description": "new desc", "success_rate": "medium", "example_factors": []})
        memory.write_patterns(patterns)
        reloaded = memory.read_patterns()
        assert len(reloaded["recommended_directions"]) == 2

    def test_add_forbidden_region(self, memory):
        patterns = memory.read_patterns()
        patterns["forbidden_regions"].append({"direction": "Bad Direction", "reason": "too correlated", "correlated_factors": ["f1"], "correlation": "> 0.7"})
        memory.write_patterns(patterns)
        reloaded = memory.read_patterns()
        assert len(reloaded["forbidden_regions"]) == 1


class TestHistory:
    def test_save_batch_history(self, memory):
        memory.save_batch_history("batch_001", {"batch_id": "batch_001", "candidates": 8, "admitted": 2, "rejected": 6})
        history = memory.load_batch_history("batch_001")
        assert history["batch_id"] == "batch_001"

    def test_list_history(self, memory):
        memory.save_batch_history("batch_001", {"batch_id": "batch_001"})
        memory.save_batch_history("batch_002", {"batch_id": "batch_002"})
        batches = memory.list_batch_history()
        assert len(batches) == 2


class TestContextPrompt:
    def test_compose_context(self, memory):
        context = memory.compose_search_context()
        assert isinstance(context, str)
        assert "Test Pattern" in context
        assert "Test insight" in context
