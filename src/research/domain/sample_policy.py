"""Sample policy definitions.

Implements the data-split and validation-window protocol from
research_execute.md Section 3.3.

Key concepts
------------
* **SamplePolicy** — the top-level object that defines how data is split
  for a given evaluation round.
* **ValidationWindow** — a named sub-range within the active validation
  period (used for split-stability and expanding-window checks).
* **SupportWindow** — an additional independent time range used for
  out-of-sample robustness checks (support_validation_windows).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass(frozen=True)
class ValidationWindow:
    """A named sub-range for split-stability or expanding-window analysis.

    These windows are within the active validation period.  They are
    *not* holdout.
    """

    window_id: str
    start: date
    end: date
    label: str = ""

    def __post_init__(self) -> None:
        if self.start >= self.end:
            raise ValueError(
                f"ValidationWindow {self.window_id}: "
                f"start ({self.start}) must be before end ({self.end})"
            )

    @property
    def days(self) -> int:
        return (self.end - self.start).days


@dataclass(frozen=True)
class SupportWindow:
    """An additional independent out-of-sample segment.

    Support windows sit outside the primary active_validation_range but
    inside the overall data span.  They are used for multi-period
    robustness checks.
    """

    window_id: str
    start: date
    end: date
    label: str = ""
    weight: float = 1.0  # importance weight in aggregation

    def __post_init__(self) -> None:
        if self.start >= self.end:
            raise ValueError(
                f"SupportWindow {self.window_id}: "
                f"start ({self.start}) must be before end ({self.end})"
            )

    @property
    def days(self) -> int:
        return (self.end - self.start).days


@dataclass(frozen=True)
class SamplePolicy:
    """Defines the full data-split protocol for one evaluation round.

    Attributes
    ----------
    validation_window_id : str
        Human-readable identifier for the active evaluation window.
    data_start : date
        Earliest data row allowed in any computation.
    active_train_range : tuple of (date, date)
        ``(start, end)`` of the training period.
    active_validation_range : tuple of (date, date)
        ``(start, end)`` of the primary out-of-sample period.
    support_validation_windows : list of SupportWindow
        Optional additional OOS segments.
    holdout_pool_range : tuple of (date, date) or None
        Reserved holdout period.  Must never be touched during
        normal evaluation.
    holdout_used : bool
        Whether holdout was actually consumed in this round.
    """

    validation_window_id: str

    data_start: date
    active_train_range: tuple  # (date, date)
    active_validation_range: tuple  # (date, date)

    support_validation_windows: List[SupportWindow] = field(default_factory=list)

    holdout_pool_range: Optional[tuple] = None  # (date, date) or None
    holdout_used: bool = False

    def __post_init__(self) -> None:
        train_start, train_end = self.active_train_range
        val_start, val_end = self.active_validation_range

        if train_start >= train_end:
            raise ValueError("Train range start must be before end")
        if val_start >= val_end:
            raise ValueError("Validation range start must be before end")
        if val_start <= train_end:
            raise ValueError(
                f"Validation start ({val_start}) must be after "
                f"train end ({train_end})"
            )
        if self.holdout_pool_range is not None:
            ho_start, ho_end = self.holdout_pool_range
            if ho_start >= ho_end:
                raise ValueError("Holdout range start must be before end")
            if ho_start <= val_end:
                raise ValueError(
                    f"Holdout start ({ho_start}) must be after "
                    f"validation end ({val_end})"
                )

    # ------------------------------------------------------------------
    # Convenience
    # ------------------------------------------------------------------

    @property
    def train_start(self) -> date:
        return self.active_train_range[0]

    @property
    def train_end(self) -> date:
        return self.active_train_range[1]

    @property
    def validation_start(self) -> date:
        return self.active_validation_range[0]

    @property
    def validation_end(self) -> date:
        return self.active_validation_range[1]

    @classmethod
    def default(cls) -> SamplePolicy:
        """Return the standard A-share daily policy (train<=2023, val=2024, holdout=2025+)."""
        return cls(
            validation_window_id="std_2024",
            data_start=date(2015, 1, 1),
            active_train_range=(date(2015, 1, 1), date(2023, 12, 31)),
            active_validation_range=(date(2024, 1, 1), date(2024, 12, 31)),
            holdout_pool_range=(date(2025, 1, 1), date(2025, 12, 31)),
            holdout_used=False,
        )
