"""Tests for research.logic.reflect."""
from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from research.logic.reflect import (
    GlobalEscalationDelta,
    LogicBeliefDelta,
    apply_belief_delta,
    consume_pending_escalations,
    load_global_escalation,
    recompute_research_state,
    resolve_escalation,
    save_global_escalation,
    transition_escalation,
    write_reflection_md,
)
from research.storage.paths import StoragePaths
from research.storage.state_store import StateStore
from research.storage.yaml_io import load_yaml, save_yaml


def _minimal_card(
    logic_id: str = "L001",
    *,
    status: str = "active",
    priority: str = "high",
    **overrides: Any,
) -> dict[str, Any]:
    card: dict[str, Any] = {
        "logic_id": logic_id,
        "name": "test logic",
        "category": "volume_price",
        "status": status,
        "priority": priority,
        "hypothesis": {
            "condition": "test",
            "behavior": "test",
            "timeframe": "5-20d",
        },
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
            "productive_families": [],
            "failed_families": [],
            "exhausted_routes": [],
            "current_bottleneck": "",
            "transitions": [],
            "promoted_families": [],
        },
        "deepening_threads": [],
        "next_actions": [],
        "last_reflected_batch": "batch_001",
        "created_at": "2026-01-01",
        "updated_at": "2026-01-01",
    }
    card.update(overrides)
    return card


def _write_card(tmp_path: Path, card: dict[str, Any]) -> Path:
    cards_dir = tmp_path / "logic" / "cards"
    cards_dir.mkdir(parents=True, exist_ok=True)
    card_path = cards_dir / f"{card['logic_id']}.yaml"
    save_yaml(card_path, card)
    return card_path


def _make_delta(**overrides: Any) -> LogicBeliefDelta:
    defaults: dict[str, Any] = {
        "logic_id": "L001",
        "batch_id": "batch_002",
    }
    defaults.update(overrides)
    return LogicBeliefDelta(**defaults)


class TestLogicBeliefDelta:
    def test_defaults(self):
        delta = LogicBeliefDelta(logic_id="L001", batch_id="batch_001")
        assert delta.status_change is None
        assert delta.generated_this_batch == 0
        assert delta.admits_this_batch == 0
        assert delta.families_to_add == []
        assert delta.threads_to_add == []

    def test_mutable_defaults_are_independent(self):
        d1 = LogicBeliefDelta(logic_id="L001", batch_id="b1")
        d2 = LogicBeliefDelta(logic_id="L002", batch_id="b2")
        d1.families_to_add.append("FM_x")
        assert d2.families_to_add == []


