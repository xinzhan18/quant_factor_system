"""Tests for ForbiddenManager: 3-state lifecycle CRUD."""

import yaml
import pytest

from research.governance.forbidden_manager import (
    ForbiddenManager,
    REASSESSMENT_TRIGGERS,
    VALID_STATES,
)


@pytest.fixture
def fm(tmp_path):
    return ForbiddenManager(tmp_path)


def _sample_pattern(pid="FP001"):
    return {
        "pattern_id": pid,
        "type": "expression_template",
        "summary": "plain breakout no volume context",
        "reason": "repeatedly no incremental value",
        "failure_mode": "weak_signal",
    }


# ---------------------------------------------------------------------------
# Add
# ---------------------------------------------------------------------------

class TestAdd:
    def test_add_creates_active_pattern(self, fm):
        p = fm.add(_sample_pattern())
        assert p["status"] == "active"
        assert "created_at" in p
        assert len(p["history"]) == 1
        assert p["history"][0]["action"] == "add"

    def test_add_persists_to_yaml(self, fm):
        fm.add(_sample_pattern())
        data = yaml.safe_load(fm.path.read_text())
        assert len(data) == 1
        assert data[0]["pattern_id"] == "FP001"

    def test_add_duplicate_raises(self, fm):
        fm.add(_sample_pattern())
        with pytest.raises(ValueError, match="already exists"):
            fm.add(_sample_pattern())

    def test_add_missing_keys_raises(self, fm):
        with pytest.raises(ValueError, match="Missing required keys"):
            fm.add({"pattern_id": "FP001"})

    def test_add_multiple(self, fm):
        fm.add(_sample_pattern("FP001"))
        fm.add(_sample_pattern("FP002"))
        assert len(fm.list_patterns()) == 2


# ---------------------------------------------------------------------------
# List / Get
# ---------------------------------------------------------------------------

class TestListGet:
    def test_list_empty(self, fm):
        assert fm.list_patterns() == []

    def test_list_all(self, fm):
        fm.add(_sample_pattern("FP001"))
        fm.add(_sample_pattern("FP002"))
        assert len(fm.list_patterns()) == 2

    def test_list_by_state(self, fm):
        fm.add(_sample_pattern("FP001"))
        fm.add(_sample_pattern("FP002"))
        fm.reassess("FP002", "opposite_evidence")
        active = fm.list_patterns(state="active")
        assert len(active) == 1
        assert active[0]["pattern_id"] == "FP001"
        under_review = fm.list_patterns(state="under_review")
        assert len(under_review) == 1

    def test_get_existing(self, fm):
        fm.add(_sample_pattern())
        p = fm.get("FP001")
        assert p is not None
        assert p["pattern_id"] == "FP001"

    def test_get_nonexistent(self, fm):
        assert fm.get("FPXXX") is None


# ---------------------------------------------------------------------------
# Reassess (active -> under_review)
# ---------------------------------------------------------------------------

class TestReassess:
    def test_active_to_under_review(self, fm):
        fm.add(_sample_pattern())
        p = fm.reassess("FP001", "opposite_evidence", evidence="2 batches show signal")
        assert p["status"] == "under_review"
        assert len(p["history"]) == 2
        last = p["history"][-1]
        assert last["action"] == "reassess"
        assert last["trigger"] == "opposite_evidence"

    def test_invalid_trigger_raises(self, fm):
        fm.add(_sample_pattern())
        with pytest.raises(ValueError, match="Invalid trigger"):
            fm.reassess("FP001", "bad_trigger")

    def test_reassess_nonexistent_raises(self, fm):
        with pytest.raises(KeyError, match="not found"):
            fm.reassess("FPXXX", "opposite_evidence")

    def test_cannot_reassess_retired(self, fm):
        fm.add(_sample_pattern())
        fm.retire("FP001")
        with pytest.raises(ValueError, match="Cannot 'reassess'"):
            fm.reassess("FP001", "opposite_evidence")

    def test_all_valid_triggers(self, fm):
        for i, trigger in enumerate(sorted(REASSESSMENT_TRIGGERS)):
            pid = f"FP{i:03d}"
            fm.add(_sample_pattern(pid))
            p = fm.reassess(pid, trigger)
            assert p["status"] == "under_review"


# ---------------------------------------------------------------------------
# Retire
# ---------------------------------------------------------------------------

class TestRetire:
    def test_active_to_retired(self, fm):
        fm.add(_sample_pattern())
        p = fm.retire("FP001", reason="no longer relevant")
        assert p["status"] == "retired"

    def test_under_review_to_retired(self, fm):
        fm.add(_sample_pattern())
        fm.reassess("FP001", "definition_too_broad")
        p = fm.retire("FP001")
        assert p["status"] == "retired"

    def test_cannot_retire_already_retired(self, fm):
        fm.add(_sample_pattern())
        fm.retire("FP001")
        with pytest.raises(ValueError, match="Cannot 'retire'"):
            fm.retire("FP001")


# ---------------------------------------------------------------------------
# Reactivate
# ---------------------------------------------------------------------------

class TestReactivate:
    def test_retired_to_active(self, fm):
        fm.add(_sample_pattern())
        fm.retire("FP001")
        p = fm.reactivate("FP001", reason="new evidence supports ban")
        assert p["status"] == "active"

    def test_under_review_to_active(self, fm):
        fm.add(_sample_pattern())
        fm.reassess("FP001", "original_evidence_wrong")
        p = fm.reactivate("FP001")
        assert p["status"] == "active"

    def test_cannot_reactivate_active(self, fm):
        fm.add(_sample_pattern())
        with pytest.raises(ValueError, match="Cannot 'reactivate'"):
            fm.reactivate("FP001")


# ---------------------------------------------------------------------------
# Full lifecycle
# ---------------------------------------------------------------------------

class TestFullLifecycle:
    def test_active_reassess_retire_reactivate(self, fm):
        fm.add(_sample_pattern())

        fm.reassess("FP001", "opposite_evidence")
        assert fm.get("FP001")["status"] == "under_review"

        fm.retire("FP001")
        assert fm.get("FP001")["status"] == "retired"

        fm.reactivate("FP001")
        p = fm.get("FP001")
        assert p["status"] == "active"
        assert len(p["history"]) == 4  # add, reassess, retire, reactivate

    def test_history_records_transitions(self, fm):
        fm.add(_sample_pattern())
        fm.reassess("FP001", "definition_too_broad")
        fm.reactivate("FP001")
        p = fm.get("FP001")
        actions = [h["action"] for h in p["history"]]
        assert actions == ["add", "reassess", "reactivate"]


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

class TestPersistence:
    def test_survives_reload(self, tmp_path):
        fm1 = ForbiddenManager(tmp_path)
        fm1.add(_sample_pattern())
        fm1.reassess("FP001", "opposite_evidence")

        fm2 = ForbiddenManager(tmp_path)
        p = fm2.get("FP001")
        assert p["status"] == "under_review"
        assert len(p["history"]) == 2

    def test_load_from_dict_format(self, tmp_path):
        """Support legacy format where file is a dict with 'forbidden_patterns' key."""
        path = tmp_path / "memory" / "forbidden.yaml"
        path.parent.mkdir(parents=True)
        data = {
            "forbidden_patterns": [
                {
                    "pattern_id": "FP001",
                    "type": "expression_template",
                    "summary": "test",
                    "reason": "test",
                    "failure_mode": "weak_signal",
                    "status": "active",
                }
            ]
        }
        path.write_text(yaml.safe_dump(data))
        fm = ForbiddenManager(tmp_path)
        assert len(fm.list_patterns()) == 1
