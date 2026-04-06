"""Tests for research.execute.precheck — DSL and Python prechecks."""

import pytest

from research.execute.precheck import (
    DSLPrecheck,
    PythonPrecheck,
    PrecheckResult,
    run_precheck,
)


# ===================================================================
# DSLPrecheck
# ===================================================================
class TestDSLPrecheck:
    def setup_method(self):
        self.checker = DSLPrecheck()

    # --- passing cases ---

    def test_valid_simple_expression(self):
        result = self.checker.check("Rank($close)")
        assert result.passed
        assert result.status == "passed"
        assert result.reason_codes == []

    def test_valid_complex_expression(self):
        result = self.checker.check("Div(Std($close, 20), Mean($volume, 20))")
        assert result.passed

    def test_valid_nested_expression(self):
        result = self.checker.check("Rank(Div(Std($close, 20), Mean($volume, 20)))")
        assert result.passed

    # --- failing cases ---

    def test_empty_expression(self):
        result = self.checker.check("")
        assert not result.passed
        assert "empty_expression" in result.reason_codes

    def test_whitespace_only(self):
        result = self.checker.check("   ")
        assert not result.passed
        assert "empty_expression" in result.reason_codes

    def test_unbalanced_parens_missing_close(self):
        result = self.checker.check("Rank($close")
        assert not result.passed
        assert "unbalanced_parentheses" in result.reason_codes

    def test_unbalanced_parens_extra_close(self):
        result = self.checker.check("Rank($close))")
        assert not result.passed
        assert "unbalanced_parentheses" in result.reason_codes

    def test_unavailable_operator(self):
        result = self.checker.check("Neg($close)")
        assert not result.passed
        codes = result.reason_codes
        assert any("unavailable_operator:Neg" in c for c in codes)

    def test_unknown_operator(self):
        result = self.checker.check("FooBar($close)")
        assert not result.passed
        assert any("unknown_operator:FooBar" in c for c in result.reason_codes)

    def test_unknown_operator_codes(self):
        result = self.checker.check("FooBar($close)")
        codes = result.reason_codes
        assert any("unknown_operator:FooBar" in c for c in codes)

    def test_forbidden_field_vwap(self):
        result = self.checker.check("Rank($vwap)")
        assert not result.passed
        assert any("forbidden_field:$vwap" in c for c in result.reason_codes)
        # Also hits forbidden_pattern
        assert any("forbidden_pattern" in c for c in result.reason_codes)

    def test_unknown_field(self):
        result = self.checker.check("Rank($nonexistent_field)")
        assert not result.passed
        assert any("unknown_field" in c for c in result.reason_codes)

    def test_expression_too_deep(self):
        # Build an expression with depth > 10
        expr = "$close"
        for _ in range(12):
            expr = f"Rank({expr})"
        result = self.checker.check(expr)
        assert not result.passed
        assert any("expression_too_deep" in c for c in result.reason_codes)

    def test_constant_expression(self):
        result = self.checker.check("Add(1, 2)")
        assert not result.passed
        assert "constant_expression" in result.reason_codes

    def test_forbidden_pattern_vwap(self):
        result = self.checker.check("Mean($vwap, 10)")
        assert not result.passed
        assert any("forbidden_pattern" in c for c in result.reason_codes)

    def test_custom_max_depth(self):
        checker = DSLPrecheck(max_depth=3)
        # depth 4 should fail
        result = checker.check("Rank(Rank(Rank(Rank($close))))")
        assert not result.passed
        assert any("expression_too_deep" in c for c in result.reason_codes)

    def test_multiple_errors_collected(self):
        # Unavailable operator + forbidden field
        result = self.checker.check("Neg($vwap)")
        assert not result.passed
        assert len(result.reason_codes) >= 2

    def test_to_dict(self):
        result = self.checker.check("Rank($close)")
        d = result.to_dict()
        assert d["status"] == "passed"
        assert isinstance(d["reason_codes"], list)


# ===================================================================
# PythonPrecheck
# ===================================================================
class TestPythonPrecheck:
    def setup_method(self):
        self.checker = PythonPrecheck()

    def test_valid_file(self, tmp_path):
        f = tmp_path / "factor.py"
        f.write_text("def compute(df, params): return df['close']")
        result = self.checker.check(str(f))
        assert result.passed

    def test_empty_path(self):
        result = self.checker.check("")
        assert not result.passed
        assert "empty_module_path" in result.reason_codes

    def test_missing_file(self):
        result = self.checker.check("/nonexistent/factor.py")
        assert not result.passed
        assert any("module_not_found" in c for c in result.reason_codes)


# ===================================================================
# run_precheck dispatcher
# ===================================================================
class TestRunPrecheck:
    def test_dsl_dispatch(self):
        candidate = {"source_type": "dsl", "expression": "Rank($close)"}
        result = run_precheck(candidate)
        assert result.passed

    def test_python_dispatch(self, tmp_path):
        f = tmp_path / "factor.py"
        f.write_text("def compute(df, params): return df['close']")
        candidate = {"source_type": "python", "module_path": str(f)}
        result = run_precheck(candidate)
        assert result.passed

    def test_default_source_type_is_dsl(self):
        candidate = {"expression": "Rank($close)"}
        result = run_precheck(candidate)
        assert result.passed

    def test_unknown_source_type(self):
        candidate = {"source_type": "rust", "code": "fn main() {}"}
        result = run_precheck(candidate)
        assert not result.passed
        assert any("unknown_source_type" in c for c in result.reason_codes)

    def test_dsl_fails_on_bad_expression(self):
        candidate = {"source_type": "dsl", "expression": "Neg($vwap)"}
        result = run_precheck(candidate)
        assert not result.passed
