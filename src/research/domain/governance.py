"""Guarded-write protocol.

All persistent writes in the research system go through a guarded-write
request/receipt pair.  This provides an audit trail and prevents
accidental overwrites.

Write levels (in increasing severity):
  - APPEND   — add a new entry (e.g. new factor, new batch result)
  - UPDATE   — modify an existing entry (e.g. logic status change)
  - REPLACE  — replace one object with another (e.g. factor replacement)
  - ARCHIVE  — move an object to history before overwriting
  - DELETE   — remove an object (rare, requires explicit confirmation)
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class WriteLevel(enum.Enum):
    """Severity / type of a write operation."""

    APPEND = "append"
    UPDATE = "update"
    REPLACE = "replace"
    ARCHIVE = "archive"
    DELETE = "delete"


class WritableObject(enum.Enum):
    """Which persistent object is being written."""

    FACTOR_RECORD = "factor_record"
    LOGIC_CARD = "logic_card"
    ROUTE_CARD = "route_card"
    RESEARCH_STATE = "research_state"
    POLICY = "policy"
    FORBIDDEN = "forbidden"
    BATCH_RESULT = "batch_result"
    JUDGE_REPORT = "judge_report"
    SCHEDULE_SNAPSHOT = "schedule_snapshot"


@dataclass
class GuardedWriteRequest:
    """A request to perform a persistent write.

    Created by the caller (e.g. judge, admission service) and
    validated by the storage layer before execution.
    """

    request_id: str = ""
    object_type: str = ""  # matches WritableObject values
    write_level: str = ""  # matches WriteLevel values
    target_path: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)

    # Who / why
    requester: str = ""  # skill or service name
    reason: str = ""
    batch_id: Optional[str] = None

    requested_at: Optional[str] = None

    # Optional: for REPLACE / ARCHIVE operations
    archive_target_path: Optional[str] = None
    previous_version_ref: Optional[str] = None


@dataclass
class GuardedWriteReceipt:
    """Confirmation that a write was executed (or rejected).

    Returned by the storage layer after processing a
    ``GuardedWriteRequest``.
    """

    request_id: str = ""
    success: bool = False
    object_type: str = ""
    write_level: str = ""
    target_path: str = ""

    # Outcome details
    error: Optional[str] = None
    archive_path: Optional[str] = None  # if archiving was done

    executed_at: Optional[str] = None
