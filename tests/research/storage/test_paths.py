"""Tests for StoragePaths (new vault-first layout per refactor_plan §4)."""

from __future__ import annotations

from pathlib import Path

from research.storage.paths import StoragePaths


class TestStoragePathsBasics:
    def test_default_root(self) -> None:
        sp = StoragePaths()
        assert sp.root == Path("storage")

    def test_custom_root(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path / "custom")
        assert sp.root == tmp_path / "custom"

    def test_state_and_config_at_root(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path)
        assert sp.state_file == tmp_path / "state.yaml"
        assert sp.config_file == tmp_path / "config.yaml"


class TestVaultPaths:
    def test_vault_structure(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path)
        assert sp.evidence_dir == tmp_path / "evidence"
        assert sp.vault_dir == tmp_path / "evidence" / "vault"
        assert sp.vault_index_file == sp.vault_dir / "INDEX.md"
        assert sp.vault_lessons_file == sp.vault_dir / "lessons.md"
        assert sp.directions_dir == sp.vault_dir / "directions"
        assert sp.factors_dir == sp.vault_dir / "factors"
        assert sp.vault_meta_dir == sp.vault_dir / "_meta"

    def test_direction_file(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path)
        p = sp.direction_file("fundamental_price_divergence")
        assert p == sp.directions_dir / "fundamental_price_divergence.md"

    def test_factor_files(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path)
        assert sp.factor_yaml_file("F020") == sp.factors_dir / "F020.yaml"
        assert sp.factor_md_file("F020") == sp.factors_dir / "F020.md"
        assert sp.factor_assets_dir("F020") == sp.factors_dir / "F020"

    def test_consolidation_log(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path)
        assert sp.consolidation_log_file == sp.vault_meta_dir / "consolidation_log.md"


class TestBatchPaths:
    def test_batch_structure(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path)
        bd = sp.batch_dir("batch_042")
        assert bd == tmp_path / "batches" / "batch_042"
        assert sp.batch_manifest_file("batch_042") == bd / "manifest.yaml"
        assert sp.batch_result_file("batch_042") == bd / "result.yaml"
        assert sp.batch_judge_file("batch_042") == bd / "judge.md"
        assert sp.batch_python_candidates_dir("batch_042") == bd / "python_candidates"
        assert sp.batch_signals_dir("batch_042") == bd / "signals"
        assert sp.batch_packets_dir("batch_042") == bd / "_packets"

    def test_batch_signal_file(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path)
        p = sp.batch_signal_file("batch_042", "C003")
        assert p == sp.batches_dir / "batch_042" / "signals" / "C003.parquet"


class TestCachePaths:
    def test_cache_structure(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path)
        assert sp.cache_dir == tmp_path / "cache"
        assert sp.market_daily_cache == sp.cache_dir / "market_daily.parquet"
        assert sp.barra_factors_cache == sp.cache_dir / "barra_factors.parquet"
        assert sp.factor_values_cache_dir == sp.cache_dir / "factor_values"

    def test_factor_value_cache_key(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path)
        p = sp.factor_value_cache_file("deadbeef12")
        assert p == sp.factor_values_cache_dir / "deadbeef12.parquet"


class TestHoldoutAndPythonFactors:
    def test_holdout_private_location(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path)
        assert sp.holdout_private_dir == tmp_path / "_holdout_private"

    def test_holdout_review_file(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path)
        p = sp.holdout_review_file("2026-04-12")
        assert p == sp.holdout_private_dir / "review_2026-04-12.md"

    def test_python_factor_file(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path)
        p = sp.python_factor_file("F020", "triple_product_80d_pb")
        assert p == sp.python_factors_dir / "F020_triple_product_80d_pb.py"


class TestEnsureDirs:
    def test_all_dirs_created(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path / "fresh")
        sp.ensure_dirs()
        for d in sp.all_dirs():
            assert d.exists(), f"expected {d} to exist"
            assert d.is_dir()

    def test_ensure_dirs_is_idempotent(self, tmp_path: Path) -> None:
        sp = StoragePaths(tmp_path / "idem")
        sp.ensure_dirs()
        sp.ensure_dirs()  # must not raise
        for d in sp.all_dirs():
            assert d.exists()

    def test_all_dirs_excludes_per_batch(self, tmp_path: Path) -> None:
        """Per-batch dirs are created on demand in Phase 1, not by ensure_dirs."""
        sp = StoragePaths(tmp_path)
        listed = sp.all_dirs()
        # No batch-specific subdirs in the base list
        assert all("batch_" not in str(d) for d in listed)
