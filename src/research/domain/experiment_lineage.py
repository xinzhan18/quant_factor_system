"""Experiment lineage tag generation and normalization.

Format (from idea_plan.md Section 6.1):

    ELT_{logic_id}_{route_type}_{mechanism_anchor}_{conditioning_anchor}_{family_anchor}_v{version}

Example:

    ELT_L021_genesis_breakout_compression_fm_breakout_v1

Normalization rules:
  - lowercase
  - replace whitespace / hyphens with underscores
  - sort multi-valued anchors alphabetically
  - strip leading/trailing underscores
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Sequence


def _normalize_anchor(raw: str) -> str:
    """Lowercase, replace non-alphanumeric with underscore, strip edges."""
    s = raw.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


def _sort_anchors(anchors: Sequence[str]) -> str:
    """Normalize each anchor, sort alphabetically, join with underscore."""
    parts = sorted(_normalize_anchor(a) for a in anchors if a)
    return "_".join(parts) if parts else "none"


@dataclass(frozen=True)
class ExperimentLineageTag:
    """Immutable experiment lineage tag.

    Use the ``generate`` classmethod to build validated tags.
    """

    logic_id: str
    route_type: str
    mechanism_anchors: tuple  # sorted, normalized
    conditioning_anchors: tuple  # sorted, normalized
    family_anchor: str
    version: int

    # ------------------------------------------------------------------
    # Construction
    # ------------------------------------------------------------------

    @classmethod
    def generate(
        cls,
        logic_id: str,
        route_type: str,
        mechanism_anchors: Sequence[str],
        conditioning_anchors: Optional[Sequence[str]] = None,
        family_anchor: str = "",
        version: int = 1,
    ) -> ExperimentLineageTag:
        """Build a validated, normalized tag.

        Parameters
        ----------
        logic_id : str
            e.g. ``"L021"``
        route_type : str
            One of genesis / mutate / crossover / repair / decorrelate.
        mechanism_anchors : sequence of str
            Core mechanism keywords (at least one required).
        conditioning_anchors : sequence of str or None
            Optional conditioning keywords.
        family_anchor : str
            Factor family identifier (e.g. ``"FM_breakout"``).
        version : int
            Tag version, monotonically increasing within same prefix.
        """
        if not mechanism_anchors:
            raise ValueError("At least one mechanism anchor is required.")
        if version < 1:
            raise ValueError(f"Version must be >= 1, got {version}")

        mech = tuple(sorted(_normalize_anchor(a) for a in mechanism_anchors if a))
        cond = tuple(
            sorted(_normalize_anchor(a) for a in (conditioning_anchors or []) if a)
        )
        fam = _normalize_anchor(family_anchor) if family_anchor else "none"

        return cls(
            logic_id=_normalize_anchor(logic_id),
            route_type=_normalize_anchor(route_type),
            mechanism_anchors=mech,
            conditioning_anchors=cond,
            family_anchor=fam,
            version=version,
        )

    # ------------------------------------------------------------------
    # Serialization
    # ------------------------------------------------------------------

    @property
    def tag(self) -> str:
        """Canonical string representation."""
        mech_str = "_".join(self.mechanism_anchors) if self.mechanism_anchors else "none"
        cond_str = "_".join(self.conditioning_anchors) if self.conditioning_anchors else "none"
        return (
            f"ELT_{self.logic_id}_{self.route_type}"
            f"_{mech_str}_{cond_str}_{self.family_anchor}_v{self.version}"
        )

    def __str__(self) -> str:  # pragma: no cover
        return self.tag

    # ------------------------------------------------------------------
    # Parsing
    # ------------------------------------------------------------------

    @classmethod
    def parse(cls, tag_str: str) -> ExperimentLineageTag:
        """Reconstruct from a canonical tag string.

        This is a best-effort parser for the fixed-structure format.
        """
        if not tag_str.startswith("ELT_"):
            raise ValueError(f"Tag must start with 'ELT_', got: {tag_str!r}")

        # Strip prefix and version suffix
        body = tag_str[4:]  # remove "ELT_"
        m = re.search(r"_v(\d+)$", body)
        if not m:
            raise ValueError(f"Tag must end with '_v<N>', got: {tag_str!r}")
        version = int(m.group(1))
        body = body[: m.start()]

        # Split remaining into parts: logic_id, route_type, then anchors
        parts = body.split("_")
        if len(parts) < 2:
            raise ValueError(f"Tag too short after removing prefix/version: {tag_str!r}")

        logic_id = parts[0]
        route_type = parts[1]

        # The remaining parts need to be split into mechanism, conditioning, family.
        # This is ambiguous in the general case. We use "none" as sentinel for missing sections.
        remaining = parts[2:]

        # Find the family anchor (last non-"none" segment before version).
        # Convention: family_anchor is always the last segment before _v{N}.
        if remaining:
            family_anchor = remaining[-1]
            middle = remaining[:-1]
        else:
            family_anchor = "none"
            middle = []

        # Split middle into mechanism and conditioning by "none" separator.
        # If "none" appears, it splits mech from cond.
        if "none" in middle:
            idx = middle.index("none")
            mech = tuple(middle[:idx]) if middle[:idx] else ("none",)
            cond = tuple(middle[idx + 1 :]) if middle[idx + 1 :] else ()
        else:
            mech = tuple(middle) if middle else ("none",)
            cond = ()

        return cls(
            logic_id=logic_id,
            route_type=route_type,
            mechanism_anchors=mech,
            conditioning_anchors=cond,
            family_anchor=family_anchor,
            version=version,
        )

    # ------------------------------------------------------------------
    # Versioning
    # ------------------------------------------------------------------

    def next_version(self) -> ExperimentLineageTag:
        """Return a copy with version incremented by one."""
        return ExperimentLineageTag(
            logic_id=self.logic_id,
            route_type=self.route_type,
            mechanism_anchors=self.mechanism_anchors,
            conditioning_anchors=self.conditioning_anchors,
            family_anchor=self.family_anchor,
            version=self.version + 1,
        )
