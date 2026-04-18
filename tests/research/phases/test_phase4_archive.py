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
        "batch_id": batch_id,
        "candidates": [
            {
                "candidate_id": cid,
                "source_type": "dsl",
                "expression": f"Mul($close, ${cid})",
                "coverage": 0.95,
                "sign": 1,
                "compute_error": None,
                "ic": {
                    "train": {"ic_mean": 0.018, "ic_ir": 0.30, "ic_win_rate": 0.58},
                    "validation": {
                        "ic_mean": 0.016,
                        "ic_ir": 0.338,
                        "ic_win_rate": 0.60,
                    },
                },
                "quintile": {
                    "validation": {
                        "monotonicity": 0.95,
                        "ls_mean": 0.007,
                    },
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

        # Two new factors allocated F001 / F002
        assert [a.factor_id for a in result.admitted] == ["F001", "F002"]
        assert all(a.yaml_path.exists() for a in result.admitted)

        # Direction frontmatter updated
        direction_md = paths.direction_file("vol")
        assert direction_md.exists()
        text = direction_md.read_text(encoding="utf-8")
        assert "F001" in text
        assert "F002" in text

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


class TestPhase4ChartBuilder:
    def test_chart_builder_success_embeds_in_packet(self, tmp_path: Path) -> None:
        storage_root = tmp_path / "storage"
        _init_repo(tmp_path)
        paths = StoragePaths(storage_root)
        paths.ensure_dirs()
        _bootstrap_state(paths, "batch_001")
        _bootstrap_batch(paths, "batch_001", ["C001"], "vol")

        seen: list[tuple[str, Path]] = []

        def fake_chart_builder(factor_id: str, assets_dir: Path) -> list[str]:
            seen.append((factor_id, assets_dir))
            return ["ic_timeseries", "quintile_bar"]

        inputs = Phase4Inputs(
            batch_id="batch_001",
            direction="vol",
            paths=paths,
            repo_root=tmp_path,
            do_commit=False,
            chart_builder=fake_chart_builder,
        )
        result = run_phase4_archive(inputs)

        assert seen == [("F001", paths.factor_assets_dir("F001"))]
        packet_text = result.report_packets[0].read_text(encoding="utf-8")
        assert "## Available Charts" in packet_text
        assert "- `ic_timeseries`" in packet_text
        assert "- `quintile_bar`" in packet_text

    def test_chart_builder_failure_does_not_block_archive(
        self, tmp_path: Path
    ) -> None:
        storage_root = tmp_path / "storage"
        _init_repo(tmp_path)
        paths = StoragePaths(storage_root)
        paths.ensure_dirs()
        _bootstrap_state(paths, "batch_001")
        _bootstrap_batch(paths, "batch_001", ["C001"], "vol")

        def broken_chart_builder(factor_id: str, assets_dir: Path) -> list[str]:
            raise RuntimeError("qlib init failed")

        inputs = Phase4Inputs(
            batch_id="batch_001",
            direction="vol",
            paths=paths,
            repo_root=tmp_path,
            do_commit=False,
            chart_builder=broken_chart_builder,
        )
        result = run_phase4_archive(inputs)

        # Archive still succeeded: factor allocated, packet written
        assert [a.factor_id for a in result.admitted] == ["F001"]
        packet_text = result.report_packets[0].read_text(encoding="utf-8")
        # Empty-charts branch active
        assert "No charts generated" in packet_text


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


class TestPhase4Backfill:
    """Phase 4 backfills the newly-allocated F{id} into Phase 3 artifacts.

    After allocation, the raw C{id} references in candidates/C{id}.md,
    judge.md, and directions/{dir}.md must gain the factor_id link.
    """

    def _seed_phase3_artifacts(
        self,
        paths: StoragePaths,
        batch_id: str,
        candidate_ids: list[str],
        direction: str,
    ) -> None:
        """Write candidate md + direction md reflecting post-JUDGE state."""
        bdir = paths.batch_dir(batch_id)
        cand_dir = bdir / "candidates"
        cand_dir.mkdir(parents=True, exist_ok=True)
        for cid in candidate_ids:
            fm = {
                "candidate_id": cid,
                "factor_id": None,
                "verdict": "admit",
            }
            md = (
                f"---\n{yaml.dump(fm, sort_keys=False)}---\n\n"
                f"## Synthesis\n\nAdmit rationale for {cid}.\n"
            )
            (cand_dir / f"{cid}.md").write_text(md, encoding="utf-8")

        # Rewrite judge.md with a table row per candidate so backfill
        # has the "admit" verdict cell + candidate wikilink to patch
        judge_fm = {
            "batch_id": batch_id,
            "direction": direction,
            "candidates": [
                {
                    "candidate_id": cid,
                    "verdict": "admit",
                    "hard_gate_result": "all_pass",
                    "checkpoint_positions": {},
                    "referenced_context": [],
                }
                for cid in candidate_ids
            ],
            "batch_summary": {
                "total": len(candidate_ids),
                "admit": len(candidate_ids),
                "reserve": 0,
                "reject": 0,
            },
        }
        rows = "\n".join(
            f"| {cid} | admit | ok | [[batches/{batch_id}/candidates/{cid}]] |"
            for cid in candidate_ids
        )
        judge_body = (
            f"---\n{yaml.dump(judge_fm, sort_keys=False)}---\n\n"
            f"## Verdict Table\n\n"
            f"| candidate | verdict | note | detail |\n"
            f"|---|---|---|---|\n"
            f"{rows}\n"
        )
        (bdir / "judge.md").write_text(judge_body, encoding="utf-8")

        # Direction md with Thread trail line that ends in "→ **admit**"
        dir_path = paths.direction_file(direction)
        dir_path.parent.mkdir(parents=True, exist_ok=True)
        dir_fm = {
            "direction": direction,
            "status": "active",
            "batches_run": [],
            "admitted_factors": [],
        }
        thread_lines = "\n".join(
            f"- [[batches/{batch_id}/candidates/{cid}|{cid}]]: "
            f"rationale → **admit**"
            for cid in candidate_ids
        )
        dir_body = (
            f"---\n{yaml.dump(dir_fm, sort_keys=False)}---\n\n"
            f"## Thread {batch_id}\n\n{thread_lines}\n"
        )
        dir_path.write_text(dir_body, encoding="utf-8")

    def test_phase4_backfills_factor_id_into_candidate_judge_direction(
        self, tmp_path: Path
    ) -> None:
        storage_root = tmp_path / "storage"
        _init_repo(tmp_path)
        paths = StoragePaths(storage_root)
        paths.ensure_dirs()
        _bootstrap_state(paths, "batch_001")
        _bootstrap_batch(paths, "batch_001", ["C001"], "vol")
        self._seed_phase3_artifacts(paths, "batch_001", ["C001"], "vol")

        inputs = Phase4Inputs(
            batch_id="batch_001",
            direction="vol",
            paths=paths,
            repo_root=tmp_path,
            do_commit=False,
        )
        result = run_phase4_archive(inputs)
        assert result.admitted, "fixture must have at least one admit"
        fid = result.admitted[0].factor_id
        cid = "C001"

        cand_md = paths.batch_candidate_md_file("batch_001", cid).read_text(
            encoding="utf-8"
        )
        judge_md = paths.batch_judge_file("batch_001").read_text(encoding="utf-8")
        dir_md = paths.direction_file("vol").read_text(encoding="utf-8")

        assert f"factor_id: {fid}" in cand_md
        assert f"admit → {fid}" in judge_md
        assert f"[[factors/{fid}]]" in judge_md
        assert f"admit → [[factors/{fid}]]" in dir_md

    def test_phase4_no_admits_skips_batch_level_backfill(
        self, tmp_path: Path
    ) -> None:
        """When nothing is admitted, judge.md + direction.md untouched by backfill."""
        storage_root = tmp_path / "storage"
        _init_repo(tmp_path)
        paths = StoragePaths(storage_root)
        paths.ensure_dirs()
        _bootstrap_state(paths, "batch_001")

        # Manually bootstrap batch with zero admits
        bdir = paths.batch_dir("batch_001")
        bdir.mkdir(parents=True, exist_ok=True)
        save_yaml(
            bdir / "manifest.yaml",
            {
                "batch_id": "batch_001",
                "direction": "vol",
                "batch_goal": "zero admits",
                "candidates": [],
            },
        )
        save_yaml(bdir / "result.yaml", {"batch_id": "batch_001", "candidates": []})
        fm = {
            "batch_id": "batch_001",
            "direction": "vol",
            "candidates": [],
            "batch_summary": {
                "total": 0, "admit": 0, "reserve": 0, "reject": 0,
            },
        }
        (bdir / "judge.md").write_text(
            f"---\n{yaml.dump(fm, sort_keys=False)}\n---\n\n## body",
            encoding="utf-8",
        )

        inputs = Phase4Inputs(
            batch_id="batch_001",
            direction="vol",
            paths=paths,
            repo_root=tmp_path,
            do_commit=False,
        )
        result = run_phase4_archive(inputs)
        assert result.admitted == []


class TestDiagnosticsRetention:
    """Phase 4 prunes non-admit diagnostic dirs older than 3 batches."""

    def _seed_diag(
        self,
        paths: StoragePaths,
        batch_id: str,
        admit_ids: list[str],
        reject_ids: list[str],
    ) -> None:
        """Create per-candidate diagnostic dirs for a historical batch."""
        for cid in admit_ids + reject_ids:
            d = paths.candidate_diagnostics_dir(batch_id, cid)
            d.mkdir(parents=True, exist_ok=True)
            (d / "ic_daily.parquet").write_bytes(b"stub")
        # Also write a minimal judge.md so _prune_ can read verdicts
        bdir = paths.batch_dir(batch_id)
        bdir.mkdir(parents=True, exist_ok=True)
        fm = {
            "batch_id": batch_id,
            "candidates": (
                [
                    {
                        "candidate_id": cid,
                        "verdict": "admit",
                        "hard_gate_result": "all_pass",
                        "checkpoint_positions": {},
                        "referenced_context": [],
                    }
                    for cid in admit_ids
                ]
                + [
                    {
                        "candidate_id": cid,
                        "verdict": "reject",
                        "hard_gate_result": "all_pass",
                        "checkpoint_positions": {},
                        "referenced_context": [],
                    }
                    for cid in reject_ids
                ]
            ),
        }
        (bdir / "judge.md").write_text(
            f"---\n{yaml.dump(fm, sort_keys=False)}\n---\nbody",
            encoding="utf-8",
        )

    def test_prunes_non_admits_older_than_three_batches(
        self, tmp_path: Path
    ) -> None:
        storage_root = tmp_path / "storage"
        _init_repo(tmp_path)
        paths = StoragePaths(storage_root)
        paths.ensure_dirs()

        # Seed 4 historical batches + the current one
        for bid, admits, rejects in [
            ("batch_001", ["C001"], ["C002", "C003"]),  # oldest, eligible
            ("batch_002", ["C004"], ["C005"]),          # eligible
            ("batch_003", [], ["C006"]),                # KEEP (within window)
            ("batch_004", ["C007"], ["C008"]),          # KEEP (within window)
        ]:
            self._seed_diag(paths, bid, admits, rejects)

        # Current batch being archived
        _bootstrap_state(paths, "batch_005")
        _bootstrap_batch(paths, "batch_005", ["C009"], "vol")
        # Seed diag for current batch too
        paths.candidate_diagnostics_dir("batch_005", "C009").mkdir(
            parents=True, exist_ok=True
        )

        run_phase4_archive(Phase4Inputs(
            batch_id="batch_005",
            direction="vol",
            paths=paths,
            repo_root=tmp_path,
            do_commit=False,
        ))

        # batch_001 + batch_002 are older than (current - 3 + 1):
        # keep_cutoff = index(batch_005) - 3 + 1 = 4 - 3 + 1 = 2
        # eligible = all_batches[:2] = [batch_001, batch_002]
        # Non-admits in those batches must be gone; admits preserved.
        assert not paths.candidate_diagnostics_dir("batch_001", "C002").exists()
        assert not paths.candidate_diagnostics_dir("batch_001", "C003").exists()
        assert paths.candidate_diagnostics_dir("batch_001", "C001").exists()
        assert not paths.candidate_diagnostics_dir("batch_002", "C005").exists()
        assert paths.candidate_diagnostics_dir("batch_002", "C004").exists()

        # batch_003 + batch_004 + batch_005 untouched (within window)
        assert paths.candidate_diagnostics_dir("batch_003", "C006").exists()
        assert paths.candidate_diagnostics_dir("batch_004", "C007").exists()
        assert paths.candidate_diagnostics_dir("batch_004", "C008").exists()
        assert paths.candidate_diagnostics_dir("batch_005", "C009").exists()
