"""Tests for research.domain.schema."""

from datetime import datetime

import pytest

from research.domain.schema import (
    CandidateRecord,
    Decision,
    EvaluationContext,
    FactorRecord,
    FactorStatus,
    Lineage,
    MutationType,
    RouteRecord,
    RouteStatus,
    RouteType,
    SourceType,
)


class TestEnums:
    """Verify enum values match the design spec."""

    def test_source_type_values(self):
        assert SourceType.DSL.value == "dsl"
        assert SourceType.PYTHON.value == "python"

    def test_factor_status_values(self):
        assert FactorStatus.ACTIVE.value == "active"
        assert FactorStatus.LEGACY.value == "legacy"
        assert FactorStatus.RETIRED.value == "retired"

    def test_route_type_values(self):
        expected = {"genesis", "mutate", "crossover", "repair", "decorrelate"}
        actual = {rt.value for rt in RouteType}
        assert actual == expected

    def test_route_status_values(self):
        expected = {"planned", "probing", "active", "completed", "failed", "reserved"}
        actual = {rs.value for rs in RouteStatus}
        assert actual == expected

    def test_decision_values(self):
        assert Decision.ADMIT.value == "admit"
        assert Decision.REPLACE.value == "replace"

    def test_mutation_type_has_genesis(self):
        assert MutationType.GENESIS.value == "genesis"
        assert len(MutationType) >= 5  # at least 5 mutation types


class TestLineage:
    def test_default_lineage(self):
        lin = Lineage()
        assert lin.parent_logic == ""
        assert lin.mutation_type == "genesis"
        assert lin.parent_factors == []

    def test_custom_lineage(self):
        lin = Lineage(
            parent_logic="L021",
            parent_routes=["R021_01"],
            parent_factors=["F013"],
            mutation_type="mutate",
        )
        assert lin.parent_logic == "L021"
        assert "R021_01" in lin.parent_routes


class TestFactorRecord:
    def test_default_construction(self):
        rec = FactorRecord()
        assert rec.factor_id == ""
        assert rec.status == "active"
        assert rec.evaluation_version == "v3"
        assert rec.metrics_snapshot == {}
        assert isinstance(rec.lineage, Lineage)

    def test_factor_record_is_mutable(self):
        rec = FactorRecord(factor_id="F001")
        rec.status = "retired"
        assert rec.status == "retired"

    def test_evaluation_context_defaults(self):
        ctx = EvaluationContext()
        assert ctx.sample_policy_version == ""
        assert ctx.holdout_used is False


class TestCandidateRecord:
    def test_default_construction(self):
        rec = CandidateRecord()
        assert rec.candidate_id == ""
        assert rec.source_type == "dsl"
        assert rec.metrics == {}
        assert isinstance(rec.lineage, Lineage)

    def test_dsl_candidate(self):
        rec = CandidateRecord(
            candidate_id="C042_03",
            logic_id="L021",
            route_id="R021_01",
            family_id="FM_breakout",
            route_type="genesis",
            source_type="dsl",
            name="compression_rank_breakout_10",
            expression="Rank(Std($close, 10))",
            rationale="test breakout under compression",
        )
        assert rec.candidate_id == "C042_03"
        assert rec.expression is not None
        assert rec.code is None

    def test_python_candidate(self):
        rec = CandidateRecord(
            candidate_id="C042_07",
            source_type="python",
            code="def compute_factor(df, params, ops): ...",
            params={"vol_window": 20},
            param_space={"vol_window": [10, 20, 40]},
        )
        assert rec.source_type == "python"
        assert rec.code is not None
        assert rec.expression is None


class TestRouteRecord:
    def test_default_construction(self):
        rec = RouteRecord()
        assert rec.route_id == ""
        assert rec.status == "planned"
        assert rec.priority == "medium"
        assert rec.dsl_naturalness == "high"
        assert rec.eval_attempts == 0

    def test_full_route(self):
        rec = RouteRecord(
            route_id="R021_01",
            logic_id="L021",
            family_id="FM_breakout",
            route_type="genesis",
            status="active",
            research_question="Does compression improve breakout independence?",
            candidate_target_count=3,
            allowed_variations=["window_variation", "rank_transform"],
        )
        assert rec.route_id == "R021_01"
        assert len(rec.allowed_variations) == 2
        assert rec.forbidden_variations == []
