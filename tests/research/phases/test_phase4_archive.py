"""End-to-end tests for Phase 4 ARCHIVE (Python side)."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
import yaml

from research.phases.phase4_archive import Phase4Inputs, run_phase4_archive
from research.storage.paths import StoragePaths
from research.storage.state import InvalidPhaseTransition, StateFile
from research.storage.yaml_io import load_yaml, save_yaml


def _init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    subprocess.run(["git", "init"], cwd=root, check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=root, check=True)
    subprocess.run(
        ["git", "config", "user.email", "t@t"], cwd=root, check=True
    )
    subprocess.run(
        ["git", "config", "commit.gpgsign", "false"],
        cwd=root,
        check=True,
    )


def _bootstrap_state(paths: StoragePaths, batch_id: str) -> None:
    save_yaml(
        paths.state_file,
        {
            "current_batch": batch_id,
            "current_batch_phase": "judged",  # Phase 3 finished
            "last_batch": None,
            "round": 0,
            "last_activity": "2026-04-12T10:00:00Z",
            "rounds_since_last_consolidation": 0,
        },
    )


def _bootstrap_batch(
    paths: StoragePaths,
    batch_id: str,
    admit_ids: list[str],
    direction: str,
) -> None:
    bdir = paths.batch_dir(batch_id)
    bdir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "batch_id": batch_id,
        "direction": direction,
        "batch_goal": "Probe fundamental × price divergence for " + direction,
        "sample_policy_version": "v3",
        "candidates": [
            {
                "candidate_id": cid,
                "source_type": "dsl",
                "expression": f"Mul($close, ${cid})",
                "canonical": f"Mul($close,${cid})",
            }
            for cid in admit_ids
        ],
    }
    save_yaml(bdir / "manifest.yaml", manifest)

    result = {
        "schema_version": "1",
        "batch_id": batch_id,
        "sample_policy_version": "v3",
        "candidates": [
            {
                "candidate_id": cid,
                "source_type": "dsl",
                "expression": f"Mul($close, ${cid})",
                "coverage": 0.95,
                "sign": 1,
                "compute_error": None,
                "effect_strength": {
                    "train": {"ic_mean": 0.018, "ic_ir": 0.30, "ic_win_rate": 0.58},
                    "validation": {
                        "ic_mean": 0.016,
                        "ic_ir": 0.338,
                        "ic_win_rate": 0.60,
                    },
                },
                "quintile": {
                    "monotonicity_validation": 0.95,
                    "long_short_mean_validation": 0.007,
                },
                "barra": {
                    "style_r_squared": 0.08,
                    "alpha_survival_ratio": 0.81,
                },
            }
            for cid in admit_ids
        ],
    }
    save_yaml(bdir / "result.yaml", result)

    # Minimal valid judge.md
    fm_candidates = [
        {
            "candidate_id": cid,
            "verdict": "admit",
            "hard_gate_result": "all_pass",
            "checkpoint_positions": {},
            "referenced_context": [],
        }
        for cid in admit_ids
    ]
    fm = {
        "batch_id": batch_id,
        "direction": direction,
        "candidates": fm_candidates,
        "batch_summary": {
            "total": len(admit_ids),
            "admit": len(admit_ids),
            "reserve": 0,
            "reject": 0,
        },
    }
    (bdir / "judge.md").write_text(
        f"---\n{yaml.dump(fm, sort_keys=False)}\n---\n\n## C001\n\n### CP01\nok",
        encoding="utf-8",
    )


class TestPhase4HappyPath:
    def test_archives_admit_and_updates_state(self, tmp_path: Path) -> None:
        storage_root = tmp_path / "storage"
        _init_repo(tmp_path)
        paths = StoragePaths(storage_root)
        paths.ensure_dirs()
        _bootstrap_state(paths, "batch_001")
        _bootstrap_batch(paths, "batch_001", ["C001", "C002"], "vol")

        inputs = Phase4Inputs(
            batch_id="batch_001",
            direction="vol",
            paths=paths,
            repo_root=tmp_path,
            do_commit=False,  # skip git for unit test simplicity
        )
        result = run_phase4_archive(inputs)

        # Two new factors allocated F020 / F021
        assert [a.factor_id for a in result.admitted] == ["F020", "F021"]
        assert all(a.yaml_path.exists() for a in result.admitted)

        # Direction frontmatter updated
        direction_md = paths.direction_file("vol")
        assert direction_md.exists()
        text = direction_md.read_text(encoding="utf-8")
        assert "F020" in text
        assert "F021" in text

        # INDEX.md refreshed
        assert result.index_path == paths.vault_index_file
        index_text = paths.vault_index_file.read_text(encoding="utf-8")
        assert "vol" in index_text
        assert "Total factors admitted | 2" in index_text

        # State advanced: finish_batch clears current_batch and bumps round
        state = StateFile(paths.state_file).read()
        assert state.current_batch is None
        assert state.current_batch_phase is None
        assert state.last_batch == "batch_001"
        assert state.round == 1
        assert state.rounds_since_last_consolidation == 1


class TestPhase4Idempotency:
    def test_double_archive_raises(self, tmp_path: Path) -> None:
        storage_root = tmp_path / "storage"
        _init_repo(tmp_path)
        paths = StoragePaths(storage_root)
        paths.ensure_dirs()
        _bootstrap_state(paths, "batch_001")
        _bootstrap_batch(paths, "batch_001", ["C001"], "vol")

        inputs = Phase4Inputs(
            batch_id="batch_001",
            direction="vol",
            paths=paths,
            repo_root=tmp_path,
            do_commit=False,
        )
        run_phase4_archive(inputs)

        # State is now idle (finish_batch was called). Trying to archive
        # again from idle → transition_phase("archived") raises because
        # idle → archived is not a legal step.
        with pytest.raises(InvalidPhaseTransition):
            run_phase4_archive(inputs)


class TestPhase4ReportCallback:
    def test_report_packet_written_per_admit(self, tmp_path: Path) -> None:
        storage_root = tmp_path / "storage"
        _init_repo(tmp_path)
        paths = StoragePaths(storage_root)
        paths.ensure_dirs()
        _bootstrap_state(paths, "batch_001")
        _bootstrap_batch(paths, "batch_001", ["C001", "C002"], "vol")

        # Capture the callback invocations
        invocations: list[tuple[str, Path, Path]] = []

        def fake_subagent(
            packet_text: str, packet_path: Path, factor_md_path: Path
        ) -> None:
            invocations.append((packet_text, packet_path, factor_md_path))
            # Write the factor.md to the specified location
            factor_md_path.parent.mkdir(parents=True, exist_ok=True)
            factor_md_path.write_text(
                f"# {factor_md_path.stem}\n\n(LLM-written report body)\n"
            )

        inputs = Phase4Inputs(
            batch_id="batch_001",
            direction="vol",
            paths=paths,
            repo_root=tmp_path,
            do_commit=False,
            report_callback=fake_subagent,
        )
        result = run_phase4_archive(inputs)

        # Both admits got packets
        assert len(result.report_packets) == 2
        assert all(p.exists() for p in result.report_packets)

        # Both callbacks were invoked
        assert len(invocations) == 2
        for text, pkt, md in invocations:
            assert "# Report Packet" in text
            assert pkt.name.startswith("report_packet_F")
            assert md.name.startswith("F") and md.suffix == ".md"

        # Both factor.md files were written by the fake subagent
        for md_path in result.factor_md_paths:
            assert md_path.exists()

    def test_no_callback_skips_subagent(self, tmp_path: Path) -> None:
        storage_root = tmp_path / "storage"
        _init_repo(tmp_path)
        paths = StoragePaths(storage_root)
        paths.ensure_dirs()
        _bootstrap_state(paths, "batch_001")
        _bootstrap_batch(paths, "batch_001", ["C001"], "vol")

        inputs = Phase4Inputs(
            batch_id="batch_001",
            direction="vol",
            paths=paths,
            repo_root=tmp_path,
            do_commit=False,
            report_callback=None,
        )
        result = run_phase4_archive(inputs)
        # Packet still written (for manual inspection)
        assert len(result.report_packets) == 1
        assert result.report_packets[0].exists()
        # factor.md not produced because no callback
        assert not result.factor_md_paths[0].exists()


class TestPhase4WithCommit:
    def test_commit_writes_git_object(self, tmp_path: Path) -> None:
        storage_root = tmp_path / "storage"
        _init_repo(tmp_path)
        paths = StoragePaths(storage_root)
        paths.ensure_dirs()
        _bootstrap_state(paths, "batch_001")
        _bootstrap_batch(paths, "batch_001", ["C001"], "vol")

        inputs = Phase4Inputs(
            batch_id="batch_001",
            direction="vol",
            paths=paths,
            repo_root=tmp_path,
            do_commit=True,
        )
        result = run_phase4_archive(inputs)
        assert result.commit is not None
        assert len(result.commit.commit_hash) == 40
        # Commit message subject format
        assert result.commit.message.startswith("[mine] batch_001 | vol | admits=1")
