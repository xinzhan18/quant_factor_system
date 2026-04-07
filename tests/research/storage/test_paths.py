"""Tests for StoragePaths."""

from __future__ import annotations

from pathlib import Path

from research.storage.paths import StoragePaths


class TestStoragePaths:
    """Verify path construction and directory creation."""

    def test_default_root(self) -> None:
        sp = StoragePaths()
        assert sp.root == Path("storage")

    def test_custom_root(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path / "custom")
        assert sp.root == tmp_path / "custom"

    def test_top_level_dirs(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path / "s")
        expected_names = {
            "state", "logic", "registry", "governance",
            "batches", "evidence", "runtime",
        }
        # Each property should return a child of root
        for name in expected_names:
            prop = getattr(sp, f"{name}_dir")
            assert prop.parent == sp.root, f"{name}_dir parent mismatch"

    def test_ensure_dirs_creates_all(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path / "s")
        assert not sp.root.exists()
        sp.ensure_dirs()
        for d in sp.all_dirs():
            assert d.is_dir(), f"expected directory: {d}"

    def test_ensure_dirs_idempotent(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path / "s")
        sp.ensure_dirs()
        sp.ensure_dirs()  # should not raise
        assert sp.state_dir.is_dir()

    def test_concrete_file_paths(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path / "s")
        assert sp.research_state_file == sp.state_dir / "research_state.yaml"
        assert sp.logic_reflection_file("L001") == sp.logic_reflections_dir / "L001.md"
        assert sp.factor_index_file == sp.factors_dir / "index.yaml"
        assert sp.research_config_file == sp.governance_dir / "research_config.yaml"
        assert sp.ledger_file == sp.governance_dir / "ledger.yaml"
        assert sp.global_escalation_file == sp.ledger_file

    def test_dynamic_paths(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path / "s")
        assert sp.logic_card_file("L001") == sp.logic_cards_dir / "L001.yaml"
        assert sp.factor_detail_file("F013") == sp.factors_dir / "factor_F013.yaml"
        bd = sp.batch_dir("batch_042")
        assert bd == sp.batches_dir / "batch_042"
        assert sp.judge_packet_file("batch_042") == bd / "judge_packet.yaml"
        assert sp.result_file("batch_042") == bd / "research_result.yaml"
        assert sp.batch_manifest_file("batch_042") == bd / "manifest.yaml"
        assert sp.idea_report_file("batch_042") == bd / "idea_report.yaml"

    def test_all_dirs_returns_list(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path / "s")
        dirs = sp.all_dirs()
        assert isinstance(dirs, list)
        assert len(dirs) >= 10
        assert all(isinstance(d, Path) for d in dirs)
