"""Policy / Forbidden / FailureTaxonomy / PolicyUpgradeLedger CRUD.

Manages the system's rule layer:
- ``policy/capability_registry.yaml``
- ``policy/implementation_policy.yaml``
- ``policy/failure_taxonomy.yaml``
- ``policy/policy_upgrade_ledger.yaml``
- ``memory/forbidden.yaml``
"""

from __future__ import annotations

from typing import Any

from .paths import StoragePaths
from .yaml_io import load_yaml, save_yaml


class PolicyStore:
    """CRUD for policy files, failure taxonomy, and forbidden patterns."""

    def __init__(self, paths: StoragePaths) -> None:
        self._paths = paths

    # ------------------------------------------------------------------
    # capability_registry.yaml
    # ------------------------------------------------------------------

    def load_capability_registry(self) -> dict[str, Any]:
        return load_yaml(self._paths.capability_registry_file)

    def save_capability_registry(self, data: dict[str, Any]) -> None:
        save_yaml(self._paths.capability_registry_file, data)

    # ------------------------------------------------------------------
    # implementation_policy.yaml
    # ------------------------------------------------------------------

    def load_implementation_policy(self) -> dict[str, Any]:
        return load_yaml(self._paths.implementation_policy_file)

    def save_implementation_policy(self, data: dict[str, Any]) -> None:
        save_yaml(self._paths.implementation_policy_file, data)

    # ------------------------------------------------------------------
    # failure_taxonomy.yaml
    # ------------------------------------------------------------------

    def load_failure_taxonomy(self) -> dict[str, Any]:
        return load_yaml(self._paths.failure_taxonomy_file)

    def save_failure_taxonomy(self, data: dict[str, Any]) -> None:
        save_yaml(self._paths.failure_taxonomy_file, data)

    # ------------------------------------------------------------------
    # policy_upgrade_ledger.yaml
    # ------------------------------------------------------------------

    def load_policy_upgrade_ledger(self) -> dict[str, Any]:
        return load_yaml(self._paths.policy_upgrade_ledger_file)

    def save_policy_upgrade_ledger(self, data: dict[str, Any]) -> None:
        save_yaml(self._paths.policy_upgrade_ledger_file, data)

    def append_policy_upgrade(self, entry: dict[str, Any]) -> None:
        """Append a policy-upgrade event to the ledger."""
        ledger = self.load_policy_upgrade_ledger()
        items = ledger.setdefault("upgrades", [])
        items.append(entry)
        self.save_policy_upgrade_ledger(ledger)

    # ------------------------------------------------------------------
    # memory/forbidden.yaml
    # ------------------------------------------------------------------

    def load_forbidden(self) -> dict[str, Any]:
        return load_yaml(self._paths.forbidden_file)

    def save_forbidden(self, data: dict[str, Any]) -> None:
        save_yaml(self._paths.forbidden_file, data)

    def append_forbidden_pattern(self, pattern: dict[str, Any]) -> None:
        """Append a forbidden pattern entry."""
        data = self.load_forbidden()
        items = data.setdefault("forbidden_patterns", [])
        items.append(pattern)
        self.save_forbidden(data)
