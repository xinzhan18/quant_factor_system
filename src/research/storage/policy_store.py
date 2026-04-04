"""Policy objects CRUD.

Manages:
- ``policy/capability_registry.yaml``
- ``policy/implementation_policy.yaml``
- ``policy/failure_taxonomy.yaml``
- ``policy/policy_upgrade_ledger.yaml``
"""

from __future__ import annotations

import logging
from typing import List

from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml, save_yaml

logger = logging.getLogger(__name__)


class PolicyStore:
    """CRUD for the four policy files."""

    def __init__(self, paths: StoragePaths) -> None:
        self.paths = paths

    # ------------------------------------------------------------------
    # capability registry
    # ------------------------------------------------------------------
    def load_capability(self) -> dict:
        """Load capability registry."""
        return load_yaml(self.paths.capability_registry)

    def save_capability(self, data: dict) -> None:
        save_yaml(self.paths.capability_registry, data)

    # ------------------------------------------------------------------
    # implementation policy
    # ------------------------------------------------------------------
    def load_implementation(self) -> dict:
        """Load implementation policy."""
        return load_yaml(self.paths.implementation_policy)

    def save_implementation(self, data: dict) -> None:
        save_yaml(self.paths.implementation_policy, data)

    # ------------------------------------------------------------------
    # failure taxonomy
    # ------------------------------------------------------------------
    def load_failure_taxonomy(self) -> dict:
        """Load failure taxonomy."""
        return load_yaml(self.paths.failure_taxonomy)

    def save_failure_taxonomy(self, data: dict) -> None:
        save_yaml(self.paths.failure_taxonomy, data)

    def list_failure_types(self) -> List[str]:
        """Return the list of known failure type names."""
        tax = self.load_failure_taxonomy()
        return tax.get("failure_types", [])

    # ------------------------------------------------------------------
    # policy upgrade ledger
    # ------------------------------------------------------------------
    def load_upgrade_ledger(self) -> dict:
        """Load the policy upgrade ledger."""
        return load_yaml(self.paths.policy_upgrade_ledger)

    def save_upgrade_ledger(self, data: dict) -> None:
        save_yaml(self.paths.policy_upgrade_ledger, data)

    def append_upgrade_entry(self, entry: dict) -> None:
        """Append a single upgrade entry to the ledger."""
        ledger = self.load_upgrade_ledger()
        entries: list = ledger.setdefault("entries", [])
        entries.append(entry)
        self.save_upgrade_ledger(ledger)
