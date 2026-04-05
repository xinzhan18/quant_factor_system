"""LogicProposal creation and validation.

A proposal is a candidate market hypothesis that has not yet been reviewed.
Proposals are persisted as YAML in ``storage/logic/proposals/``.
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

VALID_ORIGIN_TYPES = frozenset(
    {
        "canonical",
        "empirical",
        "near_miss",
        "crossover",
        "external",
        "bottom_up",
        "repeated_residual",
    }
)

SCHEMA_VERSION = "v2"


@dataclass
class LogicProposal:
    """Immutable value object representing a logic proposal."""

    proposal_id: str
    name: str
    origin_type: str
    category: str
    thesis: str
    mechanism: str
    observable_proxy: Dict[str, Any] = field(default_factory=dict)
    expected_horizon: Dict[str, Any] = field(default_factory=dict)
    implementation_space: Dict[str, Any] = field(default_factory=dict)
    novelty_claim: str = ""
    probe_readiness: Dict[str, Any] = field(default_factory=dict)
    relations_guess: Dict[str, Any] = field(default_factory=dict)
    submitted_at: str = ""
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.origin_type not in VALID_ORIGIN_TYPES:
            raise ValueError(
                f"Invalid origin_type {self.origin_type!r}; "
                f"must be one of {sorted(VALID_ORIGIN_TYPES)}"
            )
        if not self.submitted_at:
            self.submitted_at = now_ts()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict suitable for YAML output."""
        return {
            "proposal_id": self.proposal_id,
            "schema_version": self.schema_version,
            "name": self.name,
            "origin_type": self.origin_type,
            "category": self.category,
            "thesis": self.thesis,
            "mechanism": self.mechanism,
            "observable_proxy": self.observable_proxy,
            "expected_horizon": self.expected_horizon,
            "implementation_space": self.implementation_space,
            "novelty_claim": self.novelty_claim,
            "probe_readiness": self.probe_readiness,
            "relations_guess": self.relations_guess,
            "submitted_at": self.submitted_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LogicProposal":
        """Deserialize from a plain dict (e.g. loaded from YAML)."""
        return cls(
            proposal_id=data["proposal_id"],
            name=data["name"],
            origin_type=data["origin_type"],
            category=data["category"],
            thesis=data["thesis"],
            mechanism=data["mechanism"],
            observable_proxy=data.get("observable_proxy", {}),
            expected_horizon=data.get("expected_horizon", {}),
            implementation_space=data.get("implementation_space", {}),
            novelty_claim=data.get("novelty_claim", ""),
            probe_readiness=data.get("probe_readiness", {}),
            relations_guess=data.get("relations_guess", {}),
            submitted_at=data.get("submitted_at", ""),
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )


def _next_proposal_id(proposals_dir: Path) -> str:
    """Auto-increment proposal ID based on existing files."""
    pattern = re.compile(r"^proposal_P(\d+)\.yaml$")
    max_num = 0
    if proposals_dir.exists():
        for p in proposals_dir.iterdir():
            m = pattern.match(p.name)
            if m:
                max_num = max(max_num, int(m.group(1)))
    return f"P{max_num + 1:03d}"


def create_proposal(
    storage_dir: Path,
    *,
    name: str,
    origin_type: str,
    category: str,
    thesis: str,
    mechanism: str,
    observable_proxy: Optional[Dict[str, Any]] = None,
    expected_horizon: Optional[Dict[str, Any]] = None,
    implementation_space: Optional[Dict[str, Any]] = None,
    novelty_claim: str = "",
    probe_readiness: Optional[Dict[str, Any]] = None,
    relations_guess: Optional[Dict[str, Any]] = None,
) -> LogicProposal:
    """Create a new proposal, persist it, and return the object.

    Parameters
    ----------
    storage_dir:
        Root storage directory (e.g. ``Path("storage")``).
        Proposals are written to ``storage_dir / "logic" / "proposals"``.
    """
    proposals_dir = storage_dir / "logic" / "proposals"
    proposals_dir.mkdir(parents=True, exist_ok=True)

    proposal_id = _next_proposal_id(proposals_dir)
    proposal = LogicProposal(
        proposal_id=proposal_id,
        name=name,
        origin_type=origin_type,
        category=category,
        thesis=thesis,
        mechanism=mechanism,
        observable_proxy=observable_proxy or {},
        expected_horizon=expected_horizon or {},
        implementation_space=implementation_space or {},
        novelty_claim=novelty_claim,
        probe_readiness=probe_readiness or {},
        relations_guess=relations_guess or {},
    )

    path = proposals_dir / f"proposal_{proposal_id}.yaml"
    dump_yaml(path, proposal.to_dict())
    logger.info("Created proposal %s at %s", proposal_id, path)
    return proposal


def load_proposal(storage_dir: Path, proposal_id: str) -> Optional[LogicProposal]:
    """Load a proposal by ID. Returns None if not found."""
    path = storage_dir / "logic" / "proposals" / f"proposal_{proposal_id}.yaml"
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return LogicProposal.from_dict(data)


def list_proposals(storage_dir: Path) -> List[LogicProposal]:
    """Return all proposals sorted by ID."""
    proposals_dir = storage_dir / "logic" / "proposals"
    if not proposals_dir.exists():
        return []
    results: List[LogicProposal] = []
    for p in sorted(proposals_dir.iterdir()):
        if p.suffix == ".yaml" and p.name.startswith("proposal_"):
            with open(p, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if data:
                results.append(LogicProposal.from_dict(data))
    return results
