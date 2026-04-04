"""Tests for check_lookahead_bias static analysis function."""

import pytest

from mining.domain.similarity import check_lookahead_bias


def test_no_lookahead_simple():
    """pct_change has no shift — should return False."""
    code = "df['close'].pct_change(5)"
    assert check_lookahead_bias(code) is False


def test_lookahead_negative_shift():
    """Negative shift looks ahead into the future — should return True."""
    code = "df['close'].shift(-5)"
    assert check_lookahead_bias(code) is True


def test_no_lookahead_positive_shift():
    """Positive shift looks backward (lagged) — should return False."""
    code = "df['close'].shift(5)"
    assert check_lookahead_bias(code) is False


def test_syntax_error_returns_false():
    """Unparseable code should return False gracefully, not raise."""
    code = "def broken(: pass"
    assert check_lookahead_bias(code) is False


def test_no_lookahead_ops_usage():
    """Qlib-style operator expression has no shift call — should return False."""
    code = "ops.std(df['close'], 20)"
    assert check_lookahead_bias(code) is False


def test_lookahead_negative_shift_unary():
    """Shift with unary minus expression: shift(-n) where n is a variable."""
    code = "df['close'].shift(-n)"
    assert check_lookahead_bias(code) is True


def test_no_lookahead_zero_shift():
    """Zero shift is a no-op and not a lookahead — should return False."""
    code = "df['close'].shift(0)"
    assert check_lookahead_bias(code) is False


def test_lookahead_negative_float_shift():
    """Negative float shift — should return True."""
    code = "df['close'].shift(-1.5)"
    assert check_lookahead_bias(code) is True


def test_no_lookahead_empty_code():
    """Empty string has no AST nodes — should return False."""
    assert check_lookahead_bias("") is False


def test_no_lookahead_shift_keyword_arg():
    """Shift called with a keyword arg (not positional) is not detected — returns False.

    This is a known limitation of the current implementation; keyword-based
    negative shifts are rare and can be added later.
    """
    code = "df['close'].shift(periods=5)"
    assert check_lookahead_bias(code) is False
