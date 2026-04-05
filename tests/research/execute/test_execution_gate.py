"""Tests for research.execute.execution_gate — pass/warn/fail classification."""

import pytest

from research.execute.execution_gate import ExecutionGate, GateResult


def _base_result(**overrides):
    """Build a minimal passing result dict with optional overrides."""
    result = {
        "precheck": {"status": "passed", "reason_codes": []},
        "diagnostics": {
            "base_valid_ratio": 0.90,
            "base_variance": 1.0,
            "base_outlier_ratio": 0.05,
        },
        "evaluation": {
            "sign_consistency": True,
            "train_validation_decay_ratio": 0.60,
            "split_stability": "medium",
        },
        "feasibility": {
            "turnover": 0.30,
            "liquidity_coverage_ratio": 0.80,
            "tail_trade_concentration": 0.15,
        },
    }
    # Allow deep overrides
    for key, val in overrides.items():
        parts = key.split(".")
        target = result
        for part in parts[:-1]:
            target = target.setdefault(part, {})
        target[parts[-1]] = val
    return result


class TestExecutionGate:
    def setup_method(self):
        self.gate = ExecutionGate()

    # --- pass ---

    def test_clean_candidate_passes(self):
        result = _base_result()
        gate = self.gate.evaluate(result)
        assert gate.status == "pass"
        assert gate.reason_codes == []

    # --- fail_technical: precheck failed ---

    def test_precheck_failed(self):
        result = _base_result()
        result["precheck"] = {"status": "failed", "reason_codes": ["empty_expression"]}
        gate = self.gate.evaluate(result)
        assert gate.status == "fail_technical"
        assert "precheck_failed" in gate.reason_codes

    # --- fail_technical: computation ---

    def test_valid_ratio_too_low(self):
        result = _base_result(**{"diagnostics.base_valid_ratio": 0.05})
        gate = self.gate.evaluate(result)
        assert gate.status == "fail_technical"
        assert "valid_ratio_too_low" in gate.reason_codes

    def test_near_constant_signal(self):
        result = _base_result(**{"diagnostics.base_variance": 1e-10})
        gate = self.gate.evaluate(result)
        assert gate.status == "fail_technical"
        assert "near_constant_signal" in gate.reason_codes

    # --- fail_technical: stability ---

    def test_train_validation_sign_flip(self):
        result = _base_result(**{"evaluation.train_validation_decay_ratio": -0.5})
        gate = self.gate.evaluate(result)
        assert gate.status == "fail_technical"
        assert "train_validation_sign_flip" in gate.reason_codes

    # --- fail_technical: feasibility ---

    def test_extreme_turnover(self):
        result = _base_result(**{"feasibility.turnover": 5.0})
        gate = self.gate.evaluate(result)
        assert gate.status == "fail_technical"
        assert "extreme_turnover" in gate.reason_codes

    def test_extreme_low_liquidity(self):
        result = _base_result(**{"feasibility.liquidity_coverage_ratio": 0.05})
        gate = self.gate.evaluate(result)
        assert gate.status == "fail_technical"
        assert "extreme_low_liquidity" in gate.reason_codes

    def test_extreme_tail_concentration(self):
        result = _base_result(**{"feasibility.tail_trade_concentration": 0.90})
        gate = self.gate.evaluate(result)
        assert gate.status == "fail_technical"
        assert "extreme_tail_concentration" in gate.reason_codes

    # --- warn ---

    def test_low_valid_ratio_warns(self):
        result = _base_result(**{"diagnostics.base_valid_ratio": 0.20})
        gate = self.gate.evaluate(result)
        assert gate.status == "warn"
        assert "valid_ratio_low" in gate.reason_codes

    def test_high_outlier_ratio_warns(self):
        result = _base_result(**{"diagnostics.base_outlier_ratio": 0.30})
        gate = self.gate.evaluate(result)
        assert gate.status == "warn"
        assert "high_outlier_ratio" in gate.reason_codes

    def test_sign_inconsistency_warns(self):
        result = _base_result(**{"evaluation.sign_consistency": False})
        gate = self.gate.evaluate(result)
        assert gate.status == "warn"
        assert "sign_inconsistency" in gate.reason_codes

    def test_poor_split_stability_warns(self):
        result = _base_result(**{"evaluation.split_stability": "low"})
        gate = self.gate.evaluate(result)
        assert gate.status == "warn"
        assert "poor_split_stability" in gate.reason_codes

    def test_high_turnover_warns(self):
        result = _base_result(**{"feasibility.turnover": 2.0})
        gate = self.gate.evaluate(result)
        assert gate.status == "warn"
        assert "high_turnover" in gate.reason_codes

    def test_low_liquidity_warns(self):
        result = _base_result(**{"feasibility.liquidity_coverage_ratio": 0.20})
        gate = self.gate.evaluate(result)
        assert gate.status == "warn"
        assert "low_liquidity_coverage" in gate.reason_codes

    # --- missing keys handled gracefully ---

    def test_missing_diagnostics(self):
        result = {"precheck": {"status": "passed"}, "evaluation": {}, "feasibility": {}}
        gate = self.gate.evaluate(result)
        assert gate.status == "pass"

    def test_missing_feasibility(self):
        result = _base_result()
        del result["feasibility"]
        gate = self.gate.evaluate(result)
        assert gate.status == "pass"

    # --- to_dict ---

    def test_to_dict_structure(self):
        gr = GateResult(status="warn", reason_codes=["high_turnover"])
        d = gr.to_dict()
        assert d == {"status": "warn", "reason_codes": ["high_turnover"]}

    # --- extreme_outlier_ratio triggers fail ---

    def test_extreme_outlier_fails(self):
        result = _base_result(**{"diagnostics.base_outlier_ratio": 0.60})
        gate = self.gate.evaluate(result)
        assert gate.status == "fail_technical"
        assert "extreme_outlier_ratio" in gate.reason_codes

    # --- multiple warnings accumulate ---

    def test_multiple_warnings(self):
        result = _base_result(
            **{
                "diagnostics.base_valid_ratio": 0.25,
                "feasibility.turnover": 1.8,
            }
        )
        gate = self.gate.evaluate(result)
        assert gate.status == "warn"
        assert "valid_ratio_low" in gate.reason_codes
        assert "high_turnover" in gate.reason_codes
