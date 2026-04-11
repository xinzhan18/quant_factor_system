"""Tests for CP01 Hard Gates — the Python-only rejection layer."""

from __future__ import annotations

from typing import Any

import pytest

from research.checkpoints.hard_gates import (
    DEFAULT_MIN_COVERAGE,
    HardGateResult,
    evaluate_hard_gates,
)


def _base_result(
    candidates: list[dict[str, Any]],
    sample_policy_version: str = "v3",
) -> dict[str, Any]:
    return {
        "sample_policy_version": sample_policy_version,
        "candidates": candidates,
    }


def _good_candidate(**overrides: Any) -> dict[str, Any]:
    base: dict[str, Any] = {
        "candidate_id": "C001",
        "expression": "Std($close, 20)",
        "source_type": "dsl",
        "coverage": 0.95,
        "compute_error": None,
        "effect_strength": {
            "train": {"ic_mean": 0.015},
            "validation": {"ic_mean": 0.013},
        },
    }
    base.update(overrides)
    return base


class TestAllPass:
    def test_clean_candidate_passes(self) -> None:
        result = _base_result([_good_candidate()])
        gates = evaluate_hard_gates(result, current_sample_policy_version="v3")
        assert len(gates) == 1
        assert gates[0].passed is True
        assert gates[0].reasons == []
        assert gates[0].candidate_id == "C001"

    def test_returns_one_result_per_candidate(self) -> None:
        result = _base_result(
            [
                _good_candidate(candidate_id="C001"),
                _good_candidate(candidate_id="C002"),
                _good_candidate(candidate_id="C003"),
            ]
        )
        gates = evaluate_hard_gates(result, current_sample_policy_version="v3")
        assert [g.candidate_id for g in gates] == ["C001", "C002", "C003"]
        assert all(g.passed for g in gates)


class TestComputeError:
    def test_compute_error_rejected(self) -> None:
        c = _good_candidate(compute_error="ValueError: NaN overflow")
        result = _base_result([c])
        gates = evaluate_hard_gates(result, "v3")
        assert gates[0].passed is False
        assert any("compute_error" in r for r in gates[0].reasons)


class TestCoverage:
    def test_low_coverage_rejected(self) -> None:
        c = _good_candidate(coverage=0.5)
        result = _base_result([c])
        gates = evaluate_hard_gates(result, "v3")
        assert gates[0].passed is False
        assert any("coverage" in r for r in gates[0].reasons)

    def test_missing_coverage_rejected(self) -> None:
        c = _good_candidate(coverage=None)
        result = _base_result([c])
        gates = evaluate_hard_gates(result, "v3")
        assert gates[0].passed is False
        assert any("coverage" in r for r in gates[0].reasons)

    def test_custom_threshold(self) -> None:
        c = _good_candidate(coverage=0.85)
        result = _base_result([c])
        # default threshold 0.80 → passes
        gates_default = evaluate_hard_gates(result, "v3")
        assert gates_default[0].passed is True
        # stricter threshold 0.90 → fails
        gates_strict = evaluate_hard_gates(result, "v3", min_coverage=0.90)
        assert gates_strict[0].passed is False


class TestSignFlip:
    def test_opposite_signs_rejected(self) -> None:
        c = _good_candidate(
            effect_strength={
                "train": {"ic_mean": 0.02},
                "validation": {"ic_mean": -0.015},
            }
        )
        result = _base_result([c])
        gates = evaluate_hard_gates(result, "v3")
        assert gates[0].passed is False
        assert any("sign_flip" in r for r in gates[0].reasons)

    def test_zero_train_ic_rejected(self) -> None:
        c = _good_candidate(
            effect_strength={
                "train": {"ic_mean": 1e-8},
                "validation": {"ic_mean": 0.02},
            }
        )
        result = _base_result([c])
        gates = evaluate_hard_gates(result, "v3")
        assert gates[0].passed is False
        assert any("train ic_mean ~0" in r for r in gates[0].reasons)

    def test_zero_val_ic_rejected(self) -> None:
        c = _good_candidate(
            effect_strength={
                "train": {"ic_mean": 0.02},
                "validation": {"ic_mean": 1e-8},
            }
        )
        result = _base_result([c])
        gates = evaluate_hard_gates(result, "v3")
        assert gates[0].passed is False
        assert any("validation ic_mean ~0" in r for r in gates[0].reasons)

    def test_both_negative_passes(self) -> None:
        """Same-sign (both negative) must pass — alpha is still real."""
        c = _good_candidate(
            effect_strength={
                "train": {"ic_mean": -0.015},
                "validation": {"ic_mean": -0.013},
            }
        )
        result = _base_result([c])
        gates = evaluate_hard_gates(result, "v3")
        assert gates[0].passed is True


class TestForbiddenFieldsAndOperators:
    def test_forbidden_vwap_field(self) -> None:
        c = _good_candidate(expression="Mul($vwap, $volume)")
        result = _base_result([c])
        gates = evaluate_hard_gates(result, "v3")
        assert gates[0].passed is False
        assert any("forbidden_field" in r for r in gates[0].reasons)

    def test_forbidden_neg_operator(self) -> None:
        c = _good_candidate(expression="Neg($close)")
        result = _base_result([c])
        gates = evaluate_hard_gates(result, "v3")
        assert gates[0].passed is False
        assert any("forbidden_operator" in r for r in gates[0].reasons)

    def test_sma_operator_rejected(self) -> None:
        c = _good_candidate(expression="SMA($close, 20)")
        result = _base_result([c])
        gates = evaluate_hard_gates(result, "v3")
        assert gates[0].passed is False
        assert any("SMA" in r for r in gates[0].reasons)


class TestSamplePolicy:
    def test_version_mismatch_rejects_all_candidates(self) -> None:
        result = _base_result(
            [_good_candidate(), _good_candidate(candidate_id="C002")],
            sample_policy_version="v2",
        )
        gates = evaluate_hard_gates(result, current_sample_policy_version="v3")
        assert all(not g.passed for g in gates)
        assert all(
            any("sample_policy_violation" in r for r in g.reasons)
            for g in gates
        )

    def test_missing_version_rejected(self) -> None:
        result = {
            "candidates": [_good_candidate()],
        }  # no sample_policy_version
        gates = evaluate_hard_gates(result, "v3")
        assert gates[0].passed is False


class TestMultipleFailuresReported:
    """All matching reasons must be reported — not short-circuited."""

    def test_coverage_and_sign_flip_both_reported(self) -> None:
        c = _good_candidate(
            coverage=0.5,
            effect_strength={
                "train": {"ic_mean": 0.02},
                "validation": {"ic_mean": -0.015},
            },
        )
        result = _base_result([c])
        gates = evaluate_hard_gates(result, "v3")
        assert gates[0].passed is False
        assert len(gates[0].reasons) == 2
        assert any("coverage" in r for r in gates[0].reasons)
        assert any("sign_flip" in r for r in gates[0].reasons)
