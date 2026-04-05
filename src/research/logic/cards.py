"""LogicCard CRUD — persisted as YAML under ``storage/logic/cards/``.

A LogicCard represents a formally reviewed and admitted market hypothesis.
It contains the exploration contract that constrains downstream ``/idea``
generation.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from research.logic._yaml_utils import dump_yaml, now_ts

logger = logging.getLogger(__name__)

VALID_STATUSES = frozenset(
    {"proposed", "active", "warm", "productive", "saturated", "parked", "dead"}
)
VALID_PRIORITIES = frozenset({"high", "medium", "low"})


@dataclass
class ExplorationContract:
    """Defines what /idea is allowed to explore under this logic."""

    focus_question: str = ""
    direction_quota: int = 2
    candidate_quota: int = 4
    families: List[str] = field(default_factory=list)
    suggested_ops: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    avoid_patterns: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "focus_question": self.focus_question,
            "direction_quota": self.direction_quota,
            "candidate_quota": self.candidate_quota,
            "families": self.families,
            "suggested_ops": self.suggested_ops,
            "required_fields": self.required_fields,
            "avoid_patterns": self.avoid_patterns,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExplorationContract":
        return cls(
            focus_question=data.get("focus_question", ""),
            direction_quota=data.get("direction_quota", 2),
            candidate_quota=data.get("candidate_quota", 4),
            families=data.get("families", []),
            suggested_ops=data.get("suggested_ops", []),
            required_fields=data.get("required_fields", []),
            avoid_patterns=data.get("avoid_patterns", []),
        )


@dataclass
class LogicCard:
    """A formally admitted market logic hypothesis."""

    logic_id: str
    name: str
    category: str
    status: str  # one of VALID_STATUSES
    priority: str  # high / medium / low
    hypothesis: str
    contract: ExplorationContract = field(default_factory=ExplorationContract)
    discovery_budget: int = 10
    evidence_summary: Dict[str, Any] = field(default_factory=dict)
    search_ledger_ref: str = ""
    origin_proposal_id: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(
                f"Invalid status {self.status!r}; "
                f"must be one of {sorted(VALID_STATUSES)}"
            )
        if self.priority not in VALID_PRIORITIES:
            raise ValueError(
                f"Invalid priority {self.priority!r}; "
                f"must be one of {sorted(VALID_PRIORITIES)}"
            )
        ts = now_ts()
        if not self.created_at:
            self.created_at = ts
        if not self.updated_at:
            self.updated_at = ts

    def to_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "logic_id": self.logic_id,
            "name": self.name,
            "category": self.category,
            "status": self.status,
            "priority": self.priority,
            "hypothesis": self.hypothesis,
            "contract": self.contract.to_dict(),
            "discovery_budget": self.discovery_budget,
            "evidence_summary": self.evidence_summary,
            "search_ledger_ref": self.search_ledger_ref,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.origin_proposal_id:
            d["origin_proposal_id"] = self.origin_proposal_id
        return d

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogicCard":
        contract_data = data.get("contract", {})
        contract = (
            ExplorationContract.from_dict(contract_data)
            if contract_data
            else ExplorationContract()
        )
        return cls(
            logic_id=data["logic_id"],
            name=data["name"],
            category=data["category"],
            status=data["status"],
            priority=data["priority"],
            hypothesis=data["hypothesis"],
            contract=contract,
            discovery_budget=data.get("discovery_budget", 10),
            evidence_summary=data.get("evidence_summary", {}),
            search_ledger_ref=data.get("search_ledger_ref", ""),
            origin_proposal_id=data.get("origin_proposal_id"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )


class LogicCardStore:
    """YAML-backed CRUD store for LogicCard objects.

    Cards are stored at ``<cards_dir>/logic_<logic_id>.yaml``.
    A registry index is maintained at ``<storage_dir>/logic/registry.yaml``.
    """

    def __init__(self, storage_dir: Path) -> None:
        self._storage_dir = Path(storage_dir)
        self._cards_dir = self._storage_dir / "logic" / "cards"
        self._cards_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _card_path(self, logic_id: str) -> Path:
        return self._cards_dir / f"logic_{logic_id}.yaml"

    def _registry_path(self) -> Path:
        return self._storage_dir / "logic" / "registry.yaml"

    def _scan_ids(self) -> List[str]:
        pattern = re.compile(r"^logic_(L\d+)\.yaml$")
        ids: List[str] = []
        for p in self._cards_dir.iterdir():
            m = pattern.match(p.name)
            if m:
                ids.append(m.group(1))
        return sorted(ids)

    def _next_id(self) -> str:
        existing = self._scan_ids()
        if not existing:
            return "L001"
        nums = [int(lid[1:]) for lid in existing]
        return f"L{max(nums) + 1:03d}"

    def _update_registry(self) -> None:
        """Rebuild the registry index from card files."""
        entries: List[Dict[str, Any]] = []
        for lid in self._scan_ids():
            card = self.get(lid)
            if card:
                entries.append(
                    {
                        "logic_id": card.logic_id,
                        "name": card.name,
                        "category": card.category,
                        "status": card.status,
                        "priority": card.priority,
                    }
                )
        registry = {"logics": entries, "count": len(entries)}
        registry_path = self._registry_path()
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        dump_yaml(registry_path, registry)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create(
        self,
        *,
        name: str,
        category: str,
        status: str = "active",
        priority: str = "medium",
        hypothesis: str,
        contract: Optional[ExplorationContract] = None,
        discovery_budget: int = 10,
        origin_proposal_id: Optional[str] = None,
    ) -> LogicCard:
        """Create a new LogicCard with auto-incremented ID."""
        logic_id = self._next_id()
        card = LogicCard(
            logic_id=logic_id,
            name=name,
            category=category,
            status=status,
            priority=priority,
            hypothesis=hypothesis,
            contract=contract or ExplorationContract(),
            discovery_budget=discovery_budget,
            origin_proposal_id=origin_proposal_id,
        )
        self._save(card)
        logger.info("Created logic card %s: %s", logic_id, name)
        return card

    def get(self, logic_id: str) -> Optional[LogicCard]:
        """Load a single card by ID. Returns None if not found."""
        path = self._card_path(logic_id)
        if not path.exists():
            return None
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if not data:
            return None
        return LogicCard.from_dict(data)

    def list_cards(self, status: Optional[str] = None) -> List[LogicCard]:
        """Return all cards, optionally filtered by status."""
        cards: List[LogicCard] = []
        for lid in self._scan_ids():
            card = self.get(lid)
            if card is None:
                continue
            if status is None or card.status == status:
                cards.append(card)
        return cards

    def update(self, card: LogicCard) -> None:
        """Persist an updated card (must already exist)."""
        if not self._card_path(card.logic_id).exists():
            raise KeyError(f"Logic card {card.logic_id!r} not found")
        card.updated_at = now_ts()
        self._save(card)
        logger.debug("Updated logic card %s", card.logic_id)

    def delete(self, logic_id: str) -> bool:
        """Delete a card file. Returns True if deleted, False if not found."""
        path = self._card_path(logic_id)
        if not path.exists():
            return False
        path.unlink()
        self._update_registry()
        logger.info("Deleted logic card %s", logic_id)
        return True

    def _save(self, card: LogicCard) -> None:
        """Write card YAML and update registry index."""
        dump_yaml(self._card_path(card.logic_id), card.to_dict())
        self._update_registry()
