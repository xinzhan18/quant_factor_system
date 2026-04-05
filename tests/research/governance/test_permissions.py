"""Tests for governance permissions module."""

import pytest

from research.governance.permissions import (
    Actor,
    PermissionEntry,
    TargetObject,
    WriteLevel,
    WRITE_PERMISSIONS,
    actor_can_write,
    required_level,
)


class TestWriteLevel:
    def test_level_values(self):
        assert WriteLevel.level_1.value == "level_1"
        assert WriteLevel.level_2.value == "level_2"

    def test_from_string(self):
        assert WriteLevel("level_1") is WriteLevel.level_1


class TestActorEnum:
    def test_known_actors(self):
        names = {a.value for a in Actor}
        assert "guarded_writer" in names
        assert "judge" in names
        assert "idea" in names
        assert "execute" in names


class TestTargetObjectEnum:
    def test_known_targets(self):
        names = {t.value for t in TargetObject}
        expected = {
            "factor_registry",
            "logic_card",
            "route_card",
            "research_state",
            "forbidden",
            "implementation_policy",
            "policy_upgrade_ledger",
            "judge_report",
            "search_ledger",
            "batch_result",
            "batch_manifest",
            "idea_report",
            "execute_report",
        }
        assert expected.issubset(names)


class TestWritePermissionsMap:
    def test_guarded_writer_can_write_factor_registry(self):
        assert actor_can_write(
            Actor.guarded_writer, TargetObject.factor_registry, "admit"
        )

    def test_guarded_writer_can_write_logic_card(self):
        assert actor_can_write(
            Actor.guarded_writer, TargetObject.logic_card, "create"
        )

    def test_guarded_writer_cannot_write_judge_report(self):
        assert not actor_can_write(
            Actor.guarded_writer, TargetObject.judge_report, "create"
        )

    def test_judge_can_write_policy_upgrade_ledger(self):
        assert actor_can_write(
            Actor.judge, TargetObject.policy_upgrade_ledger, "append"
        )

    def test_judge_cannot_write_factor_registry(self):
        assert not actor_can_write(
            Actor.judge, TargetObject.factor_registry, "admit"
        )

    def test_idea_can_write_batch_manifest(self):
        assert actor_can_write(
            Actor.idea, TargetObject.batch_manifest, "create"
        )

    def test_execute_can_write_batch_result(self):
        assert actor_can_write(
            Actor.execute, TargetObject.batch_result, "create"
        )

    def test_execute_cannot_write_forbidden(self):
        assert not actor_can_write(
            Actor.execute, TargetObject.forbidden, "add"
        )

    def test_unknown_action_rejected(self):
        assert not actor_can_write(
            Actor.guarded_writer, TargetObject.factor_registry, "destroy"
        )


class TestRequiredLevel:
    def test_factor_registry_is_level_1(self):
        lvl = required_level(Actor.guarded_writer, TargetObject.factor_registry)
        assert lvl == WriteLevel.level_1

    def test_forbidden_is_level_2(self):
        lvl = required_level(Actor.guarded_writer, TargetObject.forbidden)
        assert lvl == WriteLevel.level_2

    def test_implementation_policy_is_level_2(self):
        lvl = required_level(
            Actor.guarded_writer, TargetObject.implementation_policy
        )
        assert lvl == WriteLevel.level_2

    def test_no_permission_returns_none(self):
        lvl = required_level(Actor.execute, TargetObject.forbidden)
        assert lvl is None


class TestPermissionEntryFrozen:
    def test_entry_is_hashable(self):
        e = PermissionEntry(
            target=TargetObject.forbidden,
            level=WriteLevel.level_2,
            allowed_actions=frozenset({"add"}),
        )
        # frozen dataclass -> hashable
        assert hash(e) is not None
