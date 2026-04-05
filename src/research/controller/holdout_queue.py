"""Holdout queue -- track pending holdout reviews with deadlines.

Rules:
    - Deadline: 1 batch or 7 days, whichever comes first
    - Supersede: same logic+family candidate replaces older entry
    - Expire: past deadline entries become expired_holdout_pending
    - No infinite resurrection: expired entries stay expired

Storage: simple YAML at storage/state/pending_holdout_queue.yaml
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import yaml

DEFAULT_DEADLINE_DAYS = 7


@dataclass
class HoldoutEntry:
    """A single pending holdout review entry."""

    candidate_id: str = ""
    logic_id: str = ""
    family_id: str = ""
    experiment_lineage_tag: str = ""
    batch_id: str = ""
    enqueued_at: str = ""
    deadline: str = ""
    status: str = "pending"  # pending / expired / superseded / reviewed

    def to_dict(self) -> Dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "logic_id": self.logic_id,
            "family_id": self.family_id,
            "experiment_lineage_tag": self.experiment_lineage_tag,
            "batch_id": self.batch_id,
            "enqueued_at": self.enqueued_at,
            "deadline": self.deadline,
            "status": self.status,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HoldoutEntry":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class HoldoutQueue:
    """Manage pending holdout review entries."""

    def __init__(self, entries: Optional[List[HoldoutEntry]] = None) -> None:
        self._entries: List[HoldoutEntry] = list(entries or [])

    @property
    def entries(self) -> List[HoldoutEntry]:
        return list(self._entries)

    def pending(self) -> List[HoldoutEntry]:
        """Return only pending (not expired/superseded/reviewed) entries."""
        return [e for e in self._entries if e.status == "pending"]

    def enqueue(
        self,
        candidate_id: str,
        logic_id: str,
        family_id: str,
        batch_id: str,
        experiment_lineage_tag: str = "",
        now: Optional[datetime] = None,
    ) -> HoldoutEntry:
        """Add a candidate to the holdout queue.

        If an existing pending entry has the same logic_id + family_id,
        it is superseded by the new entry.
        """
        now = now or datetime.now()
        deadline = now + timedelta(days=DEFAULT_DEADLINE_DAYS)

        # Supersede older entries with same logic+family
        for entry in self._entries:
            if (
                entry.status == "pending"
                and entry.logic_id == logic_id
                and entry.family_id == family_id
                and entry.candidate_id != candidate_id
            ):
                entry.status = "superseded"

        new_entry = HoldoutEntry(
            candidate_id=candidate_id,
            logic_id=logic_id,
            family_id=family_id,
            experiment_lineage_tag=experiment_lineage_tag,
            batch_id=batch_id,
            enqueued_at=now.strftime("%Y-%m-%d %H:%M:%S"),
            deadline=deadline.strftime("%Y-%m-%d %H:%M:%S"),
            status="pending",
        )
        self._entries.append(new_entry)
        return new_entry

    def expire_past_deadline(self, now: Optional[datetime] = None) -> int:
        """Mark pending entries past their deadline as expired.

        Returns:
            Number of entries expired.
        """
        now = now or datetime.now()
        expired_count = 0
        for entry in self._entries:
            if entry.status != "pending":
                continue
            try:
                dl = datetime.strptime(entry.deadline, "%Y-%m-%d %H:%M:%S")
                if now > dl:
                    entry.status = "expired"
                    expired_count += 1
            except ValueError:
                continue
        return expired_count

    def mark_reviewed(self, candidate_id: str) -> bool:
        """Mark an entry as reviewed. Returns True if found."""
        for entry in self._entries:
            if entry.candidate_id == candidate_id and entry.status == "pending":
                entry.status = "reviewed"
                return True
        return False

    def to_dict_list(self) -> List[Dict[str, Any]]:
        """Serialize all entries."""
        return [e.to_dict() for e in self._entries]

    @classmethod
    def from_dict_list(cls, data: List[Dict[str, Any]]) -> "HoldoutQueue":
        """Deserialize from a list of dicts."""
        entries = [HoldoutEntry.from_dict(d) for d in data]
        return cls(entries=entries)

    def save_yaml(self, path: str) -> None:
        """Persist queue to YAML file."""
        from pathlib import Path

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.safe_dump(
                {"holdout_queue": self.to_dict_list()},
                f,
                default_flow_style=False,
                allow_unicode=True,
            )

    @classmethod
    def load_yaml(cls, path: str) -> "HoldoutQueue":
        """Load queue from YAML file."""
        from pathlib import Path

        p = Path(path)
        if not p.exists():
            return cls()
        with open(p, "r") as f:
            data = yaml.safe_load(f) or {}
        entries_data = data.get("holdout_queue", [])
        return cls.from_dict_list(entries_data)
