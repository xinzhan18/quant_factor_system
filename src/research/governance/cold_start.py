"""Cold-start policy: per-mechanism gradual unlock.

During the early phase of the research system the governance layer must
be conservative.  ``ColdStartPolicy`` encodes per-mechanism thresholds
that must be met before certain advanced operations are unlocked.

Minimum protection:
    The system is in cold-start mode when
    ``completed_batches < 5 OR admitted_count < 10``.

Per-mechanism unlock thresholds (from logic_plan.md):
    * family_overlap   -- requires family size >= 3
    * subspace          -- requires basis >= 2
    * promote_family    -- requires 2 completed batches
    * productive        -- cumulative admit threshold
    * saturated         -- cumulative no-progress threshold
    * dead              -- cumulative failure threshold
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class SystemCounts:
    """Snapshot of system-wide counters used for unlock decisions."""

    completed_batches: int = 0
    admitted_count: int = 0


@dataclass
class MechanismCounts:
    """Per-mechanism counters supplied by the caller."""

    family_size: int = 0
    subspace_basis: int = 0
    promote_family_batches: int = 0
    cumulative_admits: int = 0
    cumulative_no_progress_batches: int = 0
    cumulative_failure_batches: int = 0


# Default thresholds for each mechanism
_DEFAULT_THRESHOLDS: Dict[str, int] = {
    "family_overlap": 3,        # family_size >= 3
    "subspace": 2,              # subspace_basis >= 2
    "promote_family": 2,        # completed batches within family >= 2
    "productive": 3,            # cumulative_admits >= 3
    "saturated": 5,             # cumulative_no_progress >= 5
    "dead": 8,                  # cumulative_failure >= 8
}


class ColdStartPolicy:
    """Per-mechanism gradual-unlock policy.

    Parameters
    ----------
    thresholds : dict, optional
        Override default thresholds.  Keys are mechanism names;
        values are integer minimums.
    min_batches : int
        System-level minimum completed batches before *any* mechanism
        can unlock.
    min_admits : int
        System-level minimum admitted factor count.
    """

    def __init__(
        self,
        thresholds: Optional[Dict[str, int]] = None,
        min_batches: int = 5,
        min_admits: int = 10,
    ) -> None:
        self._thresholds = dict(_DEFAULT_THRESHOLDS)
        if thresholds:
            self._thresholds.update(thresholds)
        self._min_batches = min_batches
        self._min_admits = min_admits

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def thresholds(self) -> Dict[str, int]:
        """Return a copy of the active thresholds."""
        return dict(self._thresholds)

    def in_cold_start(self, system: SystemCounts) -> bool:
        """Return True when the system is still in cold-start mode."""
        return (
            system.completed_batches < self._min_batches
            or system.admitted_count < self._min_admits
        )

    def is_unlocked(
        self,
        mechanism: str,
        system: SystemCounts,
        mechanism_counts: MechanismCounts,
    ) -> bool:
        """Return True if *mechanism* is unlocked given current counters.

        If the system is still in cold-start mode, **all** mechanisms
        are locked regardless of per-mechanism counters.
        """
        if self.in_cold_start(system):
            return False

        threshold = self._thresholds.get(mechanism)
        if threshold is None:
            # Unknown mechanism -- conservative default: locked.
            return False

        counter = self._counter_for(mechanism, mechanism_counts)
        return counter >= threshold

    def check_all(
        self,
        system: SystemCounts,
        mechanism_counts: MechanismCounts,
    ) -> Dict[str, bool]:
        """Return unlock status for every known mechanism."""
        return {
            name: self.is_unlocked(name, system, mechanism_counts)
            for name in self._thresholds
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _counter_for(mechanism: str, mc: MechanismCounts) -> int:
        _MAP = {
            "family_overlap": mc.family_size,
            "subspace": mc.subspace_basis,
            "promote_family": mc.promote_family_batches,
            "productive": mc.cumulative_admits,
            "saturated": mc.cumulative_no_progress_batches,
            "dead": mc.cumulative_failure_batches,
        }
        return _MAP.get(mechanism, 0)
