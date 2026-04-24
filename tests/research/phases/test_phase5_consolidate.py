"""Phase 5 consolidation orchestrator tests."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest

from research.memory.direction_updater import update_direction_frontmatter
from research.phases.phase5_consolidate import (
    ConsolidationTrigger,
    Phase5Inputs,
    Phase5PreconditionError,
    check_triggers,
    prepack_consolidation,
    preconditions_ok,
    run_phase5_consolidation,
)
from research.storage.paths import StoragePaths
from research.storage.state import StateFile
from research.storage.yaml_io import save_yaml


def _init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    subprocess.run(["git", "config", "user.email", "t@t"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"],
        cwd=root,
        check=True,
    )


def _bootstrap_idle_state(paths: StoragePaths, round_: int = 0) -> None:
    save_yaml(
        paths.state_file,
        {
            "current_batch": None,
            "current_batch_phase": None,
            "last_batch": "batch_001",
            "round": round_,
            "last_activity": "2026-04-12T10:00:00Z",
            "rounds_since_last_consolidation": 0,
        },
    )


class TestCheckTriggers:
    def test_no_trigger_returns_none(self, tmp_path: Path) -> None:
        paths = StoragePaths(tmp_path)
        paths.ensure_dirs()
        paths.vault_lessons_file.write_text("small lessons")
        t = check_triggers(
            paths,
            auto_triggers={
                "rounds_since_last": 10,
                "lessons_max_lines": 400,
                "direction_max_lines": 500,
                "total_active_directions": 20,
            },
            rounds_since_last=3,
        )
        assert t is None

    def test_rounds_trigger(self, tmp_path: Path) -> None:
        paths = StoragePaths(tmp_path)
        paths.ensure_dirs()
        t = check_triggers(paths, {"rounds_since_last": 10}, rounds_since_last=10)
        assert t is not None
        assert t.reason == "rounds_since_last"

    def test_lessons_line_count_trigger(self, tmp_path: Path) -> None:
        paths = StoragePaths(tmp_path)
        paths.ensure_dirs()
        paths.vault_lessons_file.write_text("\n" * 500)
        t = check_triggers(
            paths,
            {"lessons_max_lines": 100, "rounds_since_last": 100},
            rounds_since_last=0,
        )
        assert t is not None
        assert t.reason == "lessons_max_lines"

    def test_direction_size_trigger(self, tmp_path: Path) -> None:
        paths = StoragePaths(tmp_path)
        paths.ensure_dirs()
        update_direction_frontmatter(
            paths.direction_file("vol"), batch_id="batch_001", new_admits=[]
        )
        # Grow the direction md past the threshold
        with open(paths.direction_file("vol"), "a", encoding="utf-8") as f:
            f.write("\nextra line\n" * 600)
        t = check_triggers(
            paths,
            {
                "direction_max_lines": 100,
                "rounds_since_last": 100,
                "lessons_max_lines": 1_000_000,
                "total_active_directions": 1_000_000,
            },
            rounds_since_last=0,
        )
        assert t is not None
        assert t.reason == "direction_max_lines"
        assert t.details["direction"] == "vol"


class TestPrepackConsolidation:
    def test_packets_written_for_each_target(self, tmp_path: Path) -> None:
        paths = StoragePaths(tmp_path)
        paths.ensure_dirs()
        paths.vault_lessons_file.write_text("original lessons")
        update_direction_frontmatter(
            paths.direction_file("vol"), batch_id="batch_001", new_admits=[]
        )
        update_direction_frontmatter(
            paths.direction_file("mom"), batch_id="batch_001", new_admits=[]
        )
        paths.vault_index_file.write_text("# INDEX")

        packets = prepack_consolidation(paths)
        assert "lessons" in packets
        assert "direction:vol" in packets
        assert "direction:mom" in packets
        assert "index" not in packets
        for p in packets.values():
            assert p.exists()
            assert "# Consolidation Packet" in p.read_text(encoding="utf-8")


class TestPreconditionsOk:
    def test_idle_clean_passes(self, tmp_path: Path) -> None:
        storage = tmp_path / "storage"
        paths = StoragePaths(storage)
        paths.ensure_dirs()
        _bootstrap_idle_state(paths)
        _init_repo(tmp_path)
        # Stage + commit so git is clean
        subprocess.run(
            ["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        failures = preconditions_ok(StateFile(paths.state_file), tmp_path)
        assert failures == []

    def test_batch_in_flight_fails(self, tmp_path: Path) -> None:
        storage = tmp_path / "storage"
        paths = StoragePaths(storage)
        paths.ensure_dirs()
        save_yaml(
            paths.state_file,
            {
                "current_batch": "batch_001",
                "current_batch_phase": "judged",
                "last_batch": None,
                "round": 0,
                "last_activity": "2026-04-12T10:00:00Z",
                "rounds_since_last_consolidation": 0,
            },
        )
        _init_repo(tmp_path)
        subprocess.run(
            ["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        failures = preconditions_ok(StateFile(paths.state_file), tmp_path)
        assert any("batch in flight" in f for f in failures)

    def test_dirty_git_fails(self, tmp_path: Path) -> None:
        storage = tmp_path / "storage"
        paths = StoragePaths(storage)
        paths.ensure_dirs()
        _bootstrap_idle_state(paths)
        _init_repo(tmp_path)
        # Don't commit — git is dirty
        failures = preconditions_ok(StateFile(paths.state_file), tmp_path)
        assert any("dirty" in f for f in failures)


class TestRunPhase5:
    def test_preconditions_raise(self, tmp_path: Path) -> None:
        storage = tmp_path / "storage"
        paths = StoragePaths(storage)
        paths.ensure_dirs()
        save_yaml(
            paths.state_file,
            {
                "current_batch": "batch_001",
                "current_batch_phase": "judged",
                "last_batch": None,
                "round": 0,
                "last_activity": "2026-04-12T10:00:00Z",
                "rounds_since_last_consolidation": 0,
            },
        )
        _init_repo(tmp_path)
        subprocess.run(
            ["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )
        inputs = Phase5Inputs(
            paths=paths,
            repo_root=tmp_path,
            trigger=ConsolidationTrigger(reason="manual"),
            rewrite_callback=lambda *a: None,
            do_commit=False,
        )
        with pytest.raises(Phase5PreconditionError, match="batch in flight"):
            run_phase5_consolidation(inputs)

    def test_rewrite_failure_restores_from_backup(self, tmp_path: Path) -> None:
        storage = tmp_path / "storage"
        paths = StoragePaths(storage)
        paths.ensure_dirs()
        paths.vault_lessons_file.write_text("ORIGINAL lessons\n")
        update_direction_frontmatter(
            paths.direction_file("vol"), batch_id="batch_001", new_admits=[]
        )
        original_vol = paths.direction_file("vol").read_text(encoding="utf-8")
        paths.vault_index_file.write_text(
            "# INDEX\n\nORIGINAL upper\n"
            "<!-- BEGIN AUTO-SECTION -->\n<!-- END AUTO-SECTION -->\n"
        )
        original_index = paths.vault_index_file.read_text(encoding="utf-8")
        _bootstrap_idle_state(paths, round_=5)
        _init_repo(tmp_path)
        subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)

        call_count = {"n": 0}

        def flaky(
            packet_text: str, packet_path: Path, output_path: Path, kind: str
        ) -> None:
            call_count["n"] += 1
            # First call succeeds (lessons), second raises (mid-rewrite failure).
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text("CORRUPTED\n")
            if call_count["n"] >= 2:
                raise RuntimeError("subagent crashed")

        inputs = Phase5Inputs(
            paths=paths,
            repo_root=tmp_path,
            trigger=ConsolidationTrigger(reason="manual"),
            rewrite_callback=flaky,
            do_commit=False,
        )
        with pytest.raises(RuntimeError, match="subagent crashed"):
            run_phase5_consolidation(inputs)

        # All touched files restored to original content.
        assert paths.vault_lessons_file.read_text(encoding="utf-8") == "ORIGINAL lessons\n"
        assert paths.direction_file("vol").read_text(encoding="utf-8") == original_vol
        assert paths.vault_index_file.read_text(encoding="utf-8") == original_index

    def test_stale_backup_dir_blocks_run(self, tmp_path: Path) -> None:
        storage = tmp_path / "storage"
        paths = StoragePaths(storage)
        paths.ensure_dirs()
        _bootstrap_idle_state(paths)
        _init_repo(tmp_path)
        subprocess.run(["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", "init"], cwd=tmp_path, check=True, capture_output=True)

        # Pre-create stale backup dir (simulates prior failed run).
        stale = paths.vault_meta_dir.parent / "_consolidation" / "backup"
        stale.mkdir(parents=True, exist_ok=True)

        inputs = Phase5Inputs(
            paths=paths,
            repo_root=tmp_path,
            trigger=ConsolidationTrigger(reason="manual"),
            rewrite_callback=lambda *a: None,
            do_commit=False,
        )
        with pytest.raises(Phase5PreconditionError, match="backup"):
            run_phase5_consolidation(inputs)

    def test_end_to_end_no_commit(self, tmp_path: Path) -> None:
        storage = tmp_path / "storage"
        paths = StoragePaths(storage)
        paths.ensure_dirs()
        paths.vault_lessons_file.write_text("original lessons\n")
        update_direction_frontmatter(
            paths.direction_file("vol"), batch_id="batch_001", new_admits=["F020"]
        )
        paths.vault_index_file.write_text(
            "# INDEX\n\nUpper half content\n\n"
            "<!-- BEGIN AUTO-SECTION -->\n\nauto\n\n<!-- END AUTO-SECTION -->\n"
        )
        _bootstrap_idle_state(paths, round_=5)
        _init_repo(tmp_path)
        subprocess.run(
            ["git", "add", "-A"], cwd=tmp_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "init"],
            cwd=tmp_path,
            check=True,
            capture_output=True,
        )

        written: list[tuple[Path, str]] = []

        def fake_subagent(
            packet_text: str, packet_path: Path, output_path: Path, kind: str
        ) -> None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(
                f"# Rewritten {kind}\n\n(LLM-written)\n"
            )
            written.append((output_path, kind))

        inputs = Phase5Inputs(
            paths=paths,
            repo_root=tmp_path,
            trigger=ConsolidationTrigger(reason="manual"),
            rewrite_callback=fake_subagent,
            do_commit=False,
        )
        result = run_phase5_consolidation(inputs)

        # targets include LLM rewrite targets plus Python-refreshed INDEX
        assert "lessons" in result.targets
        assert "direction:vol" in result.targets
        assert "index" in result.targets

        # rewrite_callback fired only for LLM-owned targets; INDEX is Python-owned.
        kinds = [k for _, k in written]
        assert "lessons" in kinds
        assert "direction" in kinds
        assert "index" not in kinds

        # State counter was reset
        final = StateFile(paths.state_file).read()
        assert final.rounds_since_last_consolidation == 0
