"""Append-only write audit log.

Every accepted or rejected write request is recorded in
``ledger/write_audit_log.yaml`` as an append-only trail.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

from research.governance._yaml_io import atomic_yaml_write, safe_yaml_load_list


@dataclass
class AuditEntry:
    """A single row in the audit log."""

    request_id: str
    timestamp: str
    actor: str
    level: str
    target: str
    action: str
    status: str  # accepted / rejected
    rejection_reason_codes: Optional[List[str]] = field(default=None)


class WriteAuditLog:
    """Append-only YAML audit log.

    Parameters
    ----------
    base_dir : Path
        Root storage directory.  The log lives at
        ``<base_dir>/ledger/write_audit_log.yaml``.
    """

    def __init__(self, base_dir: Path) -> None:
        self._base_dir = Path(base_dir)
        # Audit entries live inside ledger.yaml under write_audit_log.entries
        self._ledger_path = self._base_dir / "governance" / "ledger.yaml"

    @property
    def log_path(self) -> Path:
        return self._ledger_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append(self, entry: AuditEntry) -> None:
        """Append *entry* to the audit log section in ledger.yaml."""
        import yaml

        ledger = self._load_ledger()
        audit = ledger.setdefault("write_audit_log", {})
        entries = audit.setdefault("entries", [])
        entries.append(asdict(entry))
        self._save_ledger(ledger)

    def read_all(self) -> List[dict]:
        """Return every entry as a list of plain dicts."""
        ledger = self._load_ledger()
        return ledger.get("write_audit_log", {}).get("entries", [])

    def entries_for_request(self, request_id: str) -> List[dict]:
        """Return all entries matching *request_id*."""
        return [e for e in self.read_all() if e.get("request_id") == request_id]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load_ledger(self) -> dict:
        if not self._ledger_path.exists():
            return {}
        import yaml
        text = self._ledger_path.read_text(encoding="utf-8")
        return yaml.safe_load(text) or {}

    def _save_ledger(self, ledger: dict) -> None:
        atomic_yaml_write(self._ledger_path, ledger)

    @staticmethod
    def make_entry(
        request_id: str,
        actor: str,
        level: str,
        target: str,
        action: str,
        status: str,
        rejection_reason_codes: Optional[List[str]] = None,
    ) -> AuditEntry:
        """Convenience factory that fills in the timestamp."""
        return AuditEntry(
            request_id=request_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            actor=actor,
            level=level,
            target=target,
            action=action,
            status=status,
            rejection_reason_codes=rejection_reason_codes,
        )
