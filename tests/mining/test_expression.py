"""Tests for ExpressionValidator."""

import pytest
from mining.expression import ExpressionValidator, ValidationResult


@pytest.fixture
def validator():
    return ExpressionValidator()


class TestValidationResult:
    def test_valid_result(self):
        r = ValidationResult(valid=True, errors=[], warnings=[])
        assert r.valid
        assert r.errors == []

    def test_invalid_result(self):
        r = ValidationResult(valid=False, errors=["bad syntax"], warnings=[])
        assert not r.valid
        assert "bad syntax" in r.errors


class TestFieldCheck:
    def test_valid_fields(self, validator):
        result = validator.validate("Rank(Div(Sub($close, $vwap), $vwap))")
        assert result.valid

    def test_unknown_field(self, validator):
        result = validator.validate("Rank($nonexistent_field)")
        assert not result.valid
        assert any("nonexistent_field" in e for e in result.errors)

    def test_dollar_sign_required(self, validator):
        result = validator.validate("Rank($close)")
        assert result.valid


class TestDepthCheck:
    def test_within_depth_limit(self, validator):
        result = validator.validate("Rank(Div(Sub($close, $vwap), $vwap))")
        assert result.valid

    def test_exceeds_depth_limit(self, validator):
        expr = "$close"
        for _ in range(12):
            expr = f"Rank({expr})"
        result = validator.validate(expr, max_depth=10)
        assert not result.valid
        assert any("depth" in e.lower() for e in result.errors)


class TestSyntaxCheck:
    def test_balanced_parens(self, validator):
        result = validator.validate("Rank(Div($close, $vwap))")
        assert result.valid

    def test_unbalanced_parens(self, validator):
        result = validator.validate("Rank(Div($close, $vwap)")
        assert not result.valid
        assert any("paren" in e.lower() for e in result.errors)

    def test_empty_expression(self, validator):
        result = validator.validate("")
        assert not result.valid

    def test_bare_field(self, validator):
        result = validator.validate("$close")
        assert result.valid


class TestSafeWrap:
    def test_wraps_div(self, validator):
        wrapped = validator.safe_wrap("Div($close, $volume)")
        assert "If(Greater(Abs($volume)" in wrapped

    def test_wraps_nested_div(self, validator):
        """safe_wrap should handle deeply nested expressions inside Div."""
        expr = "Div(Rank(Mean($close, 5)), Std($volume, 10))"
        wrapped = validator.safe_wrap(expr)
        assert "If(Greater(Abs(Std($volume, 10))" in wrapped
        assert "Rank(Mean($close, 5))" in wrapped

    def test_wraps_double_nested_div(self, validator):
        """safe_wrap should handle Div inside Div."""
        expr = "Div(Div($close, $open), $volume)"
        wrapped = validator.safe_wrap(expr)
        # Both Divs should be wrapped
        assert wrapped.count("If(Greater(Abs(") == 2
