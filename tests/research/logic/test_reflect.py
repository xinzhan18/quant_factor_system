"""Tests for research.logic.reflect — cognitive state updater."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict
from unittest.mock import patch

import pytest
import yaml

from research.logic.reflect import (
    LogicBeliefDelta,
    GlobalEscalationDelta,
    apply_belief_delta,
    save_global_escalation,
    load_global_escalation,
    transition_escalation,
    consume_pending_escalations,
    resolve_escalation,
    recompute_research_state,
    write_reflection_md,
)
from research.storage.yaml_io import load_yaml, save_yaml


# -----------------------------------------------------------------------
# Fixtures / helpers
# -----------------------------------------------------------------------


def _minimal_card(
    logic_id: str = "L001",
    status: str = "active",
    priority: str = "high",
    **overrides: Any,
) -> Dict[str, Any]:
    """Return the smallest valid card dict for testing."""
    card: Dict[str, Any] = {
        "logic_id": logic_id,
        "name": "test logic",
        "category": "volume_price",
        "status": status,
        "priority": priority,
        "hypothesis": "test",
        "contract": {
            "current_focus_question": "What drives reversal?",
            "preferred_families": ["FM_vol"],
            "suggested_ops": ["Std"],
            "avoid_patterns": [],
        },
        "evidence_summary": {
            "factors_generated": 10,
            "factors_admitted": 3,
            "rounds_without_admit": 1,
        },
        "deepening_threads": [],
        "next_actions": [],
        "last_reflected_batch": "batch_001",
        "created_at": "2026-01-01 00:00:00",
        "updated_at": "2026-01-01 00:00:00",
    }
    card.update(overrides)
    return card


def _write_card(tmp_path: Path, card: dict) -> Path:
    """Write a card dict to a YAML file and return the path."""
    cards_dir = tmp_path / "logic" / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    card_path = cards_dir / f"{card['logic_id']}.yaml"
    save_yaml(card_path, card)
    return card_path


def _write_registry(tmp_path: Path, logics: list | None = None) -> Path:
    """Write a minimal registry.yaml and return the path."""
    registry_path = tmp_path / "logic" / "registry.yaml"
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    data = {"logics": logics or [], "count": len(logics or [])}
    save_yaml(registry_path, data)
    return registry_path


def _make_delta(**overrides: Any) -> LogicBeliefDelta:
    """Create a LogicBeliefDelta with sensible defaults."""
    defaults: Dict[str, Any] = {
        "logic_id": "L001",
        "batch_id": "batch_002",
    }
    defaults.update(overrides)
    return LogicBeliefDelta(**defaults)


# -----------------------------------------------------------------------
# TestLogicBeliefDelta
# -----------------------------------------------------------------------


class TestLogicBeliefDelta:
    """Verify dataclass defaults and required fields."""

    def test_required_fields(self):
        delta = LogicBeliefDelta(logic_id="L001", batch_id="batch_001")
        assert delta.logic_id == "L001"
        assert delta.batch_id == "batch_001"

    def test_defaults(self):
        delta = LogicBeliefDelta(logic_id="L001", batch_id="batch_001")
        assert delta.status_change is None
        assert delta.status_reason == ""
        assert delta.focus_question_update is None
        assert delta.families_to_add == []
        assert delta.families_to_remove == []
        assert delta.ops_to_add == []
        assert delta.avoid_patterns_to_add == []
        assert delta.new_productive == []
        assert delta.new_failed == []
        assert delta.new_exhausted == []
        assert delta.bottleneck_update is None
        assert delta.generated_this_batch == 0
        assert delta.admits_this_batch == 0
        assert delta.threads_to_add == []
        assert delta.threads_to_update == []
        assert delta.threads_to_park == []
        assert delta.next_actions == []

    def test_mutable_defaults_are_independent(self):
        d1 = LogicBeliefDelta(logic_id="L001", batch_id="b1")
        d2 = LogicBeliefDelta(logic_id="L002", batch_id="b2")
        d1.families_to_add.append("FM_x")
        assert d2.families_to_add == []


# -----------------------------------------------------------------------
# TestApplyBeliefDelta
# -----------------------------------------------------------------------


class TestApplyBeliefDelta:
    """The critical tests for the single-write card updater."""

    def test_status_change(self, tmp_path):
        card = _minimal_card(status="active")
        card_path = _write_card(tmp_path, card)
        registry_path = _write_registry(tmp_path, [
            {"logic_id": "L001", "name": "test logic", "category": "volume_price",
             "status": "active", "priority": "high"},
        ])

        delta = _make_delta(status_change="warm", status_reason="cooling down")
        result = apply_belief_delta(card_path, delta, registry_path)

        assert result["status"] == "warm"
        transitions = result["evidence_summary"]["transitions"]
        assert len(transitions) == 1
        assert transitions[0]["from"] == "active"
        assert transitions[0]["to"] == "warm"
        assert transitions[0]["reason"] == "cooling down"

        # Verify persisted
        reloaded = load_yaml(card_path)
        assert reloaded["status"] == "warm"

    def test_status_change_illegal_raises(self, tmp_path):
        card = _minimal_card(status="dead")
        card_path = _write_card(tmp_path, card)
        registry_path = _write_registry(tmp_path)

        delta = _make_delta(status_change="active")

        with pytest.raises(ValueError, match="Cannot transition"):
            apply_belief_delta(card_path, delta, registry_path)

        # Card unchanged
        reloaded = load_yaml(card_path)
        assert reloaded["status"] == "dead"

    def test_contract_evolution(self, tmp_path):
        card = _minimal_card()
        card_path = _write_card(tmp_path, card)
        registry_path = _write_registry(tmp_path)

        delta = _make_delta(
            focus_question_update="What drives momentum decay?",
            families_to_add=["FM_momentum", "FM_reversal"],
            families_to_remove=["FM_vol"],
            ops_to_add=["TsRank", "CsZscore"],
            avoid_patterns_to_add=["$vwap", "Neg("],
        )
        result = apply_belief_delta(card_path, delta, registry_path)

        contract = result["contract"]
        assert contract["current_focus_question"] == "What drives momentum decay?"
        assert "FM_momentum" in contract["preferred_families"]
        assert "FM_reversal" in contract["preferred_families"]
        assert "FM_vol" not in contract["preferred_families"]
        assert "TsRank" in contract["suggested_ops"]
        assert "CsZscore" in contract["suggested_ops"]
        assert "Std" in contract["suggested_ops"]  # original preserved
        assert "$vwap" in contract["avoid_patterns"]
        assert "Neg(" in contract["avoid_patterns"]

    def test_memory_counters(self, tmp_path):
        card = _minimal_card()
        card["evidence_summary"]["factors_generated"] = 10
        card["evidence_summary"]["factors_admitted"] = 3
        card["evidence_summary"]["rounds_without_admit"] = 2
        card_path = _write_card(tmp_path, card)
        registry_path = _write_registry(tmp_path)

        delta = _make_delta(generated_this_batch=6, admits_this_batch=2)
        result = apply_belief_delta(card_path, delta, registry_path)

        ev = result["evidence_summary"]
        assert ev["factors_generated"] == 16  # 10 + 6
        assert ev["factors_admitted"] == 5  # 3 + 2
        assert ev["rounds_without_admit"] == 0  # reset because admits > 0

    def test_memory_counters_no_admits(self, tmp_path):
        card = _minimal_card()
        card["evidence_summary"]["factors_generated"] = 10
        card["evidence_summary"]["factors_admitted"] = 3
        card["evidence_summary"]["rounds_without_admit"] = 2
        card_path = _write_card(tmp_path, card)
        registry_path = _write_registry(tmp_path)

        delta = _make_delta(generated_this_batch=4, admits_this_batch=0)
        result = apply_belief_delta(card_path, delta, registry_path)

        ev = result["evidence_summary"]
        assert ev["factors_generated"] == 14  # 10 + 4
        assert ev["factors_admitted"] == 3  # unchanged
        assert ev["rounds_without_admit"] == 3  # 2 + 1

    def test_thread_mutations(self, tmp_path):
        card = _minimal_card()
        card["deepening_threads"] = [
            {"id": "T1", "topic": "volume spikes", "status": "active"},
            {"id": "T2", "topic": "reversal decay", "status": "active"},
        ]
        card_path = _write_card(tmp_path, card)
        registry_path = _write_registry(tmp_path)

        delta = _make_delta(
            threads_to_add=[
                {"id": "T3", "topic": "new direction", "status": "active"},
            ],
            threads_to_update=[
                {"id": "T1", "notes": "confirmed signal", "status": "productive"},
            ],
            threads_to_park=["T2"],
        )
        result = apply_belief_delta(card_path, delta, registry_path)

        threads = result["deepening_threads"]
        assert len(threads) == 3

        t1 = next(t for t in threads if t["id"] == "T1")
        assert t1["status"] == "productive"
        assert t1["notes"] == "confirmed signal"
        assert t1["topic"] == "volume spikes"  # preserved

        t2 = next(t for t in threads if t["id"] == "T2")
        assert t2["status"] == "parked"

        t3 = next(t for t in threads if t["id"] == "T3")
        assert t3["topic"] == "new direction"
        assert t3["status"] == "active"

    def test_single_write(self, tmp_path):
        """Verify card_path is written exactly once."""
        card = _minimal_card()
        card_path = _write_card(tmp_path, card)
        registry_path = _write_registry(tmp_path)

        delta = _make_delta(
            generated_this_batch=3,
            admits_this_batch=1,
            focus_question_update="new question",
        )

        with patch("research.logic.reflect.save_yaml") as mock_save:
            # We need to actually return nothing, just track calls
            apply_belief_delta(card_path, delta, registry_path)
            # save_yaml called exactly once for the card
            assert mock_save.call_count == 1
            assert mock_save.call_args[0][0] == card_path

    def test_registry_sync(self, tmp_path):
        card = _minimal_card(status="active")
        card_path = _write_card(tmp_path, card)
        registry_path = _write_registry(tmp_path, [
            {"logic_id": "L001", "name": "test logic", "category": "volume_price",
             "status": "active", "priority": "high"},
        ])

        delta = _make_delta(status_change="warm", status_reason="cooling")
        apply_belief_delta(card_path, delta, registry_path)

        registry = load_yaml(registry_path)
        entry = registry["logics"][0]
        assert entry["status"] == "warm"

    def test_no_registry_sync_without_change(self, tmp_path):
        card = _minimal_card(status="active")
        card_path = _write_card(tmp_path, card)
        registry_path = _write_registry(tmp_path, [
            {"logic_id": "L001", "name": "test logic", "category": "volume_price",
             "status": "active", "priority": "high"},
        ])

        delta = _make_delta(generated_this_batch=2, admits_this_batch=0)

        with patch("research.logic.reflect._sync_registry_entry") as mock_sync:
            apply_belief_delta(card_path, delta, registry_path)
            mock_sync.assert_not_called()

    def test_next_actions_and_batch(self, tmp_path):
        card = _minimal_card()
        card["next_actions"] = ["old action"]
        card_path = _write_card(tmp_path, card)
        registry_path = _write_registry(tmp_path)

        delta = _make_delta(
            batch_id="batch_005",
            next_actions=["action A", "action B"],
        )
        result = apply_belief_delta(card_path, delta, registry_path)

        assert result["next_actions"] == ["action A", "action B"]
        assert result["last_reflected_batch"] == "batch_005"

    def test_missing_card_file_raises(self, tmp_path):
        card_path = tmp_path / "logic" / "cards" / "L999.yaml"
        registry_path = _write_registry(tmp_path)
        delta = _make_delta(logic_id="L999")

        with pytest.raises(FileNotFoundError, match="not found"):
            apply_belief_delta(card_path, delta, registry_path)

    def test_productive_memory_merge(self, tmp_path):
        card = _minimal_card()
        card["evidence_summary"]["productive_families"] = [
            {"family_id": "FM_vol", "count": 2, "best_ic": 0.04},
        ]
        card_path = _write_card(tmp_path, card)
        registry_path = _write_registry(tmp_path)

        delta = _make_delta(
            new_productive=[
                {"family_id": "FM_vol", "count": 3, "best_ic": 0.05},
                {"family_id": "FM_reversal", "count": 1, "best_ic": 0.03},
            ],
        )
        result = apply_belief_delta(card_path, delta, registry_path)

        productive = result["evidence_summary"]["productive_families"]
        assert len(productive) == 2
        fm_vol = next(p for p in productive if p["family_id"] == "FM_vol")
        assert fm_vol["count"] == 3  # updated, not appended
        assert fm_vol["best_ic"] == 0.05

    def test_bottleneck_update(self, tmp_path):
        card = _minimal_card()
        card_path = _write_card(tmp_path, card)
        registry_path = _write_registry(tmp_path)

        delta = _make_delta(bottleneck_update="correlation ceiling at 0.7")
        result = apply_belief_delta(card_path, delta, registry_path)

        assert result["evidence_summary"]["current_bottleneck"] == "correlation ceiling at 0.7"

    def test_idempotent_family_add(self, tmp_path):
        """Adding the same family twice does not duplicate."""
        card = _minimal_card()
        card["contract"]["preferred_families"] = ["FM_vol"]
        card_path = _write_card(tmp_path, card)
        registry_path = _write_registry(tmp_path)

        delta = _make_delta(families_to_add=["FM_vol", "FM_new"])
        result = apply_belief_delta(card_path, delta, registry_path)

        families = result["contract"]["preferred_families"]
        assert families.count("FM_vol") == 1
        assert "FM_new" in families

    def test_round_trip_real_card_schema(self, tmp_path):
        """Verify that apply_belief_delta produces field names matching the
        actual card YAML schema (L001/L002/L003), not a parallel set."""
        card: Dict[str, Any] = {
            "logic_id": "L001",
            "name": "volume_price_divergence",
            "category": "volume_price",
            "created_at": "2026-04-05",
            "status": "active",
            "priority": "high",
            "hypothesis": {"condition": "test", "behavior": "test", "timeframe": "5-20d"},
            "contract": {
                "current_focus_question": "original question",
                "preferred_families": ["pv_correlation"],
                "suggested_ops": ["Corr"],
                "avoid_patterns": [],
            },
            "evidence_summary": {
                "factors_generated": 5,
                "factors_admitted": 1,
                "rounds_without_admit": 0,
                "productive_families": [
                    {"family_id": "PF_pv_correlation", "factors": ["R001"]},
                ],
                "failed_families": [],
                "exhausted_routes": [],
                "current_bottleneck": "original bottleneck",
                "transitions": [],
                "promoted_families": [],
            },
            "deepening_threads": [
                {"id": "T001", "question": "Why does X work?", "status": "active", "priority": "high"},
            ],
            "next_actions": ["probe Y"],
            "last_reflected_batch": "batch_003",
        }
        card_path = _write_card(tmp_path, card)
        registry_path = _write_registry(tmp_path)

        delta = _make_delta(
            generated_this_batch=4,
            admits_this_batch=1,
            bottleneck_update="new bottleneck text",
            new_productive=[{"family_id": "PF_new", "factors": ["R010"]}],
            new_failed=[{"family_id": "PF_bad", "reason": "IC too low"}],
            new_exhausted=[{"tag": "ELT_test", "verdict": "kill", "reason": "dead"}],
            threads_to_update=[{"id": "T001", "status": "answered"}],
            threads_to_add=[{"id": "T002", "question": "new question", "status": "active"}],
        )
        apply_belief_delta(card_path, delta, registry_path)

        reloaded = load_yaml(card_path)
        ev = reloaded["evidence_summary"]

        # Correct field names present
        assert "productive_families" in ev
        assert "failed_families" in ev
        assert "exhausted_routes" in ev
        assert "current_bottleneck" in ev
        assert ev["current_bottleneck"] == "new bottleneck text"

        # Old field names must NOT exist
        assert "productive_factors" not in ev
        assert "failed_factors" not in ev
        assert "exhausted_directions" not in ev
        assert "bottleneck" not in ev

        # Threads use "id", not "thread_id"
        threads = reloaded["deepening_threads"]
        assert len(threads) == 2
        for t in threads:
            assert "id" in t
            assert "thread_id" not in t

        # T001 was updated
        t1 = next(t for t in threads if t["id"] == "T001")
        assert t1["status"] == "answered"


# -----------------------------------------------------------------------
# TestGlobalEscalation
# -----------------------------------------------------------------------


class TestGlobalEscalation:
    """Tests for global escalation persistence and status machine."""

    def test_save_and_load(self, tmp_path):
        path = tmp_path / "state" / "global_escalation.yaml"
        delta = GlobalEscalationDelta(
            batch_id="batch_010",
            proposed_lessons=[{"lesson": "avoid $vwap"}],
            proposed_forbidden=[{"pattern": "Neg("}],
        )
        save_global_escalation(path, delta)
        entries = load_global_escalation(path)

        assert len(entries) == 1
        assert entries[0]["batch_id"] == "batch_010"
        assert entries[0]["status"] == "pending"
        assert len(entries[0]["proposed_lessons"]) == 1

    def test_append_multiple(self, tmp_path):
        path = tmp_path / "state" / "global_escalation.yaml"

        save_global_escalation(
            path, GlobalEscalationDelta(batch_id="batch_010")
        )
        save_global_escalation(
            path, GlobalEscalationDelta(batch_id="batch_011")
        )
        save_global_escalation(
            path, GlobalEscalationDelta(batch_id="batch_012")
        )

        entries = load_global_escalation(path)
        assert len(entries) == 3
        assert [e["batch_id"] for e in entries] == [
            "batch_010",
            "batch_011",
            "batch_012",
        ]

    def test_transition_status(self, tmp_path):
        path = tmp_path / "state" / "global_escalation.yaml"
        save_global_escalation(
            path, GlobalEscalationDelta(batch_id="batch_010")
        )

        # pending -> consumed
        transition_escalation(path, "batch_010", "consumed")
        entries = load_global_escalation(path)
        assert entries[0]["status"] == "consumed"
        assert "consumed_at" in entries[0]

        # consumed -> applied
        transition_escalation(path, "batch_010", "applied", resolution="added to lessons")
        entries = load_global_escalation(path)
        assert entries[0]["status"] == "applied"
        assert "resolved_at" in entries[0]
        assert entries[0]["resolution"] == "added to lessons"

    def test_transition_invalid_raises(self, tmp_path):
        path = tmp_path / "state" / "global_escalation.yaml"
        save_global_escalation(
            path, GlobalEscalationDelta(batch_id="batch_010")
        )

        # pending -> applied (skip consumed) should fail
        with pytest.raises(ValueError, match="Cannot transition"):
            transition_escalation(path, "batch_010", "applied")

    def test_transition_missing_batch_raises(self, tmp_path):
        path = tmp_path / "state" / "global_escalation.yaml"
        save_global_escalation(
            path, GlobalEscalationDelta(batch_id="batch_010")
        )

        with pytest.raises(ValueError, match="No escalation entry"):
            transition_escalation(path, "batch_999", "consumed")

    def test_load_missing_file(self, tmp_path):
        path = tmp_path / "nonexistent.yaml"
        entries = load_global_escalation(path)
        assert entries == []

    def test_load_empty_file(self, tmp_path):
        path = tmp_path / "empty.yaml"
        path.write_text("", encoding="utf-8")
        entries = load_global_escalation(path)
        assert entries == []

    def test_consumed_then_dismissed(self, tmp_path):
        path = tmp_path / "state" / "global_escalation.yaml"
        save_global_escalation(
            path, GlobalEscalationDelta(batch_id="batch_010")
        )
        transition_escalation(path, "batch_010", "consumed")
        transition_escalation(path, "batch_010", "dismissed", resolution="not relevant")

        entries = load_global_escalation(path)
        assert entries[0]["status"] == "dismissed"
        assert entries[0]["resolution"] == "not relevant"

    def test_saturation_signal_preserved(self, tmp_path):
        path = tmp_path / "state" / "global_escalation.yaml"
        delta = GlobalEscalationDelta(
            batch_id="batch_010",
            saturation_signal={"signal_type": "ohlcv_exhausted", "evidence": 0.95},
        )
        save_global_escalation(path, delta)

        entries = load_global_escalation(path)
        assert entries[0]["saturation_signal"]["signal_type"] == "ohlcv_exhausted"


# -----------------------------------------------------------------------
# TestRecomputeState
# -----------------------------------------------------------------------


class _MockStateStore:
    """Minimal mock that records calls to update_state."""

    def __init__(self, initial_state: dict | None = None):
        self._state = initial_state or {}
        self.update_calls: list = []

    def update_state(self, patch: dict) -> dict:
        self.update_calls.append(patch)
        self._state.update(patch)
        return dict(self._state)


class TestRecomputeState:
    """Tests for recompute_research_state()."""

    def _setup_cards(self, tmp_path: Path, statuses: dict) -> Path:
        """Create card YAML files with given statuses.  statuses = {logic_id: status}."""
        cards_dir = tmp_path / "logic" / "cards"
        cards_dir.mkdir(parents=True, exist_ok=True)
        for lid, status in statuses.items():
            card = {"logic_id": lid, "status": status}
            save_yaml(cards_dir / f"{lid}.yaml", card)
        return cards_dir

    def test_derives_active_warm(self, tmp_path):
        cards_dir = self._setup_cards(tmp_path, {
            "L001": "active",
            "L002": "warm",
            "L003": "dead",
            "L004": "active",
            "L005": "saturated",
            "L006": "warm",
        })
        store = _MockStateStore()
        result = recompute_research_state(cards_dir, store)

        assert sorted(result["active_logic_ids"]) == ["L001", "L004"]
        assert sorted(result["warm_logic_ids"]) == ["L002", "L006"]

    def test_preserves_other_fields(self, tmp_path):
        cards_dir = self._setup_cards(tmp_path, {"L001": "active"})
        store = _MockStateStore(initial_state={
            "current_batch": "batch_042",
            "mode": "formal",
        })

        result = recompute_research_state(cards_dir, store)

        assert result["current_batch"] == "batch_042"
        assert result["mode"] == "formal"
        assert result["active_logic_ids"] == ["L001"]

    def test_empty_cards_dir(self, tmp_path):
        cards_dir = tmp_path / "logic" / "cards"
        cards_dir.mkdir(parents=True, exist_ok=True)
        store = _MockStateStore()

        result = recompute_research_state(cards_dir, store)

        assert result["active_logic_ids"] == []
        assert result["warm_logic_ids"] == []

    def test_only_one_update_call(self, tmp_path):
        cards_dir = self._setup_cards(tmp_path, {
            "L001": "active",
            "L002": "warm",
        })
        store = _MockStateStore()
        recompute_research_state(cards_dir, store)

        assert len(store.update_calls) == 1


# -----------------------------------------------------------------------
# TestWriteReflectionMd
# -----------------------------------------------------------------------


class TestWriteReflectionMd:
    """Tests for write_reflection_md()."""

    def test_creates_file(self, tmp_path):
        path = tmp_path / "reflections" / "L001.md"
        delta = _make_delta(generated_this_batch=5, admits_this_batch=2)
        write_reflection_md(path, delta, "Good batch overall.")

        assert path.exists()
        content = path.read_text(encoding="utf-8")
        assert "Batch batch_002" in content
        assert "**Generated**: 5" in content
        assert "**Admitted**: 2" in content
        assert "Good batch overall." in content

    def test_appends_to_existing(self, tmp_path):
        path = tmp_path / "reflections" / "L001.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# L001 Reflections\n", encoding="utf-8")

        delta1 = _make_delta(batch_id="batch_001", generated_this_batch=3)
        write_reflection_md(path, delta1, "First reflection.")

        delta2 = _make_delta(batch_id="batch_002", generated_this_batch=5)
        write_reflection_md(path, delta2, "Second reflection.")

        content = path.read_text(encoding="utf-8")
        assert "# L001 Reflections" in content
        assert "Batch batch_001" in content
        assert "Batch batch_002" in content
        assert "First reflection." in content
        assert "Second reflection." in content

    def test_includes_status_change(self, tmp_path):
        path = tmp_path / "reflections" / "L001.md"
        delta = _make_delta(status_change="warm", status_reason="cooling down")
        write_reflection_md(path, delta, "Narrative.")

        content = path.read_text(encoding="utf-8")
        assert "warm" in content
        assert "cooling down" in content


# -----------------------------------------------------------------------
# TestConsumeResolveAPI
# -----------------------------------------------------------------------


class TestConsumeResolveAPI:
    """Tests for the programmatic consume/resolve escalation API."""

    def test_consume_pending(self, tmp_path):
        path = tmp_path / "state" / "global_escalation.yaml"
        save_global_escalation(path, GlobalEscalationDelta(batch_id="b1"))
        save_global_escalation(path, GlobalEscalationDelta(batch_id="b2"))

        consumed = consume_pending_escalations(path)
        assert len(consumed) == 2
        assert all(c["status"] == "consumed" for c in consumed)
        assert all("consumed_at" in c for c in consumed)

        # Idempotent: second call returns empty
        consumed2 = consume_pending_escalations(path)
        assert consumed2 == []

    def test_consume_empty(self, tmp_path):
        path = tmp_path / "nonexistent.yaml"
        consumed = consume_pending_escalations(path)
        assert consumed == []

    def test_consume_skips_non_pending(self, tmp_path):
        path = tmp_path / "state" / "global_escalation.yaml"
        save_global_escalation(path, GlobalEscalationDelta(batch_id="b1"))
        save_global_escalation(path, GlobalEscalationDelta(batch_id="b2"))
        # Consume first time
        consume_pending_escalations(path)
        # Add one more pending
        save_global_escalation(path, GlobalEscalationDelta(batch_id="b3"))

        consumed = consume_pending_escalations(path)
        assert len(consumed) == 1
        assert consumed[0]["batch_id"] == "b3"

    def test_resolve_applied(self, tmp_path):
        path = tmp_path / "state" / "global_escalation.yaml"
        save_global_escalation(path, GlobalEscalationDelta(batch_id="b1"))
        consume_pending_escalations(path)

        resolve_escalation(path, "b1", "added to lessons")
        entries = load_global_escalation(path)
        assert entries[0]["status"] == "applied"
        assert entries[0]["resolution"] == "added to lessons"

    def test_resolve_dismissed(self, tmp_path):
        path = tmp_path / "state" / "global_escalation.yaml"
        save_global_escalation(path, GlobalEscalationDelta(batch_id="b1"))
        consume_pending_escalations(path)

        resolve_escalation(path, "b1", "not relevant", dismiss=True)
        entries = load_global_escalation(path)
        assert entries[0]["status"] == "dismissed"
        assert entries[0]["resolution"] == "not relevant"

    def test_resolve_without_consume_raises(self, tmp_path):
        path = tmp_path / "state" / "global_escalation.yaml"
        save_global_escalation(path, GlobalEscalationDelta(batch_id="b1"))

        with pytest.raises(ValueError, match="Cannot transition"):
            resolve_escalation(path, "b1", "skip consume")