class TestApplyBeliefDelta:
    def test_status_change(self, tmp_path: Path):
        card_path = _write_card(tmp_path, _minimal_card(status="active"))
        delta = _make_delta(status_change="warm", status_reason="cooling down")

        result = apply_belief_delta(card_path, delta)

        assert result["status"] == "warm"
        transitions = result["evidence_summary"]["transitions"]
        assert transitions[0]["from"] == "active"
        assert transitions[0]["to"] == "warm"
        assert transitions[0]["reason"] == "cooling down"
        assert load_yaml(card_path)["status"] == "warm"

    def test_status_change_illegal_raises(self, tmp_path: Path):
        card_path = _write_card(tmp_path, _minimal_card(status="dead"))

        with pytest.raises(ValueError, match="Cannot transition"):
            apply_belief_delta(card_path, _make_delta(status_change="active"))

    def test_contract_evolution(self, tmp_path: Path):
        card_path = _write_card(tmp_path, _minimal_card())
        delta = _make_delta(
            focus_question_update="What drives momentum decay?",
            families_to_add=["FM_momentum", "FM_reversal"],
            families_to_remove=["FM_vol"],
            ops_to_add=["TsRank", "CsZscore"],
            avoid_patterns_to_add=["$vwap", "Neg("],
        )

        result = apply_belief_delta(card_path, delta)
        contract = result["contract"]

        assert contract["current_focus_question"] == "What drives momentum decay?"
        assert sorted(contract["preferred_families"]) == ["FM_momentum", "FM_reversal"]
        assert "Std" in contract["suggested_ops"]
        assert "TsRank" in contract["suggested_ops"]
        assert "CsZscore" in contract["suggested_ops"]
        assert "$vwap" in contract["avoid_patterns"]
        assert "Neg(" in contract["avoid_patterns"]

    def test_memory_counters(self, tmp_path: Path):
        card_path = _write_card(tmp_path, _minimal_card())
        delta = _make_delta(generated_this_batch=6, admits_this_batch=2)

        result = apply_belief_delta(card_path, delta)
        ev = result["evidence_summary"]

        assert ev["factors_generated"] == 16
        assert ev["factors_admitted"] == 5
        assert ev["rounds_without_admit"] == 0

    def test_memory_counters_no_admits(self, tmp_path: Path):
        card_path = _write_card(tmp_path, _minimal_card())
        delta = _make_delta(generated_this_batch=4, admits_this_batch=0)

        result = apply_belief_delta(card_path, delta)
        ev = result["evidence_summary"]

        assert ev["factors_generated"] == 14
        assert ev["factors_admitted"] == 3
        assert ev["rounds_without_admit"] == 2

    def test_family_memory_merge(self, tmp_path: Path):
        card = _minimal_card()
        card["evidence_summary"]["productive_families"] = [
            {"family_id": "FM_vol", "count": 2, "best_ic": 0.04},
        ]
        card_path = _write_card(tmp_path, card)
        delta = _make_delta(
            new_productive=[
                {"family_id": "FM_vol", "count": 3, "best_ic": 0.05},
                {"family_id": "FM_reversal", "count": 1, "best_ic": 0.03},
            ],
            new_failed=[{"family_id": "FM_bad", "reason": "IC too low"}],
            new_exhausted=[{"family_id": "FM_dead", "verdict": "kill"}],
            bottleneck_update="correlation ceiling at 0.7",
        )

        result = apply_belief_delta(card_path, delta)
        ev = result["evidence_summary"]

        assert len(ev["productive_families"]) == 2
        fm_vol = next(p for p in ev["productive_families"] if p["family_id"] == "FM_vol")
        assert fm_vol["count"] == 3
        assert ev["failed_families"][0]["family_id"] == "FM_bad"
        assert ev["exhausted_routes"][0]["family_id"] == "FM_dead"
        assert ev["current_bottleneck"] == "correlation ceiling at 0.7"

    def test_thread_mutations(self, tmp_path: Path):
        card = _minimal_card()
        card["deepening_threads"] = [
            {"id": "T1", "topic": "volume spikes", "status": "active"},
            {"id": "T2", "topic": "reversal decay", "status": "active"},
        ]
        card_path = _write_card(tmp_path, card)
        delta = _make_delta(
            threads_to_add=[{"id": "T3", "topic": "new direction", "status": "active"}],
            threads_to_update=[{"id": "T1", "notes": "confirmed", "status": "answered"}],
            threads_to_park=["T2"],
        )

        result = apply_belief_delta(card_path, delta)
        threads = result["deepening_threads"]

        assert len(threads) == 3
        assert next(t for t in threads if t["id"] == "T1")["status"] == "answered"
        assert next(t for t in threads if t["id"] == "T1")["notes"] == "confirmed"
        assert next(t for t in threads if t["id"] == "T2")["status"] == "parked"
        assert next(t for t in threads if t["id"] == "T3")["topic"] == "new direction"

    def test_next_actions_and_batch(self, tmp_path: Path):
        card_path = _write_card(tmp_path, _minimal_card(next_actions=["old action"]))
        result = apply_belief_delta(
            card_path,
            _make_delta(batch_id="batch_005", next_actions=["action A", "action B"]),
        )

        assert result["next_actions"] == ["action A", "action B"]
        assert result["last_reflected_batch"] == "batch_005"

    def test_missing_card_file_raises(self, tmp_path: Path):
        with pytest.raises(FileNotFoundError, match="not found"):
            apply_belief_delta(
                tmp_path / "logic" / "cards" / "L999.yaml",
                _make_delta(logic_id="L999"),
            )

    def test_single_write(self, tmp_path: Path):
        card_path = _write_card(tmp_path, _minimal_card())
        delta = _make_delta(generated_this_batch=3, admits_this_batch=1)

        with patch("research.logic.reflect.save_yaml") as mock_save:
            apply_belief_delta(card_path, delta)
            assert mock_save.call_count == 1
            assert mock_save.call_args[0][0] == card_path

    def test_round_trip_real_card_schema(self, tmp_path: Path):
        card = {
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
                "productive_families": [{"family_id": "PF_pv_correlation", "factors": ["R001"]}],
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

        apply_belief_delta(card_path, delta)
        reloaded = load_yaml(card_path)
        ev = reloaded["evidence_summary"]

        assert "productive_families" in ev
        assert "failed_families" in ev
        assert "exhausted_routes" in ev
        assert "current_bottleneck" in ev
        assert "productive_factors" not in ev
        assert "failed_factors" not in ev
        assert "exhausted_directions" not in ev
        assert "bottleneck" not in ev

        threads = reloaded["deepening_threads"]
        assert len(threads) == 2
        assert all("id" in t and "thread_id" not in t for t in threads)


class TestWriteReflectionMd:
    def test_appends_batch_section(self, tmp_path: Path):
        reflection_path = tmp_path / "logic" / "reflections" / "L001.md"
        delta = _make_delta(
            generated_this_batch=4,
            admits_this_batch=1,
            status_change="warm",
            status_reason="cooling",
            bottleneck_update="corr ceiling",
            next_actions=["probe A", "probe B"],
        )

        write_reflection_md(reflection_path, delta, "Narrative body.")
        text = reflection_path.read_text(encoding="utf-8")

        assert "## Batch batch_002" in text
        assert "**Logic**: L001" in text
        assert "**Status change**: → warm (cooling)" in text
        assert "- probe A" in text
        assert "Narrative body." in text


class TestGlobalEscalation:
    def test_save_and_load(self, tmp_path: Path):
        path = tmp_path / "state" / "global_escalation.yaml"
        save_global_escalation(
            path,
            GlobalEscalationDelta(
                batch_id="batch_010",
                proposed_lessons=[{"lesson": "avoid $vwap"}],
                proposed_forbidden=[{"pattern": "Neg("}],
            ),
        )
        entries = load_global_escalation(path)

        assert len(entries) == 1
        assert entries[0]["batch_id"] == "batch_010"
        assert entries[0]["status"] == "pending"

    def test_append_multiple(self, tmp_path: Path):
        path = tmp_path / "state" / "global_escalation.yaml"
        save_global_escalation(path, GlobalEscalationDelta(batch_id="batch_010"))
        save_global_escalation(path, GlobalEscalationDelta(batch_id="batch_011"))

        entries = load_global_escalation(path)
        assert [e["batch_id"] for e in entries] == ["batch_010", "batch_011"]

    def test_transition_status(self, tmp_path: Path):
        path = tmp_path / "state" / "global_escalation.yaml"
        save_global_escalation(path, GlobalEscalationDelta(batch_id="batch_010"))

        transition_escalation(path, "batch_010", "consumed")
        entries = load_global_escalation(path)
        assert entries[0]["status"] == "consumed"
        assert "consumed_at" in entries[0]

        transition_escalation(path, "batch_010", "applied", resolution="accepted")
        entries = load_global_escalation(path)
        assert entries[0]["status"] == "applied"
        assert entries[0]["resolution"] == "accepted"

    def test_consume_and_resolve_api(self, tmp_path: Path):
        path = tmp_path / "state" / "global_escalation.yaml"
        save_global_escalation(path, GlobalEscalationDelta(batch_id="b1"))
        save_global_escalation(path, GlobalEscalationDelta(batch_id="b2"))

        consumed = consume_pending_escalations(path)
        assert len(consumed) == 2
        assert all(c["status"] == "consumed" for c in consumed)
        assert consume_pending_escalations(path) == []

        resolve_escalation(path, "b1", "added to lessons")
        resolve_escalation(path, "b2", "not relevant", dismiss=True)
        entries = load_global_escalation(path)
        status_map = {entry["batch_id"]: entry["status"] for entry in entries}
        assert status_map == {"b1": "applied", "b2": "dismissed"}


class TestRecomputeResearchState:
    def test_recompute_from_cards(self, tmp_path: Path):
        cards_dir = tmp_path / "storage" / "logic" / "cards"
        save_yaml(cards_dir / "L001.yaml", _minimal_card("L001", status="active"))
        save_yaml(cards_dir / "L002.yaml", _minimal_card("L002", status="warm"))
        save_yaml(cards_dir / "L003.yaml", _minimal_card("L003", status="parked"))

        paths = StoragePaths(tmp_path / "storage")
        state_store = StateStore(paths)
        save_yaml(
            paths.research_state_file,
            {"current_batch": "batch_005", "pending_holdout": 1},
        )

        state = recompute_research_state(cards_dir, state_store)

        assert state["active_logic_ids"] == ["L001"]
        assert state["warm_logic_ids"] == ["L002"]
        assert state["current_batch"] == "batch_005"
        assert state["pending_holdout"] == 1
