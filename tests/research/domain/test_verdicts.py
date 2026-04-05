"""Tests for research.domain.verdicts."""

import pytest

from research.domain.reason_codes import ReasonCode
from research.domain.verdicts import (
    BatchJudgeReport,
    CandidateVerdict,
    CandidateVerdictRecord,
    EffectBucket,
    FeasibilityBucket,
    LogicRecommendation,
    LogicRecommendationRecord,
    RedundancyBucket,
    RouteVerdict,
    RouteVerdictRecord,
    StabilityBucket,
)


class TestCandidateVerdict:
    def test_values(self):
        assert CandidateVerdict.ADMIT.value == "admit"
        assert CandidateVerdict.REPLACE.value == "replace"
        assert CandidateVerdict.REJECT.value == "reject"
        assert CandidateVerdict.DEFER.value == "defer"


class TestRouteVerdict:
    def test_values(self):
        assert RouteVerdict.PASS.value == "pass"
        assert RouteVerdict.BORDERLINE.value == "borderline"
        assert RouteVerdict.FAIL.value == "fail"


class TestLogicRecommendation:
    def test_values(self):
        expected = {"continue", "warm", "park", "saturate", "kill"}
        actual = {lr.value for lr in LogicRecommendation}
        assert actual == expected


class TestBucketEnums:
    def test_effect_bucket(self):
        assert EffectBucket.STRONG.value == "strong"
        assert len(EffectBucket) == 4

    def test_stability_bucket(self):
        assert StabilityBucket.ROBUST.value == "robust"
        assert len(StabilityBucket) == 4

    def test_redundancy_bucket(self):
        assert RedundancyBucket.NOVEL.value == "novel"
        assert len(RedundancyBucket) == 4

    def test_feasibility_bucket(self):
        assert FeasibilityBucket.GOOD.value == "good"
        assert len(FeasibilityBucket) == 4


class TestCandidateVerdictRecord:
    def test_default_construction(self):
        rec = CandidateVerdictRecord(
            candidate_id="C042_01",
            verdict=CandidateVerdict.ADMIT,
        )
        assert rec.candidate_id == "C042_01"
        assert rec.verdict is CandidateVerdict.ADMIT
        assert rec.reason_codes == []
        assert rec.has_fatal is False

    def test_has_fatal_with_fatal_code(self):
        rec = CandidateVerdictRecord(
            candidate_id="C042_02",
            verdict=CandidateVerdict.REJECT,
            reason_codes=[ReasonCode.STRENGTH_IC_TOO_LOW],
        )
        assert rec.has_fatal is True

    def test_has_fatal_without_fatal_code(self):
        rec = CandidateVerdictRecord(
            candidate_id="C042_03",
            verdict=CandidateVerdict.REJECT,
            reason_codes=[ReasonCode.STRENGTH_SHARPE_LOW],
        )
        assert rec.has_fatal is False

    def test_replace_target(self):
        rec = CandidateVerdictRecord(
            candidate_id="C042_04",
            verdict=CandidateVerdict.REPLACE,
            replace_target_id="F013",
        )
        assert rec.replace_target_id == "F013"

    def test_bucket_assignments(self):
        rec = CandidateVerdictRecord(
            candidate_id="C042_05",
            verdict=CandidateVerdict.ADMIT,
            effect_bucket=EffectBucket.STRONG,
            stability_bucket=StabilityBucket.ROBUST,
            redundancy_bucket=RedundancyBucket.NOVEL,
            feasibility_bucket=FeasibilityBucket.GOOD,
        )
        assert rec.effect_bucket is EffectBucket.STRONG
        assert rec.feasibility_bucket is FeasibilityBucket.GOOD


class TestRouteVerdictRecord:
    def test_default_construction(self):
        rec = RouteVerdictRecord(
            route_id="R021_01",
            logic_id="L021",
            verdict=RouteVerdict.PASS,
        )
        assert rec.verdict is RouteVerdict.PASS
        assert rec.probe_ic_mean is None

    def test_with_probe_metrics(self):
        rec = RouteVerdictRecord(
            route_id="R021_01",
            logic_id="L021",
            verdict=RouteVerdict.BORDERLINE,
            probe_ic_mean=0.012,
            probe_ic_seg_a=0.015,
            probe_ic_seg_b=0.008,
        )
        assert rec.probe_ic_mean == 0.012


class TestBatchJudgeReport:
    def test_empty_report(self):
        report = BatchJudgeReport(batch_id="batch_042")
        assert report.admitted == []
        assert report.rejected == []

    def test_admitted_includes_replace(self):
        report = BatchJudgeReport(
            batch_id="batch_042",
            candidate_verdicts=[
                CandidateVerdictRecord(
                    candidate_id="C042_01",
                    verdict=CandidateVerdict.ADMIT,
                ),
                CandidateVerdictRecord(
                    candidate_id="C042_02",
                    verdict=CandidateVerdict.REPLACE,
                ),
                CandidateVerdictRecord(
                    candidate_id="C042_03",
                    verdict=CandidateVerdict.REJECT,
                ),
            ],
        )
        assert len(report.admitted) == 2
        assert len(report.rejected) == 1
