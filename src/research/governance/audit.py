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
        self._log_path = self._base_dir / "ledger" / "write_audit_log.yaml"

    @property
    def log_path(self) -> Path:
        return self._log_path

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append(self, entry: AuditEntry) -> None:
        """Append *entry* to the audit log atomically."""
        entries = self._load()
        entries.append(asdict(entry))
        self._save(entries)

    def read_all(self) -> List[dict]:
        """Return every entry as a list of plain dicts."""
        return self._load()

    def entries_for_request(self, request_id: str) -> List[dict]:
        """Return all entries matching *request_id*."""
        return [e for e in self._load() if e.get("request_id") == request_id]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _load(self) -> List[dict]:
        return safe_yaml_load_list(self._log_path)

    def _save(self, entries: List[dict]) -> None:
        atomic_yaml_write(self._log_path, entries)

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
