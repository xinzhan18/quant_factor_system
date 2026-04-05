"""Tests for HoldoutQueue -- pending holdout review management."""
import os
import tempfile
from datetime import datetime, timedelta

from research.controller.holdout_queue import (
    HoldoutEntry,
    HoldoutQueue,
    DEFAULT_DEADLINE_DAYS,
)


class TestHoldoutQueueEnqueue:
    def test_enqueue_basic(self):
        q = HoldoutQueue()
        entry = q.enqueue(
            candidate_id="C001",
            logic_id="L021",
            family_id="FM_breakout",
            batch_id="batch_042",
        )
        assert entry.candidate_id == "C001"
        assert entry.status == "pending"
        assert len(q.entries) == 1

    def test_enqueue_sets_deadline(self):
        q = HoldoutQueue()
        now = datetime(2026, 4, 5, 12, 0, 0)
        entry = q.enqueue(
            candidate_id="C001",
            logic_id="L021",
            family_id="FM_breakout",
            batch_id="batch_042",
            now=now,
        )
        expected_deadline = (now + timedelta(days=DEFAULT_DEADLINE_DAYS)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        assert entry.deadline == expected_deadline


class TestHoldoutQueueSupersede:
    def test_supersede_same_logic_family(self):
        q = HoldoutQueue()
        now = datetime(2026, 4, 5, 12, 0, 0)
        q.enqueue("C001", "L021", "FM_breakout", "batch_042", now=now)
        q.enqueue("C002", "L021", "FM_breakout", "batch_043", now=now)
        entries = q.entries
        assert entries[0].status == "superseded"
        assert entries[1].status == "pending"
        assert entries[1].candidate_id == "C002"

    def test_no_supersede_different_family(self):
        q = HoldoutQueue()
        now = datetime(2026, 4, 5, 12, 0, 0)
        q.enqueue("C001", "L021", "FM_breakout", "batch_042", now=now)
        q.enqueue("C002", "L021", "FM_reversal", "batch_043", now=now)
        pending = q.pending()
        assert len(pending) == 2

    def test_no_supersede_different_logic(self):
        q = HoldoutQueue()
        now = datetime(2026, 4, 5, 12, 0, 0)
        q.enqueue("C001", "L021", "FM_breakout", "batch_042", now=now)
        q.enqueue("C002", "L008", "FM_breakout", "batch_043", now=now)
        pending = q.pending()
        assert len(pending) == 2


class TestHoldoutQueueExpiry:
    def test_expire_past_deadline(self):
        q = HoldoutQueue()
        now = datetime(2026, 4, 5, 12, 0, 0)
        q.enqueue("C001", "L021", "FM_breakout", "batch_042", now=now)
        # Advance past deadline
        future = now + timedelta(days=DEFAULT_DEADLINE_DAYS + 1)
        expired = q.expire_past_deadline(now=future)
        assert expired == 1
        assert q.entries[0].status == "expired"

    def test_not_expired_before_deadline(self):
        q = HoldoutQueue()
        now = datetime(2026, 4, 5, 12, 0, 0)
        q.enqueue("C001", "L021", "FM_breakout", "batch_042", now=now)
        # Still within deadline
        still_ok = now + timedelta(days=DEFAULT_DEADLINE_DAYS - 1)
        expired = q.expire_past_deadline(now=still_ok)
        assert expired == 0
        assert q.entries[0].status == "pending"

    def test_already_superseded_not_expired(self):
        q = HoldoutQueue()
        now = datetime(2026, 4, 5, 12, 0, 0)
        q.enqueue("C001", "L021", "FM_breakout", "batch_042", now=now)
        q.enqueue("C002", "L021", "FM_breakout", "batch_043", now=now)
        # Advance past deadline
        future = now + timedelta(days=DEFAULT_DEADLINE_DAYS + 1)
        expired = q.expire_past_deadline(now=future)
        # Only the pending one (C002) should expire, C001 is already superseded
        assert expired == 1
        assert q.entries[0].status == "superseded"  # C001 stays superseded
        assert q.entries[1].status == "expired"  # C002 expired


class TestHoldoutQueueMarkReviewed:
    def test_mark_reviewed(self):
        q = HoldoutQueue()
        q.enqueue("C001", "L021", "FM_breakout", "batch_042")
        assert q.mark_reviewed("C001")
        assert q.entries[0].status == "reviewed"

    def test_mark_reviewed_not_found(self):
        q = HoldoutQueue()
        assert not q.mark_reviewed("C999")


class TestHoldoutQueueSerialization:
    def test_round_trip_dict(self):
        q = HoldoutQueue()
        now = datetime(2026, 4, 5, 12, 0, 0)
        q.enqueue("C001", "L021", "FM_breakout", "batch_042", now=now)
        data = q.to_dict_list()
        q2 = HoldoutQueue.from_dict_list(data)
        assert len(q2.entries) == 1
        assert q2.entries[0].candidate_id == "C001"

    def test_yaml_round_trip(self):
        q = HoldoutQueue()
        now = datetime(2026, 4, 5, 12, 0, 0)
        q.enqueue("C001", "L021", "FM_breakout", "batch_042", now=now)
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "holdout_queue.yaml")
            q.save_yaml(path)
            q2 = HoldoutQueue.load_yaml(path)
            assert len(q2.entries) == 1
            assert q2.entries[0].candidate_id == "C001"

    def test_load_missing_file(self):
        q = HoldoutQueue.load_yaml("/nonexistent/path.yaml")
        assert len(q.entries) == 0
