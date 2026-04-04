"""Tests for canonical factor record schema."""
import pytest
from mining.domain.schema import FactorRecord, normalize_metrics, METRICS_ALIASES


class TestFactorRecord:
    def test_migration_defaults(self):
        """Raw FactorRecord defaults to legacy/v1 for migration safety."""
        rec = FactorRecord(
            id="001", name="test_factor", expression="Std($close, 20)",
            category="volatility", batch="batch_001",
        )
        assert rec.status == "legacy"
        assert rec.evaluation_version == "v1"
        assert rec.source == "dsl"

    def test_for_new_admission_factory(self):
        """for_new_admission() produces active/v2."""
        rec = FactorRecord.for_new_admission(
            id="001", name="test", expression="X",
            category="c", batch="b", metrics={"ic_mean": -0.02},
        )
        assert rec.status == "active"
        assert rec.evaluation_version == "v2"

    def test_for_migration_factory(self):
        """for_migration() produces legacy/v1."""
        rec = FactorRecord.for_migration(
            id="001", name="test", expression="X",
            category="c", batch="b",
        )
        assert rec.status == "legacy"
        assert rec.evaluation_version == "v1"

    def test_long_leg_from_negative_ic(self):
        rec = FactorRecord(
            id="001", name="x", expression="X", category="c", batch="b",
            metrics={"ic_mean": -0.05},
        )
        assert rec.long_leg == "low"

    def test_long_leg_from_positive_ic(self):
        rec = FactorRecord(
            id="002", name="x", expression="X", category="c", batch="b",
            metrics={"ic_mean": 0.03},
        )
        assert rec.long_leg == "high"

    def test_long_leg_from_zero_ic(self):
        rec = FactorRecord(
            id="003", name="x", expression="X", category="c", batch="b",
            metrics={"ic_mean": 0.0},
        )
        assert rec.long_leg == "high"

    def test_long_leg_none_when_no_ic(self):
        rec = FactorRecord(
            id="004", name="x", expression="X", category="c", batch="b",
            metrics={},
        )
        assert rec.long_leg is None

    def test_invalid_status_rejected(self):
        with pytest.raises(ValueError, match="status"):
            FactorRecord(
                id="001", name="x", expression="X", category="c", batch="b",
                status="invalid",
            )

    def test_active_status_accepted(self):
        rec = FactorRecord(
            id="001", name="x", expression="X", category="c", batch="b",
            status="active", evaluation_version="v2",
        )
        assert rec.status == "active"

    def test_retired_status_accepted(self):
        rec = FactorRecord(
            id="001", name="x", expression="X", category="c", batch="b",
            status="retired",
        )
        assert rec.status == "retired"

    def test_invalid_source_rejected(self):
        with pytest.raises(ValueError, match="source"):
            FactorRecord(
                id="001", name="x", expression="X", category="c", batch="b",
                source="javascript",
            )

    def test_to_detail_dict(self):
        rec = FactorRecord.for_new_admission(
            id="001", name="test", expression="Std($close, 20)",
            category="vol", batch="b1",
            admitted_at="2026-04-04",
            metrics={"ic_mean": -0.05, "ic_ir": -0.3},
        )
        d = rec.to_detail_dict()
        assert d["id"] == "001"
        assert d["status"] == "active"
        assert d["evaluation_version"] == "v2"
        assert d["long_leg"] == "low"
        assert d["metrics"]["ic_mean"] == -0.05
        # Optional fields not present when None
        assert "logic_id" not in d
        assert "lineage" not in d

    def test_to_detail_dict_includes_optional_fields(self):
        rec = FactorRecord.for_new_admission(
            id="001", name="test", expression="X",
            category="c", batch="b",
            logic_id="L001",
            lineage={"parent": "009"},
            metrics={"ic_mean": -0.02},
        )
        d = rec.to_detail_dict()
        assert d["logic_id"] == "L001"
        assert d["lineage"] == {"parent": "009"}

    def test_to_index_dict(self):
        rec = FactorRecord.for_new_admission(
            id="001", name="test", expression="Std($close, 20)",
            category="vol", batch="b1",
            metrics={"ic_mean": -0.05},
        )
        idx = rec.to_index_dict()
        assert idx["id"] == "001"
        assert idx["status"] == "active"
        assert idx["evaluation_version"] == "v2"
        assert idx["long_leg"] == "low"
        assert idx["ic_mean"] == -0.05
        # Index should NOT have batch, admitted_at, metrics dict
        assert "batch" not in idx
        assert "admitted_at" not in idx
        assert "metrics" not in idx


class TestNormalizeMetrics:
    def test_ic_mean_is_aliased(self):
        raw = {"ic_mean_is": -0.05, "ic_ir_is": -0.4}
        norm = normalize_metrics(raw)
        assert norm["ic_mean"] == -0.05
        assert norm["ic_ir"] == -0.4
        assert "ic_mean_is" not in norm

    def test_max_lib_corr_aliased(self):
        raw = {"max_lib_corr": 0.5, "max_corr_factor": "009"}
        norm = normalize_metrics(raw)
        assert norm["max_corr"] == 0.5
        assert "max_lib_corr" not in norm
        assert norm["max_corr_factor"] == "009"  # passthrough

    def test_both_present_prefers_canonical(self):
        raw = {"ic_mean": -0.05, "ic_mean_is": -0.03}
        norm = normalize_metrics(raw)
        assert norm["ic_mean"] == -0.05

    def test_monotonicity_renamed(self):
        raw = {"monotonicity": -0.9}
        norm = normalize_metrics(raw)
        assert norm["monotonicity_is"] == -0.9
        assert "monotonicity" not in norm

    def test_passthrough_unknown_keys(self):
        raw = {"ic_mean_oos": -0.04, "custom_metric": 42}
        norm = normalize_metrics(raw)
        assert norm["ic_mean_oos"] == -0.04
        assert norm["custom_metric"] == 42

    def test_empty_dict(self):
        assert normalize_metrics({}) == {}

    def test_all_aliases_at_once(self):
        raw = {
            "ic_mean_is": -0.05,
            "ic_ir_is": -0.3,
            "max_lib_corr": 0.5,
            "monotonicity": -0.9,
            "ic_mean_oos": -0.04,
        }
        norm = normalize_metrics(raw)
        assert norm == {
            "ic_mean": -0.05,
            "ic_ir": -0.3,
            "max_corr": 0.5,
            "monotonicity_is": -0.9,
            "ic_mean_oos": -0.04,
        }
