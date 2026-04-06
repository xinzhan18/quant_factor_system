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
    # Top-level directories (7)
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
    def governance_dir(self) -> Path:
        return self.root / "governance"

    @property
    def batches_dir(self) -> Path:
        return self.root / "batches"

    @property
    def evidence_dir(self) -> Path:
        return self.root / "evidence"

    @property
    def runtime_dir(self) -> Path:
        return self.root / "runtime"

    # ------------------------------------------------------------------
    # Sub-directories
    # ------------------------------------------------------------------

    # logic/
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

    # registry/
    @property
    def factors_dir(self) -> Path:
        return self.registry_dir / "factors"

    @property
    def families_dir(self) -> Path:
        return self.registry_dir / "families"

    # evidence/
    @property
    def vault_dir(self) -> Path:
        return self.evidence_dir / "vault"

    @property
    def vault_assets_dir(self) -> Path:
        return self.vault_dir / "assets"

    @property
    def vault_factors_dir(self) -> Path:
        return self.vault_dir / "factors"

    # runtime/
    @property
    def cache_dir(self) -> Path:
        return self.runtime_dir / "cache"

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
        """Derived cache — authoritative source is cards/*.yaml."""
        return self.logic_dir / "registry.yaml"

    # registry/
    @property
    def factor_index_file(self) -> Path:
        return self.factors_dir / "index.yaml"

    @property
    def family_registry_file(self) -> Path:
        return self.families_dir / "family_registry.yaml"

    # governance/
    @property
    def ledger_file(self) -> Path:
        return self.governance_dir / "ledger.yaml"

    @property
    def research_config_file(self) -> Path:
        return self.governance_dir / "research_config.yaml"

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

    @property
    def logic_reflections_dir(self) -> Path:
        return self.logic_dir / "reflections"

    def logic_reflection_file(self, logic_id: str) -> Path:
        return self.logic_reflections_dir / f"{logic_id}.md"

    @property
    def global_escalation_file(self) -> Path:
        return self.root / "state" / "global_escalation.yaml"

    def factor_detail_file(self, factor_id: str) -> Path:
        return self.factors_dir / f"factor_{factor_id}.yaml"

    # batch — per-batch subdirectory
    def batch_dir(self, batch_id: str) -> Path:
        return self.batches_dir / batch_id

    def batch_manifest_file(self, batch_id: str) -> Path:
        return self.batch_dir(batch_id) / "manifest.yaml"

    def idea_report_file(self, batch_id: str) -> Path:
        return self.batch_dir(batch_id) / "idea_report.yaml"

    def result_file(self, batch_id: str) -> Path:
        return self.batch_dir(batch_id) / "research_result.yaml"

    def execute_report_file(self, batch_id: str) -> Path:
        return self.batch_dir(batch_id) / "execute_report.yaml"

    def judge_packet_file(self, batch_id: str) -> Path:
        return self.batch_dir(batch_id) / "judge_packet.yaml"

    def context_snapshot_file(self, batch_id: str) -> Path:
        return self.batch_dir(batch_id) / "context_snapshot.yaml"

    def judge_report_file(self, batch_id: str) -> Path:
        return self.batch_dir(batch_id) / "judge_report.yaml"

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
            self.logic_reflections_dir,
            self.registry_dir,
            self.factors_dir,
            self.families_dir,
            self.governance_dir,
            self.batches_dir,
            self.vault_dir,
            self.vault_assets_dir,
            self.vault_factors_dir,
            self.cache_dir,
        ]

    def ensure_dirs(self) -> None:
        """Create every directory in the storage tree (idempotent)."""
        for d in self.all_dirs():
            d.mkdir(parents=True, exist_ok=True)
