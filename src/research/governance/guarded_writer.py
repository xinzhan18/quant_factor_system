"""GuardedWriter: validate write requests and execute or reject.

The writer enforces two access levels:

* **level_1** -- execute immediately and produce an audit receipt.
* **level_2** -- validate that *repeated evidence* exists
  (>= ``min_batches`` batches, >= ``min_routes`` routes, consistent
  reason codes) before writing to high-impact objects
  (``forbidden``).

Every request -- accepted or rejected -- is recorded in the
:class:`~research.governance.audit.WriteAuditLog`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from research.governance._yaml_io import atomic_yaml_write
from research.governance.audit import WriteAuditLog
from research.governance.permissions import (
    Actor,
    TargetObject,
    WriteLevel,
    actor_can_write,
    required_level,
)


# ------------------------------------------------------------------
# Request / Receipt data classes
# ------------------------------------------------------------------


@dataclass
class WriteRequest:
    """Describes a single write intention.

    Attributes
    ----------
    actor : str
        The actor name (must match an :class:`Actor` value).
    write_level : str
        ``"level_1"`` or ``"level_2"``.
    target_object : str
        The target object name (must match a :class:`TargetObject` value).
    action : str
        What to do (``admit``, ``update``, ``add``, etc.).
    payload : dict
        The data to write.
    request_id : str, optional
        Auto-generated UUID if not provided.
    target_ref : str, optional
        Identifier of the specific instance being modified (e.g. factor id).
    evidence_refs : list of dict, optional
        For level-2 writes: list of evidence descriptors.
        Each should contain at minimum ``batch_id``, ``route_id``,
        and ``reason_code``.
    """

    actor: str
    write_level: str
    target_object: str
    action: str
    payload: Dict[str, Any]
    request_id: str = ""
    target_ref: str = ""
    evidence_refs: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.request_id:
            self.request_id = uuid.uuid4().hex[:12]


@dataclass
class WriteReceipt:
    """Result of a :meth:`GuardedWriter.write` call."""

    request_id: str
    status: str  # "accepted" | "rejected"
    written_paths: List[str] = field(default_factory=list)
    rejection_reason_codes: List[str] = field(default_factory=list)


# ------------------------------------------------------------------
# GuardedWriter
# ------------------------------------------------------------------


class GuardedWriter:
    """Programmatic writeback enforcement layer.

    Parameters
    ----------
    base_dir : Path
        Root storage directory used by the underlying writers.
    audit_log : WriteAuditLog, optional
        An existing audit log instance.  If *None* one is created
        automatically under *base_dir*.
    min_batches : int
        Minimum number of distinct batch ids required for level-2 evidence.
    min_routes : int
        Minimum number of distinct route ids required for level-2 evidence.
    """

    def __init__(
        self,
        base_dir: Path,
        audit_log: Optional[WriteAuditLog] = None,
        min_batches: int = 3,
        min_routes: int = 2,
    ) -> None:
        self._base_dir = Path(base_dir)
        self._audit = audit_log or WriteAuditLog(self._base_dir)
        self._min_batches = min_batches
        self._min_routes = min_routes

    @property
    def audit_log(self) -> WriteAuditLog:
        return self._audit

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def write(self, request: WriteRequest) -> WriteReceipt:
        """Validate *request*, execute if allowed, and return a receipt."""
        rejection_codes: List[str] = []

        # 1. Resolve actor enum
        try:
            actor_enum = Actor(request.actor)
        except ValueError:
            rejection_codes.append("unknown_actor")
            return self._reject(request, rejection_codes)

        # 2. Resolve target enum
        try:
            target_enum = TargetObject(request.target_object)
        except ValueError:
            rejection_codes.append("unknown_target")
            return self._reject(request, rejection_codes)

        # 3. Resolve write level
        try:
            level_enum = WriteLevel(request.write_level)
        except ValueError:
            rejection_codes.append("invalid_write_level")
            return self._reject(request, rejection_codes)

        # 4. Check actor is allowed to touch target+action
        if not actor_can_write(actor_enum, target_enum, request.action):
            rejection_codes.append("permission_denied")
            return self._reject(request, rejection_codes)

        # 5. Verify the declared level matches what the permission map requires
        req_level = required_level(actor_enum, target_enum)
        if req_level is not None and level_enum != req_level:
            rejection_codes.append("level_mismatch")
            return self._reject(request, rejection_codes)

        # 6. Level-2 evidence gate
        if level_enum == WriteLevel.level_2:
            evidence_issues = self._validate_evidence(request.evidence_refs)
            if evidence_issues:
                rejection_codes.extend(evidence_issues)
                return self._reject(request, rejection_codes)

        # 7. Execute the write
        written = self._execute_write(target_enum, request)

        # 8. Audit + receipt
        receipt = WriteReceipt(
            request_id=request.request_id,
            status="accepted",
            written_paths=written,
        )
        self._record_audit(request, "accepted")
        return receipt

    # ------------------------------------------------------------------
    # Level-2 evidence validation
    # ------------------------------------------------------------------

    def _validate_evidence(
        self, evidence_refs: List[Dict[str, Any]]
    ) -> List[str]:
        """Return a list of rejection reason codes (empty = OK)."""
        issues: List[str] = []
        if not evidence_refs:
            issues.append("no_evidence")
            return issues

        batch_ids = {e.get("batch_id") for e in evidence_refs if e.get("batch_id")}
        route_ids = {e.get("route_id") for e in evidence_refs if e.get("route_id")}
        reason_codes = {e.get("reason_code") for e in evidence_refs if e.get("reason_code")}

        if len(batch_ids) < self._min_batches:
            issues.append("insufficient_batches")
        if len(route_ids) < self._min_routes:
            issues.append("insufficient_routes")
        if len(reason_codes) > 1:
            issues.append("inconsistent_reason_codes")

        return issues

    # ------------------------------------------------------------------
    # Write execution (thin dispatcher)
    # ------------------------------------------------------------------

    def _execute_write(
        self, target: TargetObject, request: WriteRequest
    ) -> List[str]:
        """Execute the write and return a list of written file paths."""
        if target == TargetObject.factor_registry:
            return self._write_factor_registry(request)
        return self._write_generic(target, request)

    def _write_factor_registry(self, request: WriteRequest) -> List[str]:
        """Write to the factor registry via RegistryStore."""
        from research.storage.paths import StoragePaths
        from research.storage.registry_store import RegistryStore

        paths = StoragePaths(self._base_dir)
        store = RegistryStore(paths)
        payload = request.payload
        action = request.action
        factor_id = request.target_ref or payload.get("factor_id", "")

        written: List[str] = []

        if action == "admit":
            # Upsert into index
            index_entry = {
                "factor_id": factor_id,
                "name": payload.get("name", ""),
                "expression": payload.get("expression", ""),
                "status": "active",
                "admitted_batch": payload.get("batch_id", ""),
            }
            store.upsert_factor_entry(factor_id, index_entry)
            written.append(str(paths.factor_index_file))

            # Save detail file
            store.save_factor_detail(factor_id, payload)
            written.append(str(paths.factor_detail_file(factor_id)))

            # Persist to DB: factor_meta + factor_values
            self._persist_factor_to_db(factor_id, payload)

        elif action == "retire":
            index = store.load_factor_index()
            for f in index.get("factors", []):
                if f.get("factor_id") == factor_id:
                    f["status"] = "retired"
            store.save_factor_index(index)
            written.append(str(paths.factor_index_file))

        elif action == "replace":
            old_id = payload.get("replaced_factor_id")
            if old_id:
                # Retire old
                index = store.load_factor_index()
                for f in index.get("factors", []):
                    if f.get("factor_id") == old_id:
                        f["status"] = "retired"
                store.save_factor_index(index)
            # Admit new (reuse admit logic)
            request_copy = WriteRequest(
                actor=request.actor,
                write_level=request.write_level,
                target_object=request.target_object,
                action="admit",
                payload=payload,
                target_ref=factor_id,
            )
            written.extend(self._write_factor_registry(request_copy))

        elif action == "update":
            store.save_factor_detail(factor_id, payload)
            written.append(str(paths.factor_detail_file(factor_id)))

        return written

    def _write_generic(
        self, target: TargetObject, request: WriteRequest
    ) -> List[str]:
        """Default writer: dump the payload to a per-target YAML file."""
        target_dir = self._base_dir / "governance" / target.value
        target_dir.mkdir(parents=True, exist_ok=True)
        ref = request.target_ref or request.request_id
        out_path = target_dir / f"{ref}.yaml"
        atomic_yaml_write(out_path, request.payload)
        return [str(out_path)]

    # ------------------------------------------------------------------
    # DB persistence (best-effort, non-blocking)
    # ------------------------------------------------------------------

    @staticmethod
    def _persist_factor_to_db(factor_id: str, payload: Dict[str, Any]) -> None:
        """Write factor_meta + factor_values to TimescaleDB.

        Best-effort: logs warning on failure but does not raise.
        """
        from research.storage.factor_db import write_factor_meta, write_factor_values

        expression = payload.get("expression", "")
        name = payload.get("name", "")
        metrics = payload.get("metrics", {})
        # Also check top-level keys (judge may flatten metrics)
        if not metrics:
            metrics = {k: payload.get(k) for k in [
                "ic_mean_train", "ic_mean_validation", "ic_ir_validation",
                "ic_win_rate_validation", "monotonicity_validation",
                "max_lib_corr", "nearest_factor_id",
            ] if payload.get(k) is not None}

        try:
            write_factor_meta(
                factor_id=factor_id,
                name=name,
                expression=expression,
                metrics=metrics,
                batch_id=payload.get("batch_id", ""),
            )
        except Exception as exc:
            logger.warning("DB factor_meta write failed for %s: %s", factor_id, exc)

        if not expression:
            return

        try:
            from research.compute.data_provider import DataProvider, ensure_qlib_init
            from research.execute.config import load_research_config

            config = load_research_config()
            sp = config.get("sample_policy", {})
            start = sp.get("data_start", "2015-01-01")
            end = sp.get("active_validation_range", ["2022-01-01", "2023-12-31"])[1]

            ensure_qlib_init()
            provider = DataProvider(use_cache=True)
            factor_df = provider.get_factor_values(expression, start, end)
            write_factor_values(factor_id, factor_df)
        except Exception as exc:
            logger.warning("DB factor_values write failed for %s: %s", factor_id, exc)

    # ------------------------------------------------------------------
    # Audit helpers
    # ------------------------------------------------------------------

    def _reject(
        self, request: WriteRequest, codes: List[str]
    ) -> WriteReceipt:
        receipt = WriteReceipt(
            request_id=request.request_id,
            status="rejected",
            rejection_reason_codes=codes,
        )
        self._record_audit(request, "rejected", codes)
        return receipt

    def _record_audit(
        self,
        request: WriteRequest,
        status: str,
        rejection_codes: Optional[List[str]] = None,
    ) -> None:
        entry = WriteAuditLog.make_entry(
            request_id=request.request_id,
            actor=request.actor,
            level=request.write_level,
            target=request.target_object,
            action=request.action,
            status=status,
            rejection_reason_codes=rejection_codes,
        )
        self._audit.append(entry)

