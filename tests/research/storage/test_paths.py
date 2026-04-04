"""Tests for research.storage.paths.StoragePaths."""

from __future__ import annotations

from pathlib import Path

from research.storage.paths import StoragePaths


class TestStoragePaths:
    """Verify path properties and directory creation."""

    def test_defaults_to_storage(self):
        paths = StoragePaths()
        assert paths.root == Path("storage")

    def test_custom_root(self):
        paths = StoragePaths(root="/tmp/my_store")
        assert paths.root == Path("/tmp/my_store")

    def test_state_paths(self):
        p = StoragePaths("s")
        assert p.research_state == Path("s/state/research_state.yaml")
        assert p.pending_holdout_queue == Path("s/state/pending_holdout_queue.yaml")

    def test_logic_paths(self):
        p = StoragePaths("s")
        assert p.logic_registry == Path("s/logic/registry.yaml")
        assert p.logic_cards_dir == Path("s/logic/cards")
        assert p.logic_card("L001") == Path("s/logic/cards/L001.yaml")
        assert p.logic_proposal("P021") == Path("s/logic/proposals/P021.yaml")
        assert p.logic_review("P021") == Path("s/logic/reviews/review_P021.yaml")
        assert p.logic_snapshot("schedule_20260405") == Path(
            "s/logic/snapshots/schedule_20260405.yaml"
        )

    def test_registry_paths(self):
        p = StoragePaths("s")
        assert p.factor_index == Path("s/registry/factors/index.yaml")
        assert p.factor_detail("001") == Path("s/registry/factors/factor_001.yaml")
        assert p.family_registry == Path("s/registry/families/family_registry.yaml")

    def test_policy_paths(self):
        p = StoragePaths("s")
        assert p.capability_registry == Path("s/policy/capability_registry.yaml")
        assert p.implementation_policy == Path("s/policy/implementation_policy.yaml")
        assert p.failure_taxonomy == Path("s/policy/failure_taxonomy.yaml")
        assert p.policy_upgrade_ledger == Path("s/policy/policy_upgrade_ledger.yaml")

    def test_ledger_paths(self):
        p = StoragePaths("s")
        assert p.search_ledger == Path("s/ledger/search_ledger.yaml")
        assert p.batch_usage == Path("s/ledger/batch_usage.yaml")
        assert p.holdout_review_ledger == Path("s/ledger/holdout_review_ledger.yaml")
        assert p.write_audit_log == Path("s/ledger/write_audit_log.yaml")

    def test_packet_path(self):
        p = StoragePaths("s")
        assert p.packet("PKT001") == Path("s/packets/PKT001.yaml")

    def test_candidate_paths(self):
        p = StoragePaths("s")
        assert p.batch_manifest("batch_042") == Path("s/candidates/batch_042.yaml")
        assert p.batch_idea_report("batch_042") == Path(
            "s/candidates/batch_042_idea_report.yaml"
        )

    def test_result_paths(self):
        p = StoragePaths("s")
        assert p.batch_result("batch_042") == Path("s/results/batch_042_result.yaml")
        assert p.batch_execute_report("batch_042") == Path(
            "s/results/batch_042_execute_report.yaml"
        )
        assert p.batch_judge_report("batch_042") == Path(
            "s/results/batch_042_judge_report.yaml"
        )

    def test_ensure_dirs(self, tmp_path: Path):
        p = StoragePaths(root=str(tmp_path / "store"))
        p.ensure_dirs()

        # Verify a selection of directories were created.
        assert p.state_dir.is_dir()
        assert p.logic_cards_dir.is_dir()
        assert p.logic_proposals_dir.is_dir()
        assert p.logic_reviews_dir.is_dir()
        assert p.logic_snapshots_dir.is_dir()
        assert p.factors_dir.is_dir()
        assert p.families_dir.is_dir()
        assert p.policy_dir.is_dir()
        assert p.ledger_dir.is_dir()
        assert p.packets_dir.is_dir()
        assert p.memory_dir.is_dir()
        assert p.results_dir.is_dir()
        assert p.candidates_dir.is_dir()
        assert p.notes_dir.is_dir()
        assert p.evaluation_profiles_dir.is_dir()

    def test_ensure_dirs_idempotent(self, tmp_path: Path):
        p = StoragePaths(root=str(tmp_path / "store"))
        p.ensure_dirs()
        p.ensure_dirs()  # Should not raise.
        assert p.state_dir.is_dir()
