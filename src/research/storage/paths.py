"""StoragePaths: all path constants for the research storage tree.

Every directory and file path is a property relative to a configurable root.
``ensure_dirs()`` creates the full directory tree in one call.
"""

from __future__ import annotations

from pathlib import Path


class StoragePaths:
    """Centralised path registry for the research storage tree."""

    def __init__(self, root: str | Path = "storage") -> None:
        self.root = Path(root)

    # ------------------------------------------------------------------
    # Top-level directories
    # ------------------------------------------------------------------

    @property
    def state_dir(self) -> Path:
        return self.root / "state"

    @property
    def logic_dir(self) -> Path:
        return self.root / "logic"

    @property
    def registry_dir(self) -> Path:
        return self.root / "registry"

    @property
    def policy_dir(self) -> Path:
        return self.root / "policy"

    @property
    def ledger_dir(self) -> Path:
        return self.root / "ledger"

    @property
    def packets_dir(self) -> Path:
        return self.root / "packets"

    @property
    def memory_dir(self) -> Path:
        return self.root / "memory"

    @property
    def results_dir(self) -> Path:
        return self.root / "results"

    @property
    def candidates_dir(self) -> Path:
        return self.root / "candidates"

    @property
    def notes_dir(self) -> Path:
        return self.root / "notes"

    @property
    def evaluation_profiles_dir(self) -> Path:
        return self.root / "evaluation_profiles"

    # ------------------------------------------------------------------
    # Sub-directories
    # ------------------------------------------------------------------

    @property
    def logic_proposals_dir(self) -> Path:
        return self.logic_dir / "proposals"

    @property
    def logic_reviews_dir(self) -> Path:
        return self.logic_dir / "reviews"

    @property
    def logic_cards_dir(self) -> Path:
        return self.logic_dir / "cards"

    @property
    def logic_snapshots_dir(self) -> Path:
        return self.logic_dir / "snapshots"

    @property
    def factors_dir(self) -> Path:
        return self.registry_dir / "factors"

    @property
    def families_dir(self) -> Path:
        return self.registry_dir / "families"

    # ------------------------------------------------------------------
    # Concrete file paths
    # ------------------------------------------------------------------

    # state/
    @property
    def research_state_file(self) -> Path:
        return self.state_dir / "research_state.yaml"

    @property
    def pending_holdout_queue_file(self) -> Path:
        return self.state_dir / "pending_holdout_queue.yaml"

    # logic/
    @property
    def logic_registry_file(self) -> Path:
        return self.logic_dir / "registry.yaml"

    # registry/
    @property
    def factor_index_file(self) -> Path:
        return self.factors_dir / "index.yaml"

    @property
    def family_registry_file(self) -> Path:
        return self.families_dir / "family_registry.yaml"

    # policy/
    @property
    def capability_registry_file(self) -> Path:
        return self.policy_dir / "capability_registry.yaml"

    @property
    def implementation_policy_file(self) -> Path:
        return self.policy_dir / "implementation_policy.yaml"

    @property
    def failure_taxonomy_file(self) -> Path:
        return self.policy_dir / "failure_taxonomy.yaml"

    @property
    def policy_upgrade_ledger_file(self) -> Path:
        return self.policy_dir / "policy_upgrade_ledger.yaml"

    # ledger/
    @property
    def search_ledger_file(self) -> Path:
        return self.ledger_dir / "search_ledger.yaml"

    @property
    def batch_usage_file(self) -> Path:
        return self.ledger_dir / "batch_usage.yaml"

    @property
    def holdout_review_ledger_file(self) -> Path:
        return self.ledger_dir / "holdout_review_ledger.yaml"

    @property
    def write_audit_log_file(self) -> Path:
        return self.ledger_dir / "write_audit_log.yaml"

    # memory/
    @property
    def forbidden_file(self) -> Path:
        return self.memory_dir / "forbidden.yaml"

    # evaluation_profiles/
    @property
    def research_eval_v1_file(self) -> Path:
        return self.evaluation_profiles_dir / "research_eval_v1.yaml"

    # ------------------------------------------------------------------
    # Dynamic paths (depend on batch_id / factor_id / logic_id)
    # ------------------------------------------------------------------

    def logic_card_file(self, logic_id: str) -> Path:
        return self.logic_cards_dir / f"{logic_id}.yaml"

    def logic_proposal_file(self, proposal_id: str) -> Path:
        return self.logic_proposals_dir / f"{proposal_id}.yaml"

    def logic_review_file(self, proposal_id: str) -> Path:
        return self.logic_reviews_dir / f"review_{proposal_id}.yaml"

    def logic_snapshot_file(self, snapshot_name: str) -> Path:
        return self.logic_snapshots_dir / f"{snapshot_name}.yaml"

    def factor_detail_file(self, factor_id: str) -> Path:
        return self.factors_dir / f"factor_{factor_id}.yaml"

    def judge_packet_file(self, batch_id: str) -> Path:
        return self.packets_dir / f"{batch_id}_judge_packet.yaml"

    def context_snapshot_file(self, batch_id: str) -> Path:
        return self.packets_dir / f"{batch_id}_context_snapshot.yaml"

    def batch_manifest_file(self, batch_id: str) -> Path:
        return self.candidates_dir / f"{batch_id}.yaml"

    def idea_report_file(self, batch_id: str) -> Path:
        return self.candidates_dir / f"{batch_id}_idea_report.yaml"

    def result_file(self, batch_id: str) -> Path:
        return self.results_dir / f"{batch_id}_result.yaml"

    def execute_report_file(self, batch_id: str) -> Path:
        return self.results_dir / f"{batch_id}_execute_report.yaml"

    def judge_report_file(self, batch_id: str) -> Path:
        return self.results_dir / f"{batch_id}_judge_report.yaml"

    # ------------------------------------------------------------------
    # Directory creation
    # ------------------------------------------------------------------

    def all_dirs(self) -> list[Path]:
        """Return every directory that should exist in the storage tree."""
        return [
            self.state_dir,
            self.logic_dir,
            self.logic_proposals_dir,
            self.logic_reviews_dir,
            self.logic_cards_dir,
            self.logic_snapshots_dir,
            self.registry_dir,
            self.factors_dir,
            self.families_dir,
            self.policy_dir,
            self.ledger_dir,
            self.packets_dir,
            self.memory_dir,
            self.results_dir,
            self.candidates_dir,
            self.notes_dir,
            self.evaluation_profiles_dir,
        ]

    def ensure_dirs(self) -> None:
        """Create every directory in the storage tree (idempotent)."""
        for d in self.all_dirs():
            d.mkdir(parents=True, exist_ok=True)
