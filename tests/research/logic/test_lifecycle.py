"""Tests for research.logic.lifecycle — state transitions, family promotion, arbitration."""
import pytest

from research.logic.cards import LogicCard, LogicCardStore, ExplorationContract
from research.logic.lifecycle import (
    ALLOWED_TRANSITIONS,
    LifecycleManager,
    ArbitrationRecord,
)


def _make_store(tmp_path) -> LogicCardStore:
    return LogicCardStore(tmp_path)


def _create_test_card(store: LogicCardStore, **overrides) -> LogicCard:
    defaults = dict(
        name="test logic",
        category="volume_price",
        status="active",
        priority="high",
        hypothesis="test hypothesis",
    )
    defaults.update(overrides)
    return store.create(**defaults)


class TestStateTransitions:
    def test_valid_transition(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store, status="active")
        mgr = LifecycleManager(store, tmp_path)

        result = mgr.transition(card.logic_id, "warm", reason="cooling down")
        assert result.status == "warm"

        # Verify persisted
        reloaded = store.get(card.logic_id)
        assert reloaded.status == "warm"

    def test_invalid_transition_raises(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store, status="dead")
        mgr = LifecycleManager(store, tmp_path)

        with pytest.raises(ValueError, match="Cannot transition"):
            mgr.transition(card.logic_id, "active")

    def test_invalid_target_status_raises(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store, status="active")
        mgr = LifecycleManager(store, tmp_path)

        with pytest.raises(ValueError, match="Invalid target status"):
            mgr.transition(card.logic_id, "invented_status")

    def test_nonexistent_card_raises(self, tmp_path):
        store = _make_store(tmp_path)
        mgr = LifecycleManager(store, tmp_path)

        with pytest.raises(KeyError, match="not found"):
            mgr.transition("L999", "active")

    def test_transition_records_history(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store, status="active")
        mgr = LifecycleManager(store, tmp_path)

        mgr.transition(card.logic_id, "productive", reason="good results")
        reloaded = store.get(card.logic_id)
        transitions = reloaded.evidence_summary.get("transitions", [])
        assert len(transitions) == 1
        assert transitions[0]["from"] == "active"
        assert transitions[0]["to"] == "productive"
        assert transitions[0]["reason"] == "good results"

    def test_get_allowed_transitions(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store, status="proposed")
        mgr = LifecycleManager(store, tmp_path)

        allowed = mgr.get_allowed_transitions(card.logic_id)
        assert set(allowed) == {"active", "warm", "parked", "dead"}

    def test_all_transitions_defined(self):
        """Every status has a transitions entry."""
        from research.logic.cards import VALID_STATUSES

        for status in VALID_STATUSES:
            assert status in ALLOWED_TRANSITIONS

    def test_proposed_to_active_chain(self, tmp_path):
        """Test a typical lifecycle chain: proposed -> active -> productive -> saturated -> dead."""
        store = _make_store(tmp_path)
        card = _create_test_card(store, status="proposed")
        mgr = LifecycleManager(store, tmp_path)

        card = mgr.transition(card.logic_id, "active")
        assert card.status == "active"

        card = mgr.transition(card.logic_id, "productive")
        assert card.status == "productive"

        card = mgr.transition(card.logic_id, "saturated")
        assert card.status == "saturated"

        card = mgr.transition(card.logic_id, "dead")
        assert card.status == "dead"


class TestFamilyPromotion:
    def test_promote_success(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store)
        mgr = LifecycleManager(store, tmp_path)

        batch_evidence = [
            {"batch_id": "batch_001", "admitted": 2},
            {"batch_id": "batch_002", "admitted": 1},
        ]
        success, reason = mgr.promote_family(
            card.logic_id,
            "FM_breakout",
            batch_evidence=batch_evidence,
            subspace_redundancy=0.3,
        )
        assert success is True

        # Check persisted
        reloaded = store.get(card.logic_id)
        promoted = reloaded.evidence_summary.get("promoted_families", [])
        assert len(promoted) == 1
        assert promoted[0]["family_id"] == "FM_breakout"

    def test_promote_insufficient_batches(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store)
        mgr = LifecycleManager(store, tmp_path)

        success, reason = mgr.promote_family(
            card.logic_id,
            "FM_x",
            batch_evidence=[{"batch_id": "b1"}],
        )
        assert success is False
        assert "2 batches" in reason

    def test_promote_high_redundancy(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store)
        mgr = LifecycleManager(store, tmp_path)

        success, reason = mgr.promote_family(
            card.logic_id,
            "FM_x",
            batch_evidence=[{"a": 1}, {"b": 2}],
            subspace_redundancy=0.9,
        )
        assert success is False
        assert "redundancy" in reason.lower()


class TestArbitration:
    def test_record_aligned(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store)
        mgr = LifecycleManager(store, tmp_path)

        rec = mgr.record_arbitration(
            logic_id=card.logic_id,
            factor_id="F042",
            judge_recommendation="admit",
            logic_decision="admit",
        )
        assert rec.is_override is False

    def test_record_override(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store)
        mgr = LifecycleManager(store, tmp_path)

        rec = mgr.record_arbitration(
            logic_id=card.logic_id,
            factor_id="F042",
            judge_recommendation="admit",
            logic_decision="override_reject",
            reason="corr too high with existing",
        )
        assert rec.is_override is True

    def test_list_arbitrations(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store)
        mgr = LifecycleManager(store, tmp_path)

        mgr.record_arbitration(
            logic_id=card.logic_id,
            factor_id="F001",
            judge_recommendation="admit",
            logic_decision="admit",
        )
        mgr.record_arbitration(
            logic_id=card.logic_id,
            factor_id="F002",
            judge_recommendation="reject",
            logic_decision="override_admit",
            reason="exploratory value",
        )

        records = mgr.list_arbitrations(card.logic_id)
        assert len(records) == 2
        assert records[0].factor_id == "F001"
        assert records[1].is_override is True

    def test_list_empty(self, tmp_path):
        store = _make_store(tmp_path)
        mgr = LifecycleManager(store, tmp_path)
        assert mgr.list_arbitrations("L999") == []

    def test_arbitration_record_roundtrip(self):
        rec = ArbitrationRecord(
            logic_id="L001",
            factor_id="F042",
            judge_recommendation="admit",
            logic_decision="override_reject",
            reason="test",
        )
        d = rec.to_dict()
        rec2 = ArbitrationRecord.from_dict(d)
        assert rec2.logic_id == rec.logic_id
        assert rec2.is_override == rec.is_override
