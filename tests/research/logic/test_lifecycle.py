"""Tests for research.logic.lifecycle — state transitions, family promotion, arbitration."""
import warnings

import pytest

from research.logic.cards import LogicCard, LogicCardStore, ExplorationContract
from research.logic.lifecycle import (
    ALLOWED_TRANSITIONS,
    LifecycleManager,
    ArbitrationRecord,
    validate_transition,
    build_transition_record,
    validate_promotion,
    build_promotion_record,
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
    """Tests for LifecycleManager.transition() (deprecated, backward-compat)."""

    def test_valid_transition(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store, status="active")
        mgr = LifecycleManager(store, tmp_path)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            result = mgr.transition(card.logic_id, "warm", reason="cooling down")
        assert result.status == "warm"

        # Verify persisted
        reloaded = store.get(card.logic_id)
        assert reloaded.status == "warm"

    def test_invalid_transition_raises(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store, status="dead")
        mgr = LifecycleManager(store, tmp_path)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            with pytest.raises(ValueError, match="Cannot transition"):
                mgr.transition(card.logic_id, "active")

    def test_invalid_target_status_raises(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store, status="active")
        mgr = LifecycleManager(store, tmp_path)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            with pytest.raises(ValueError, match="Invalid target status"):
                mgr.transition(card.logic_id, "invented_status")

    def test_nonexistent_card_raises(self, tmp_path):
        store = _make_store(tmp_path)
        mgr = LifecycleManager(store, tmp_path)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            with pytest.raises(KeyError, match="not found"):
                mgr.transition("L999", "active")

    def test_transition_records_history(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store, status="active")
        mgr = LifecycleManager(store, tmp_path)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            mgr.transition(card.logic_id, "productive", reason="good results")
        reloaded = store.get(card.logic_id)
        transitions = reloaded.evidence_summary.get("transitions", [])
        assert len(transitions) == 1
        assert transitions[0]["from"] == "active"
        assert transitions[0]["to"] == "productive"
        assert transitions[0]["reason"] == "good results"

    def test_transition_emits_deprecation_warning(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store, status="active")
        mgr = LifecycleManager(store, tmp_path)

        with pytest.warns(DeprecationWarning, match="transition.*deprecated"):
            mgr.transition(card.logic_id, "warm")

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

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            card = mgr.transition(card.logic_id, "active")
            assert card.status == "active"

            card = mgr.transition(card.logic_id, "productive")
            assert card.status == "productive"

            card = mgr.transition(card.logic_id, "saturated")
            assert card.status == "saturated"

            card = mgr.transition(card.logic_id, "dead")
            assert card.status == "dead"


class TestFamilyPromotion:
    """Tests for LifecycleManager.promote_family() (deprecated, backward-compat)."""

    def test_promote_success(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store)
        mgr = LifecycleManager(store, tmp_path)

        batch_evidence = [
            {"batch_id": "batch_001", "admitted": 2},
            {"batch_id": "batch_002", "admitted": 1},
        ]
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
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

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
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

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            success, reason = mgr.promote_family(
                card.logic_id,
                "FM_x",
                batch_evidence=[{"a": 1}, {"b": 2}],
                subspace_redundancy=0.9,
            )
        assert success is False
        assert "redundancy" in reason.lower()

    def test_promote_emits_deprecation_warning(self, tmp_path):
        store = _make_store(tmp_path)
        card = _create_test_card(store)
        mgr = LifecycleManager(store, tmp_path)

        with pytest.warns(DeprecationWarning, match="promote_family.*deprecated"):
            mgr.promote_family(
                card.logic_id,
                "FM_x",
                batch_evidence=[{"a": 1}, {"b": 2}],
            )


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


# ------------------------------------------------------------------
# Pure function tests (no I/O, no LifecycleManager needed)
# ------------------------------------------------------------------


class TestValidateTransition:
    """Tests for the pure validate_transition() function."""

    def test_valid_transition_returns_to_status(self):
        result = validate_transition("active", "warm")
        assert result == "warm"

    def test_invalid_target_status_raises(self):
        with pytest.raises(ValueError, match="Invalid target status"):
            validate_transition("active", "invented_status")

    def test_disallowed_transition_raises(self):
        with pytest.raises(ValueError, match="Cannot transition"):
            validate_transition("dead", "active")

    def test_all_allowed_transitions_pass(self):
        for from_status, allowed in ALLOWED_TRANSITIONS.items():
            for to_status in allowed:
                assert validate_transition(from_status, to_status) == to_status

    def test_unknown_current_status_rejects(self):
        """An unrecognized current_status has no allowed transitions."""
        with pytest.raises(ValueError, match="Cannot transition"):
            validate_transition("nonexistent", "active")


class TestBuildTransitionRecord:
    """Tests for the pure build_transition_record() function."""

    def test_returns_expected_keys(self):
        rec = build_transition_record("active", "warm", "cooling down")
        assert rec["from"] == "active"
        assert rec["to"] == "warm"
        assert rec["reason"] == "cooling down"
        assert "at" in rec

    def test_empty_reason(self):
        rec = build_transition_record("proposed", "active", "")
        assert rec["reason"] == ""

    def test_timestamp_is_string(self):
        rec = build_transition_record("active", "warm", "test")
        assert isinstance(rec["at"], str)
        assert len(rec["at"]) > 0


class TestValidatePromotion:
    """Tests for the pure validate_promotion() function."""

    def test_valid_promotion(self):
        ok, reason = validate_promotion(
            [{"batch_id": "b1"}, {"batch_id": "b2"}], 0.3
        )
        assert ok is True
        assert reason == "ok"

    def test_insufficient_batches(self):
        ok, reason = validate_promotion([{"batch_id": "b1"}], 0.3)
        assert ok is False
        assert "2 batches" in reason

    def test_empty_batches(self):
        ok, reason = validate_promotion([], 0.0)
        assert ok is False

    def test_high_redundancy(self):
        ok, reason = validate_promotion(
            [{"a": 1}, {"b": 2}], 0.9
        )
        assert ok is False
        assert "redundancy" in reason.lower()

    def test_boundary_redundancy_exactly_at_max(self):
        """Redundancy == MAX is allowed (only > is rejected)."""
        ok, reason = validate_promotion(
            [{"a": 1}, {"b": 2}], 0.7
        )
        assert ok is True

    def test_boundary_redundancy_just_above_max(self):
        ok, reason = validate_promotion(
            [{"a": 1}, {"b": 2}], 0.70001
        )
        assert ok is False


class TestBuildPromotionRecord:
    """Tests for the pure build_promotion_record() function."""

    def test_returns_expected_keys(self):
        evidence = [{"batch_id": "b1"}, {"batch_id": "b2"}]
        rec = build_promotion_record("FM_breakout", evidence, 0.3)
        assert rec["family_id"] == "FM_breakout"
        assert rec["batch_count"] == 2
        assert rec["subspace_redundancy"] == 0.3
        assert "promoted_at" in rec

    def test_timestamp_is_string(self):
        rec = build_promotion_record("FM_x", [{"a": 1}], 0.0)
        assert isinstance(rec["promoted_at"], str)
        assert len(rec["promoted_at"]) > 0
