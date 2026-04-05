"""Tests for research.logic.family_registry — Family CRUD operations."""
import pytest

from research.logic.family_registry import (
    FamilyRecord,
    FamilyRegistry,
    PROVISIONAL_PREFIX,
    VALID_FAMILY_STATUSES,
)


class TestFamilyRecord:
    def test_create_registered(self):
        rec = FamilyRecord(
            family_id="FM_001",
            name="breakout",
            status="registered",
        )
        assert rec.family_id == "FM_001"
        assert rec.status == "registered"

    def test_create_provisional(self):
        rec = FamilyRecord(
            family_id="PF_001",
            name="auto_pattern_1",
            status="provisional",
        )
        assert rec.family_id == "PF_001"

    def test_provisional_requires_prefix(self):
        with pytest.raises(ValueError, match="PF_"):
            FamilyRecord(
                family_id="FM_001",
                name="bad",
                status="provisional",
            )

    def test_invalid_status(self):
        with pytest.raises(ValueError, match="Invalid family status"):
            FamilyRecord(
                family_id="FM_001",
                name="bad",
                status="invalid",
            )

    def test_roundtrip_dict(self):
        rec = FamilyRecord(
            family_id="FM_001",
            name="breakout",
            status="registered",
            description="price breakout patterns",
            typical_ops=["TsRank", "Std"],
            factor_ids=["F001", "F002"],
        )
        d = rec.to_dict()
        rec2 = FamilyRecord.from_dict(d)
        assert rec2.family_id == rec.family_id
        assert rec2.typical_ops == ["TsRank", "Std"]
        assert rec2.factor_ids == ["F001", "F002"]


class TestFamilyRegistry:
    def test_create_registered(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        rec = reg.create(
            name="breakout",
            status="registered",
            description="price breakout patterns",
        )
        assert rec.family_id == "FM_001"
        assert rec.status == "registered"

        # Verify file
        path = tmp_path / "registry" / "families" / "FM_001.yaml"
        assert path.exists()

    def test_create_provisional(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        rec = reg.create(
            name="auto_pattern",
            status="provisional",
        )
        assert rec.family_id.startswith("PF_")

    def test_auto_increment(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        r1 = reg.create(name="a", status="registered")
        r2 = reg.create(name="b", status="registered")
        assert r1.family_id == "FM_001"
        assert r2.family_id == "FM_002"

    def test_get(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        reg.create(name="test", status="registered")
        loaded = reg.get("FM_001")
        assert loaded is not None
        assert loaded.name == "test"

    def test_get_nonexistent(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        assert reg.get("FM_999") is None

    def test_list_all(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        reg.create(name="a", status="registered")
        reg.create(name="b", status="provisional")
        all_families = reg.list_families()
        assert len(all_families) == 2

    def test_list_by_status(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        reg.create(name="a", status="registered")
        reg.create(name="b", status="provisional")
        registered = reg.list_families(status="registered")
        assert len(registered) == 1
        assert registered[0].name == "a"

    def test_update(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        rec = reg.create(name="test", status="registered")
        rec.description = "updated description"
        reg.update(rec)

        reloaded = reg.get(rec.family_id)
        assert reloaded.description == "updated description"

    def test_update_nonexistent_raises(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        rec = FamilyRecord(
            family_id="FM_999", name="x", status="registered"
        )
        with pytest.raises(KeyError, match="not found"):
            reg.update(rec)

    def test_delete(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        reg.create(name="test", status="registered")
        assert reg.delete("FM_001") is True
        assert reg.get("FM_001") is None

    def test_delete_nonexistent(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        assert reg.delete("FM_999") is False

    def test_add_factor(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        rec = reg.create(name="test", status="registered")
        reg.add_factor(rec.family_id, "F001")
        reg.add_factor(rec.family_id, "F002")
        # Duplicate should be idempotent
        reg.add_factor(rec.family_id, "F001")

        reloaded = reg.get(rec.family_id)
        assert reloaded.factor_ids == ["F001", "F002"]

    def test_add_logic(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        rec = reg.create(name="test", status="registered")
        reg.add_logic(rec.family_id, "L001")

        reloaded = reg.get(rec.family_id)
        assert reloaded.logic_ids == ["L001"]

    def test_promote_to_registered(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        prov = reg.create(name="detected_pattern", status="provisional")
        assert prov.family_id.startswith("PF_")

        promoted = reg.promote_to_registered(prov.family_id)
        assert promoted.family_id.startswith("FM_")
        assert promoted.status == "registered"
        assert promoted.name == "detected_pattern"

        # Old provisional file should be gone
        assert reg.get(prov.family_id) is None
        # New registered file should exist
        assert reg.get(promoted.family_id) is not None

    def test_promote_non_provisional_raises(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        rec = reg.create(name="already_reg", status="registered")
        with pytest.raises(ValueError, match="provisional"):
            reg.promote_to_registered(rec.family_id)

    def test_index_file_updated(self, tmp_path):
        reg = FamilyRegistry(tmp_path)
        reg.create(name="a", status="registered")
        reg.create(name="b", status="registered")

        import yaml

        index_path = tmp_path / "registry" / "families" / "families_index.yaml"
        assert index_path.exists()
        with open(index_path) as f:
            data = yaml.safe_load(f)
        assert data["count"] == 2
        assert len(data["families"]) == 2

    def test_no_hard_blocking_for_provisional(self, tmp_path):
        """Provisional families should not block factor assignment."""
        reg = FamilyRegistry(tmp_path)
        prov = reg.create(name="auto", status="provisional")
        # Should be able to add factors to provisional families
        reg.add_factor(prov.family_id, "F099")
        reloaded = reg.get(prov.family_id)
        assert "F099" in reloaded.factor_ids
