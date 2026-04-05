"""Tests for ColdStartPolicy: per-mechanism gradual unlock."""

import pytest

from research.governance.cold_start import (
    ColdStartPolicy,
    MechanismCounts,
    SystemCounts,
)


@pytest.fixture
def policy():
    return ColdStartPolicy()


# ---------------------------------------------------------------------------
# Cold-start mode detection
# ---------------------------------------------------------------------------

class TestColdStartDetection:
    def test_zero_counters_is_cold_start(self, policy):
        s = SystemCounts(completed_batches=0, admitted_count=0)
        assert policy.in_cold_start(s) is True

    def test_low_batches_is_cold_start(self, policy):
        s = SystemCounts(completed_batches=4, admitted_count=20)
        assert policy.in_cold_start(s) is True

    def test_low_admits_is_cold_start(self, policy):
        s = SystemCounts(completed_batches=10, admitted_count=9)
        assert policy.in_cold_start(s) is True

    def test_both_sufficient_exits_cold_start(self, policy):
        s = SystemCounts(completed_batches=5, admitted_count=10)
        assert policy.in_cold_start(s) is False

    def test_custom_thresholds(self):
        p = ColdStartPolicy(min_batches=2, min_admits=3)
        s = SystemCounts(completed_batches=2, admitted_count=3)
        assert p.in_cold_start(s) is False


# ---------------------------------------------------------------------------
# Per-mechanism unlock
# ---------------------------------------------------------------------------

class TestMechanismUnlock:
    def _system_ready(self):
        return SystemCounts(completed_batches=10, admitted_count=20)

    def test_family_overlap_locked_below_threshold(self, policy):
        mc = MechanismCounts(family_size=2)
        assert policy.is_unlocked("family_overlap", self._system_ready(), mc) is False

    def test_family_overlap_unlocked_at_threshold(self, policy):
        mc = MechanismCounts(family_size=3)
        assert policy.is_unlocked("family_overlap", self._system_ready(), mc) is True

    def test_subspace_locked(self, policy):
        mc = MechanismCounts(subspace_basis=1)
        assert policy.is_unlocked("subspace", self._system_ready(), mc) is False

    def test_subspace_unlocked(self, policy):
        mc = MechanismCounts(subspace_basis=2)
        assert policy.is_unlocked("subspace", self._system_ready(), mc) is True

    def test_promote_family_locked(self, policy):
        mc = MechanismCounts(promote_family_batches=1)
        assert policy.is_unlocked("promote_family", self._system_ready(), mc) is False

    def test_promote_family_unlocked(self, policy):
        mc = MechanismCounts(promote_family_batches=2)
        assert policy.is_unlocked("promote_family", self._system_ready(), mc) is True

    def test_productive_locked(self, policy):
        mc = MechanismCounts(cumulative_admits=2)
        assert policy.is_unlocked("productive", self._system_ready(), mc) is False

    def test_productive_unlocked(self, policy):
        mc = MechanismCounts(cumulative_admits=3)
        assert policy.is_unlocked("productive", self._system_ready(), mc) is True

    def test_saturated_locked(self, policy):
        mc = MechanismCounts(cumulative_no_progress_batches=4)
        assert policy.is_unlocked("saturated", self._system_ready(), mc) is False

    def test_saturated_unlocked(self, policy):
        mc = MechanismCounts(cumulative_no_progress_batches=5)
        assert policy.is_unlocked("saturated", self._system_ready(), mc) is True

    def test_dead_locked(self, policy):
        mc = MechanismCounts(cumulative_failure_batches=7)
        assert policy.is_unlocked("dead", self._system_ready(), mc) is False

    def test_dead_unlocked(self, policy):
        mc = MechanismCounts(cumulative_failure_batches=8)
        assert policy.is_unlocked("dead", self._system_ready(), mc) is True


# ---------------------------------------------------------------------------
# Cold-start blocks everything
# ---------------------------------------------------------------------------

class TestColdStartBlocksAll:
    def test_all_locked_during_cold_start(self, policy):
        cold_system = SystemCounts(completed_batches=2, admitted_count=5)
        mc = MechanismCounts(
            family_size=100,
            subspace_basis=100,
            promote_family_batches=100,
            cumulative_admits=100,
            cumulative_no_progress_batches=100,
            cumulative_failure_batches=100,
        )
        result = policy.check_all(cold_system, mc)
        assert all(v is False for v in result.values())


# ---------------------------------------------------------------------------
# check_all
# ---------------------------------------------------------------------------

class TestCheckAll:
    def test_check_all_returns_dict(self, policy):
        s = SystemCounts(completed_batches=10, admitted_count=20)
        mc = MechanismCounts(family_size=5, subspace_basis=3)
        result = policy.check_all(s, mc)
        assert isinstance(result, dict)
        assert "family_overlap" in result
        assert "subspace" in result
        assert result["family_overlap"] is True
        assert result["subspace"] is True
        # others default to 0, so should be False
        assert result["productive"] is False


# ---------------------------------------------------------------------------
# Unknown mechanism
# ---------------------------------------------------------------------------

class TestUnknownMechanism:
    def test_unknown_mechanism_is_locked(self, policy):
        s = SystemCounts(completed_batches=100, admitted_count=100)
        mc = MechanismCounts()
        assert policy.is_unlocked("nonexistent_mechanism", s, mc) is False


# ---------------------------------------------------------------------------
# Custom thresholds override defaults
# ---------------------------------------------------------------------------

class TestCustomMechanismThresholds:
    def test_override(self):
        p = ColdStartPolicy(thresholds={"family_overlap": 10})
        s = SystemCounts(completed_batches=10, admitted_count=20)
        mc = MechanismCounts(family_size=9)
        assert p.is_unlocked("family_overlap", s, mc) is False
        mc2 = MechanismCounts(family_size=10)
        assert p.is_unlocked("family_overlap", s, mc2) is True

    def test_thresholds_property_returns_copy(self):
        p = ColdStartPolicy()
        t = p.thresholds
        t["family_overlap"] = 999
        assert p.thresholds["family_overlap"] != 999
