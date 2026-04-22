"""Tests for audit_index_format — the Phase 4 hard-stop drift detector."""

from __future__ import annotations

from pathlib import Path

import pytest

from research.memory.index_audit import (
    IndexFormatError,
    audit_index_format,
    audit_index_format_or_raise,
)
from research.memory.index_narrative import INSIGHT_BEGIN, INSIGHT_END
from research.storage.paths import StoragePaths
from research.storage.yaml_io import save_yaml


def _seed_minimal_vault(tmp_path: Path) -> StoragePaths:
    """Build a minimal but audit-passable vault under ``tmp_path``."""
    paths = StoragePaths(tmp_path)
    paths.ensure_dirs()

    save_yaml(
        paths.state_file,
        {
            "current_batch": None,
            "current_batch_phase": None,
            "last_batch": "batch_001",
            "round": 1,
            "last_activity": "2026-04-22T00:00:00Z",
            "rounds_since_last_consolidation": 1,
        },
    )

    # _bases/
    bases_dir = paths.vault_dir / "_bases"
    bases_dir.mkdir(parents=True, exist_ok=True)
    for fname in ("directions.base", "factors.base", "recent_batches.base"):
        (bases_dir / fname).write_text(
            "filters: []\nviews:\n  - type: table\n    name: x\n    order: [file.name]\n",
            encoding="utf-8",
        )

    # one valid direction
    d = paths.direction_file("vol")
    d.write_text(
        "---\n"
        "direction_id: vol\nstatus: exploring\npriority: high\n"
        "rounds: 1\nadmits: 0\nlast_batch: batch_001\n"
        "---\n# vol\n",
        encoding="utf-8",
    )

    # one valid factor (yaml + md sides both present)
    save_yaml(
        paths.factors_dir / "F001.yaml",
        {"factor_id": "F001", "status": "active"},
    )
    (paths.factors_dir / "F001.md").write_text(
        "---\n"
        "id: F001\ndecision: admit\nstatus: active\n"
        "composite_grade: A\nic_ir_validation: 0.3\n"
        "monotonicity_validation: 1.0\ndirection: vol\n"
        "---\n# F001\n",
        encoding="utf-8",
    )

    # one valid batch judge
    bdir = paths.batches_dir / "batch_001"
    bdir.mkdir(parents=True, exist_ok=True)
    (bdir / "judge.md").write_text(
        "---\n"
        "batch_id: batch_001\ndirection: vol\n"
        "admit_count: 0\nreject_count: 1\nreserve_count: 0\ncandidate_count: 1\n"
        "---\n# judge\n",
        encoding="utf-8",
    )

    # minimal audit-passable INDEX body
    paths.vault_index_file.write_text(
        "---\n"
        "round: 1\nlast_batch: batch_001\n"
        "---\n"
        "# Index\n\n"
        "![[_bases/directions.base]]\n"
        "![[_bases/factors.base]]\n"
        "![[_bases/recent_batches.base]]\n\n"
        f"{INSIGHT_BEGIN}\n> body\n{INSIGHT_END}\n",
        encoding="utf-8",
    )
    return paths


class TestAuditPasses:
    def test_clean_vault(self, tmp_path: Path) -> None:
        paths = _seed_minimal_vault(tmp_path)
        report = audit_index_format(paths)
        assert report.ok, report.errors


class TestAuditCatches:
    def test_missing_base_file(self, tmp_path: Path) -> None:
        paths = _seed_minimal_vault(tmp_path)
        (paths.vault_dir / "_bases" / "directions.base").unlink()
        report = audit_index_format(paths)
        assert not report.ok
        assert any("directions.base missing" in e for e in report.errors)

    def test_missing_direction_frontmatter_key(self, tmp_path: Path) -> None:
        paths = _seed_minimal_vault(tmp_path)
        # Wipe priority to simulate drift
        d = paths.direction_file("vol")
        d.write_text(
            "---\ndirection_id: vol\nstatus: exploring\n"
            "rounds: 1\nadmits: 0\nlast_batch: batch_001\n---\n# vol\n",
            encoding="utf-8",
        )
        report = audit_index_format(paths)
        assert any("vol.md" in e and "priority" in e for e in report.errors)

    def test_missing_factor_md_key(self, tmp_path: Path) -> None:
        paths = _seed_minimal_vault(tmp_path)
        (paths.factors_dir / "F001.md").write_text(
            "---\nid: F001\ndecision: admit\nstatus: active\n---\n",
            encoding="utf-8",
        )
        report = audit_index_format(paths)
        assert any("F001.md" in e for e in report.errors)

    def test_missing_judge_fields(self, tmp_path: Path) -> None:
        paths = _seed_minimal_vault(tmp_path)
        (paths.batches_dir / "batch_001" / "judge.md").write_text(
            "---\nbatch_id: batch_001\n---\n# judge\n",
            encoding="utf-8",
        )
        report = audit_index_format(paths)
        assert any("judge.md" in e for e in report.errors)

    def test_missing_index_embed(self, tmp_path: Path) -> None:
        paths = _seed_minimal_vault(tmp_path)
        paths.vault_index_file.write_text(
            "---\nround: 1\nlast_batch: batch_001\n---\n# Index\n",
            encoding="utf-8",
        )
        report = audit_index_format(paths)
        assert any("_bases/directions.base" in e for e in report.errors)
        assert any("insight sentinels" in e for e in report.errors)

    def test_state_round_mismatch(self, tmp_path: Path) -> None:
        paths = _seed_minimal_vault(tmp_path)
        save_yaml(
            paths.state_file,
            {
                "current_batch": None,
                "current_batch_phase": None,
                "last_batch": "batch_001",
                "round": 42,  # diverged from INDEX frontmatter round=1
                "last_activity": "2026-04-22T00:00:00Z",
                "rounds_since_last_consolidation": 1,
            },
        )
        report = audit_index_format(paths)
        assert any("round" in e for e in report.errors)


class TestAuditOrRaise:
    def test_passes_silent(self, tmp_path: Path) -> None:
        paths = _seed_minimal_vault(tmp_path)
        audit_index_format_or_raise(paths)  # no exception

    def test_raises_on_failure(self, tmp_path: Path) -> None:
        paths = _seed_minimal_vault(tmp_path)
        (paths.vault_dir / "_bases" / "factors.base").unlink()
        with pytest.raises(IndexFormatError) as exc:
            audit_index_format_or_raise(paths)
        assert "factors.base" in str(exc.value)
