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
    return ExperienceMemory(config)


class TestReadState:
    def test_read_state(self, memory):
        state = memory.read_state()
        assert state["library"]["size"] == 0

    def test_read_patterns(self, memory):
        patterns = memory.read_patterns()
        assert len(patterns["recommended_directions"]) == 1
        assert patterns["recommended_directions"][0]["pattern"] == "Test Pattern"


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
        # compose_search_context no longer exposes patterns.yaml recommended_directions;
        # it always includes the mining state section.
        assert "## Current Mining State" in context


class TestContextPromptExpanded:
    """Tests for expanded compose_search_context() sections."""

    def test_returns_string(self, memory):
        """compose_search_context always returns a string."""
        result = memory.compose_search_context()
        assert isinstance(result, str)

    def test_contains_mining_state_header(self, memory):
        """Output includes the mining state section header."""
        result = memory.compose_search_context()
        assert "## Current Mining State" in result

    def test_contains_library_size(self, memory):
        """Output includes the library size from state.yaml."""
        result = memory.compose_search_context()
        assert "Library size: 0" in result

    def test_includes_next_round_hint(self, memory):
        """next_round_hint from state.yaml appears in output when present."""
        from pathlib import Path
        import yaml
        state_path = Path(memory._dir) / "state.yaml"
        state = yaml.safe_load(state_path.read_text())
        state["next_round_hint"] = "Try momentum reversals"
        state_path.write_text(yaml.dump(state))

        result = memory.compose_search_context()
        assert "Try momentum reversals" in result

    def test_direction_statuses_section(self, memory):
        """Directions written to memory appear in output under Direction Statuses."""
        memory.write_direction("test_dir", {
            "name": "test_dir",
            "status": "active",
            "priority": "high",
            "category": "momentum",
        })
        result = memory.compose_search_context()
        assert "## Direction Statuses" in result
        assert "test_dir" in result

    def test_forbidden_regions_section(self, memory):
        """Forbidden regions added via add_forbidden appear in output."""
        memory.add_forbidden("Corr(*,*)", "highly correlated family")
        result = memory.compose_search_context()
        assert "## Forbidden Regions" in result
        assert "Corr(*,*)" in result
        assert "highly correlated family" in result

    def test_coverage_map_section_with_logic_lib(self, memory, tmp_path):
        """Taxonomy Coverage section appears when logic library has active entries."""
        from mining.logic import MarketLogicLibrary

        logic_dir = tmp_path / "logic"
        logic_dir.mkdir()
        lib = MarketLogicLibrary(str(logic_dir))
        lib.create("Momentum Reversal", "momentum", {"core_idea": "test"})

        # Override the config's logic_dir to point to tmp logic dir
        memory._config.logic_dir = str(logic_dir)
        result = memory.compose_search_context()
        assert "## Taxonomy Coverage" in result
        assert "momentum" in result

    def test_active_logics_section_with_logic_lib(self, memory, tmp_path):
        """Active Market Logics section appears when there are active logics."""
        from mining.logic import MarketLogicLibrary

        logic_dir = tmp_path / "logic2"
        logic_dir.mkdir()
        lib = MarketLogicLibrary(str(logic_dir))
        lib.create("Mean Reversion Signal", "reversal", {"core_idea": "test"})
        lib.update_stats("L001", factors_generated=3, factors_admitted=1, best_ic=0.042)

        memory._config.logic_dir = str(logic_dir)
        result = memory.compose_search_context()
        assert "## Active Market Logics" in result
        assert "Mean Reversion Signal" in result
        assert "best_ic=0.042" in result

    def test_graceful_when_logic_dir_missing(self, memory):
        """compose_search_context does not raise when logic_dir does not exist."""
        memory._config.logic_dir = "/nonexistent/path/logic"
        result = memory.compose_search_context()
        assert isinstance(result, str)
        assert "## Current Mining State" in result


class TestEvalHistory:
    def test_save_and_list_eval_history(self, memory):
        memory.save_eval_history("batch_050", {"batch_id": "batch_050", "phase": "evaluate"})
        memory.save_eval_history("batch_051", {"batch_id": "batch_051", "phase": "evaluate"})
        history = memory.list_eval_history()
        assert len(history) == 2
        assert "batch_050" in history
        assert "batch_051" in history

    def test_eval_history_in_subdir(self, memory):
        """Eval history goes to history/eval/, not history/ root."""
        memory.save_eval_history("batch_050", {"batch_id": "batch_050"})
        eval_dir = Path(memory._dir) / "history" / "eval"
        assert (eval_dir / "batch_050.yaml").exists()
        # Old-style list should NOT include eval history
        old_list = memory.list_batch_history()
        assert "batch_050" not in old_list

    def test_save_admission_history(self, memory):
        memory.save_admission_history("batch_050", {"batch_id": "batch_050", "phase": "judge"})
        history = memory.list_admission_history()
        assert len(history) == 1


class TestAuditDirections:
    def test_detects_attempts_mismatch(self, memory, config):
        """audit_directions detects when recorded != observed attempts."""
        # Create a direction with 0 attempts
        memory.write_direction("test_dir", {
            "name": "test_dir", "status": "active", "attempts": 0,
            "category": "momentum", "priority": "high",
        })
        # Create a batch file that references this direction
        candidates_dir = Path(config.candidates_dir)
        candidates_dir.mkdir(parents=True, exist_ok=True)
        batch = {
            "batch_id": "batch_099",
            "candidates": [
                {"name": "F1", "expression": "Rank($close)", "direction": "test_dir"},
            ],
        }
        (candidates_dir / "batch_099.yaml").write_text(yaml.dump(batch))

        mismatches = memory.audit_directions(config.candidates_dir)
        assert len(mismatches) >= 1
        flags = [m["flag"] for m in mismatches]
        assert "attempts_mismatch" in flags

    def test_detects_zero_attempts_terminal(self, memory, config):
        """audit_directions flags attempts=0 + status=exhausted."""
        memory.write_direction("dead_dir", {
            "name": "dead_dir", "status": "exhausted", "attempts": 0,
            "category": "volatility", "priority": "low",
        })
        mismatches = memory.audit_directions(config.candidates_dir)
        flags = [m["flag"] for m in mismatches]
        assert "zero_attempts_terminal_status" in flags

    def test_empty_directions_no_crash(self, memory, config):
        """audit_directions with no directions returns empty list."""
        mismatches = memory.audit_directions(config.candidates_dir)
        assert mismatches == []


class TestGetLineageSummary:
    def test_get_lineage_summary_empty(self, memory):
        """With no library factors, returns empty string."""
        result = memory.get_lineage_summary()
        assert result == ""
