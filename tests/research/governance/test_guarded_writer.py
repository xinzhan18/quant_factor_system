"""Tests for GuardedWriter: validate, execute, or reject write requests."""

import yaml
import pytest

from research.governance.guarded_writer import GuardedWriter, WriteRequest, WriteReceipt
from research.governance.audit import WriteAuditLog


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def base_dir(tmp_path):
    return tmp_path


@pytest.fixture
def writer(base_dir):
    return GuardedWriter(base_dir)


def _level1_request(**overrides) -> WriteRequest:
    defaults = dict(
        actor="judge",
        write_level="level_1",
        target_object="factor_registry",
        action="admit",
        payload={"factor_id": "F099", "name": "test_factor"},
    )
    defaults.update(overrides)
    return WriteRequest(**defaults)


def _level2_request(evidence_refs=None, **overrides) -> WriteRequest:
    defaults = dict(
        actor="judge",
        write_level="level_2",
        target_object="forbidden",
        action="add",
        payload={"pattern_id": "FP999", "summary": "test"},
        evidence_refs=evidence_refs or [],
    )
    defaults.update(overrides)
    return WriteRequest(**defaults)


def _make_evidence(n_batches=3, n_routes=2, reason="weak_signal"):
    """Build an evidence_refs list that satisfies level-2 defaults."""
    refs = []
    for i in range(max(n_batches, n_routes)):
        refs.append({
            "batch_id": f"batch_{i:03d}" if i < n_batches else f"batch_{n_batches - 1:03d}",
            "route_id": f"R{i:03d}" if i < n_routes else f"R{n_routes - 1:03d}",
            "reason_code": reason,
        })
    return refs


# ---------------------------------------------------------------------------
# Level 1 tests
# ---------------------------------------------------------------------------

class TestLevel1Write:
    def test_accepted_and_file_written(self, writer, base_dir):
        req = _level1_request()
        receipt = writer.write(req)
        assert receipt.status == "accepted"
        # admit writes index.yaml + factor detail file
        assert len(receipt.written_paths) == 2
        paths = receipt.written_paths
        assert any("index.yaml" in p for p in paths)
        detail_path = next(p for p in paths if "factor_F099.yaml" in p)
        data = yaml.safe_load(open(detail_path))
        assert data["factor_id"] == "F099"

    def test_audit_entry_created(self, writer, base_dir):
        req = _level1_request()
        receipt = writer.write(req)
        entries = writer.audit_log.read_all()
        assert len(entries) == 1
        assert entries[0]["request_id"] == receipt.request_id
        assert entries[0]["status"] == "accepted"

    def test_auto_request_id(self, writer):
        req = _level1_request()
        assert len(req.request_id) == 12  # hex uuid prefix

    def test_custom_request_id(self, writer):
        req = _level1_request(request_id="my-req-001")
        receipt = writer.write(req)
        assert receipt.request_id == "my-req-001"


# ---------------------------------------------------------------------------
# Level 2 tests
# ---------------------------------------------------------------------------

class TestLevel2Write:
    def test_accepted_with_sufficient_evidence(self, writer, base_dir):
        evidence = _make_evidence(n_batches=3, n_routes=2)
        req = _level2_request(evidence_refs=evidence)
        receipt = writer.write(req)
        assert receipt.status == "accepted"
        assert len(receipt.written_paths) == 1

    def test_rejected_no_evidence(self, writer):
        req = _level2_request(evidence_refs=[])
        receipt = writer.write(req)
        assert receipt.status == "rejected"
        assert "no_evidence" in receipt.rejection_reason_codes

    def test_rejected_insufficient_batches(self, writer):
        evidence = _make_evidence(n_batches=2, n_routes=2)
        req = _level2_request(evidence_refs=evidence)
        receipt = writer.write(req)
        assert receipt.status == "rejected"
        assert "insufficient_batches" in receipt.rejection_reason_codes

    def test_rejected_insufficient_routes(self, writer):
        evidence = _make_evidence(n_batches=3, n_routes=1)
        req = _level2_request(evidence_refs=evidence)
        receipt = writer.write(req)
        assert receipt.status == "rejected"
        assert "insufficient_routes" in receipt.rejection_reason_codes

    def test_rejected_inconsistent_reasons(self, writer):
        refs = [
            {"batch_id": "b1", "route_id": "r1", "reason_code": "weak_signal"},
            {"batch_id": "b2", "route_id": "r2", "reason_code": "high_overlap"},
            {"batch_id": "b3", "route_id": "r1", "reason_code": "weak_signal"},
        ]
        req = _level2_request(evidence_refs=refs)
        receipt = writer.write(req)
        assert receipt.status == "rejected"
        assert "inconsistent_reason_codes" in receipt.rejection_reason_codes

    def test_audit_for_rejected(self, writer):
        req = _level2_request(evidence_refs=[])
        writer.write(req)
        entries = writer.audit_log.read_all()
        assert entries[0]["status"] == "rejected"
        assert entries[0]["rejection_reason_codes"] is not None


# ---------------------------------------------------------------------------
# Permission enforcement tests
# ---------------------------------------------------------------------------

class TestPermissionEnforcement:
    def test_unknown_actor_rejected(self, writer):
        req = _level1_request(actor="rogue_agent")
        receipt = writer.write(req)
        assert receipt.status == "rejected"
        assert "unknown_actor" in receipt.rejection_reason_codes

    def test_unknown_target_rejected(self, writer):
        req = _level1_request(target_object="nonexistent_thing")
        receipt = writer.write(req)
        assert receipt.status == "rejected"
        assert "unknown_target" in receipt.rejection_reason_codes

    def test_invalid_level_rejected(self, writer):
        req = _level1_request(write_level="level_99")
        receipt = writer.write(req)
        assert receipt.status == "rejected"
        assert "invalid_write_level" in receipt.rejection_reason_codes

    def test_permission_denied_wrong_actor(self, writer):
        req = _level1_request(actor="execute")
        receipt = writer.write(req)
        assert receipt.status == "rejected"
        assert "permission_denied" in receipt.rejection_reason_codes

    def test_level_mismatch_rejected(self, writer):
        # forbidden requires level_2, but request says level_1
        req = WriteRequest(
            actor="judge",
            write_level="level_1",
            target_object="forbidden",
            action="add",
            payload={"x": 1},
        )
        receipt = writer.write(req)
        assert receipt.status == "rejected"
        assert "level_mismatch" in receipt.rejection_reason_codes

    def test_disallowed_action_rejected(self, writer):
        req = _level1_request(action="destroy")
        receipt = writer.write(req)
        assert receipt.status == "rejected"
        assert "permission_denied" in receipt.rejection_reason_codes


# ---------------------------------------------------------------------------
# Custom thresholds
# ---------------------------------------------------------------------------

class TestCustomThresholds:
    def test_custom_min_batches(self, base_dir):
        gw = GuardedWriter(base_dir, min_batches=1, min_routes=1)
        evidence = [
            {"batch_id": "b1", "route_id": "r1", "reason_code": "x"},
        ]
        req = _level2_request(evidence_refs=evidence)
        receipt = gw.write(req)
        assert receipt.status == "accepted"


# ---------------------------------------------------------------------------
# Multiple writes accumulate audit entries
# ---------------------------------------------------------------------------

class TestAuditAccumulation:
    def test_multiple_writes(self, writer):
        for i in range(3):
            req = _level1_request(
                request_id=f"req-{i}",
                payload={"factor_id": f"F{i:03d}"},
                target_ref=f"F{i:03d}",
            )
            writer.write(req)
        entries = writer.audit_log.read_all()
        assert len(entries) == 3
