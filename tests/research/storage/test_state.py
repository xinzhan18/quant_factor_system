"""Tests for the state.yaml read/write layer and phase transitions."""

from __future__ import annotations

from pathlib import Path

import pytest

from research.storage.state import (
    InvalidPhaseTransition,
    InvalidStateSchema,
    State,
    StateFile,
)
from research.storage.yaml_io import save_yaml


def _bootstrap_state_file(tmp_path: Path) -> StateFile:
    """Initialize a clean state.yaml at tmp_path/state.yaml and return the facade."""
    p = tmp_path / "state.yaml"
    save_yaml(
        p,
        {
            "current_batch": None,
            "current_batch_phase": None,
            "last_batch": None,
            "round": 0,
            "last_activity": "2026-04-12T00:00:00Z",
            "rounds_since_last_consolidation": 0,
        },
    )
    return StateFile(p)


class TestStateFromDict:
    def test_missing_required_field_raises(self) -> None:
        with pytest.raises(InvalidStateSchema, match="missing required"):
            State.from_dict({"current_batch": None})

    def test_invalid_phase_raises(self) -> None:
        with pytest.raises(InvalidStateSchema, match="current_batch_phase"):
            State.from_dict(
                {
                    "current_batch": None,
                    "current_batch_phase": "banana",
                    "last_batch": None,
                    "round": 0,
                    "last_activity": "2026-04-12T00:00:00Z",
                    "rounds_since_last_consolidation": 0,
                }
            )

    def test_roundtrip_dict(self) -> None:
        d = {
            "current_batch": "batch_042",
            "current_batch_phase": "executing",
            "last_batch": "batch_041",
            "round": 42,
            "last_activity": "2026-04-12T00:00:00Z",
            "rounds_since_last_consolidation": 3,
        }
        s = State.from_dict(d)
        assert s.to_dict() == d

    def test_with_patch_is_immutable_derive(self) -> None:
        s1 = State(
            current_batch=None,
            current_batch_phase=None,
            last_batch=None,
            round=0,
            last_activity="2026-04-12T00:00:00Z",
            rounds_since_last_consolidation=0,
        )
        s2 = s1.with_patch(round=5)
        assert s1.round == 0
        assert s2.round == 5


class TestStateFileReadWrite:
    def test_read_missing_raises(self, tmp_path: Path) -> None:
        sf = StateFile(tmp_path / "absent.yaml")
        with pytest.raises(InvalidStateSchema, match="does not exist"):
            sf.read()

    def test_read_roundtrip(self, tmp_path: Path) -> None:
        sf = _bootstrap_state_file(tmp_path)
        s = sf.read()
        assert s.current_batch is None
        assert s.current_batch_phase is None
        assert s.round == 0

    def test_write_stamps_last_activity(self, tmp_path: Path) -> None:
        sf = _bootstrap_state_file(tmp_path)
        s = sf.read()
        original_ts = s.last_activity
        sf.write(s)
        s2 = sf.read()
        # last_activity was re-stamped with current time → differs
        assert s2.last_activity != original_ts
        # Everything else preserved
        assert s2.current_batch == s.current_batch
        assert s2.round == s.round


class TestPhaseTransitions:
    def test_happy_path_full_cycle(self, tmp_path: Path) -> None:
        sf = _bootstrap_state_file(tmp_path)
        # Begin a batch
        s = sf.begin_batch("batch_001")
        assert s.current_batch == "batch_001"
        assert s.current_batch_phase == "designed"
        # Advance through the DAG
        s = sf.transition_phase("executing")
        assert s.current_batch_phase == "executing"
        s = sf.transition_phase("judged")
        assert s.current_batch_phase == "judged"
        s = sf.transition_phase("archived")
        assert s.current_batch_phase == "archived"
        # Finish → round++, current_batch → last_batch
        s = sf.finish_batch()
        assert s.current_batch is None
        assert s.current_batch_phase is None
        assert s.last_batch == "batch_001"
        assert s.round == 1
        assert s.rounds_since_last_consolidation == 1

    def test_begin_while_already_in_batch_raises(self, tmp_path: Path) -> None:
        sf = _bootstrap_state_file(tmp_path)
        sf.begin_batch("batch_001")
        with pytest.raises(InvalidPhaseTransition, match="already in batch"):
            sf.begin_batch("batch_002")

    def test_skip_phase_raises(self, tmp_path: Path) -> None:
        sf = _bootstrap_state_file(tmp_path)
        sf.begin_batch("batch_001")
        with pytest.raises(InvalidPhaseTransition, match="designed.*judged"):
            sf.transition_phase("judged")  # skipped executing

    def test_backwards_transition_raises(self, tmp_path: Path) -> None:
        sf = _bootstrap_state_file(tmp_path)
        sf.begin_batch("batch_001")
        sf.transition_phase("executing")
        with pytest.raises(InvalidPhaseTransition):
            sf.transition_phase("designed")

    def test_double_archive_raises_q32_idempotency(self, tmp_path: Path) -> None:
        """Q32: re-running archive on an already-archived batch must raise."""
        sf = _bootstrap_state_file(tmp_path)
        sf.begin_batch("batch_001")
        sf.transition_phase("executing")
        sf.transition_phase("judged")
        sf.transition_phase("archived")
        with pytest.raises(InvalidPhaseTransition):
            sf.transition_phase("archived")

    def test_finish_before_archived_raises(self, tmp_path: Path) -> None:
        sf = _bootstrap_state_file(tmp_path)
        sf.begin_batch("batch_001")
        sf.transition_phase("executing")
        with pytest.raises(InvalidPhaseTransition, match="must be archived"):
            sf.finish_batch()


class TestConsolidation:
    def test_mark_consolidated_resets_counter(self, tmp_path: Path) -> None:
        sf = _bootstrap_state_file(tmp_path)
        # Simulate 3 completed batches by direct patch
        s = sf.read().with_patch(rounds_since_last_consolidation=3)
        sf.write(s)
        assert sf.read().rounds_since_last_consolidation == 3

        sf.mark_consolidated()
        assert sf.read().rounds_since_last_consolidation == 0

    def test_mark_consolidated_while_in_batch_raises(self, tmp_path: Path) -> None:
        sf = _bootstrap_state_file(tmp_path)
        sf.begin_batch("batch_001")
        with pytest.raises(InvalidPhaseTransition, match="in flight"):
            sf.mark_consolidated()
