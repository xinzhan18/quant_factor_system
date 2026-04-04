"""StoragePaths — all path constants for the research storage tree.

Every directory and well-known file is exposed as a ``@property`` so that
consuming code never hard-codes path strings.  Call :meth:`ensure_dirs` once
at startup to create the full directory skeleton.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class StoragePaths:
    """Centralised path registry for ``storage/``."""

    def __init__(self, root: str = "storage") -> None:
        self.root = Path(root)

    # ------------------------------------------------------------------
    # state/
    # ------------------------------------------------------------------
    @property
    def state_dir(self) -> Path:
        return self.root / "state"

    @property
    def research_state(self) -> Path:
        return self.state_dir / "research_state.yaml"

    @property
    def pending_holdout_queue(self) -> Path:
        return self.state_dir / "pending_holdout_queue.yaml"

    # ------------------------------------------------------------------
    # logic/
    # ------------------------------------------------------------------
    @property
    def logic_dir(self) -> Path:
        return self.root / "logic"

    @property
    def logic_registry(self) -> Path:
        return self.logic_dir / "registry.yaml"

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

    # ------------------------------------------------------------------
    # registry/  (factors + families)
    # ------------------------------------------------------------------
    @property
    def registry_dir(self) -> Path:
        return self.root / "registry"

    @property
    def factors_dir(self) -> Path:
        return self.registry_dir / "factors"

    @property
    def factor_index(self) -> Path:
        return self.factors_dir / "index.yaml"

    @property
    def families_dir(self) -> Path:
        return self.registry_dir / "families"

    @property
    def family_registry(self) -> Path:
        return self.families_dir / "family_registry.yaml"

    # ------------------------------------------------------------------
    # policy/
    # ------------------------------------------------------------------
    @property
    def policy_dir(self) -> Path:
        return self.root / "policy"

    @property
    def capability_registry(self) -> Path:
        return self.policy_dir / "capability_registry.yaml"

    @property
    def implementation_policy(self) -> Path:
        return self.policy_dir / "implementation_policy.yaml"

    @property
    def failure_taxonomy(self) -> Path:
        return self.policy_dir / "failure_taxonomy.yaml"

    @property
    def policy_upgrade_ledger(self) -> Path:
        return self.policy_dir / "policy_upgrade_ledger.yaml"

    # ------------------------------------------------------------------
    # ledger/
    # ------------------------------------------------------------------
    @property
    def ledger_dir(self) -> Path:
        return self.root / "ledger"

    @property
    def search_ledger(self) -> Path:
        return self.ledger_dir / "search_ledger.yaml"

    @property
    def batch_usage(self) -> Path:
        return self.ledger_dir / "batch_usage.yaml"

    @property
    def holdout_review_ledger(self) -> Path:
        return self.ledger_dir / "holdout_review_ledger.yaml"

    @property
    def write_audit_log(self) -> Path:
        return self.ledger_dir / "write_audit_log.yaml"

    # ------------------------------------------------------------------
    # packets/
    # ------------------------------------------------------------------
    @property
    def packets_dir(self) -> Path:
        return self.root / "packets"

    # ------------------------------------------------------------------
    # memory/
    # ------------------------------------------------------------------
    @property
    def memory_dir(self) -> Path:
        return self.root / "memory"

    @property
    def forbidden(self) -> Path:
        return self.memory_dir / "forbidden.yaml"

    # ------------------------------------------------------------------
    # results/
    # ------------------------------------------------------------------
    @property
    def results_dir(self) -> Path:
        return self.root / "results"

    # ------------------------------------------------------------------
    # candidates/
    # ------------------------------------------------------------------
    @property
    def candidates_dir(self) -> Path:
        return self.root / "candidates"

    # ------------------------------------------------------------------
    # notes/
    # ------------------------------------------------------------------
    @property
    def notes_dir(self) -> Path:
        return self.root / "notes"

    # ------------------------------------------------------------------
    # evaluation_profiles/
    # ------------------------------------------------------------------
    @property
    def evaluation_profiles_dir(self) -> Path:
        return self.root / "evaluation_profiles"

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def factor_detail(self, factor_id: str) -> Path:
        """Path to a single factor detail YAML, e.g. ``factor_001.yaml``."""
        return self.factors_dir / f"factor_{factor_id}.yaml"

    def logic_card(self, logic_id: str) -> Path:
        """Path to a single logic card, e.g. ``L001.yaml``."""
        return self.logic_cards_dir / f"{logic_id}.yaml"

    def logic_proposal(self, proposal_id: str) -> Path:
        return self.logic_proposals_dir / f"{proposal_id}.yaml"

    def logic_review(self, proposal_id: str) -> Path:
        return self.logic_reviews_dir / f"review_{proposal_id}.yaml"

    def logic_snapshot(self, snapshot_name: str) -> Path:
        return self.logic_snapshots_dir / f"{snapshot_name}.yaml"

    def batch_manifest(self, batch_id: str) -> Path:
        return self.candidates_dir / f"{batch_id}.yaml"

    def batch_idea_report(self, batch_id: str) -> Path:
        return self.candidates_dir / f"{batch_id}_idea_report.yaml"

    def batch_result(self, batch_id: str) -> Path:
        return self.results_dir / f"{batch_id}_result.yaml"

    def batch_execute_report(self, batch_id: str) -> Path:
        return self.results_dir / f"{batch_id}_execute_report.yaml"

    def batch_judge_report(self, batch_id: str) -> Path:
        return self.results_dir / f"{batch_id}_judge_report.yaml"

    def packet(self, packet_id: str) -> Path:
        return self.packets_dir / f"{packet_id}.yaml"

    # ------------------------------------------------------------------
    # directory creation
    # ------------------------------------------------------------------
    _ALL_DIRS_ATTRS = [
        "state_dir",
        "logic_dir",
        "logic_proposals_dir",
        "logic_reviews_dir",
        "logic_cards_dir",
        "logic_snapshots_dir",
        "registry_dir",
        "factors_dir",
        "families_dir",
        "policy_dir",
        "ledger_dir",
        "packets_dir",
        "memory_dir",
        "results_dir",
        "candidates_dir",
        "notes_dir",
        "evaluation_profiles_dir",
    ]

    def ensure_dirs(self) -> None:
        """Create every directory in the storage tree (idempotent)."""
        for attr in self._ALL_DIRS_ATTRS:
            path: Path = getattr(self, attr)
            path.mkdir(parents=True, exist_ok=True)
        logger.debug("Storage directories ensured under %s", self.root)
