"""Tests for research.domain.reason_codes."""

import pytest

from research.domain.reason_codes import ReasonCode, Severity, SEVERITY_COLOURS


class TestSeverity:
    def test_values(self):
        assert Severity.FATAL.value == "fatal"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.INFO.value == "info"


class TestReasonCode:
    def test_severity_attribute(self):
        assert ReasonCode.STRENGTH_IC_TOO_LOW.severity is Severity.FATAL
        assert ReasonCode.STRENGTH_SHARPE_LOW.severity is Severity.MEDIUM
        assert ReasonCode.INFO_NEAR_MISS.severity is Severity.INFO

    def test_code_str_attribute(self):
        assert ReasonCode.STRENGTH_IC_TOO_LOW.code_str == "strength_ic_too_low"
        assert ReasonCode.POLICY_FORBIDDEN_PATTERN.code_str == "policy_forbidden_pattern"

    def test_is_fatal(self):
        assert ReasonCode.STRENGTH_IC_TOO_LOW.is_fatal is True
        assert ReasonCode.REDUNDANCY_HIGH_CORRELATION.is_fatal is True
        assert ReasonCode.STRENGTH_SHARPE_LOW.is_fatal is False
        assert ReasonCode.INFO_NEAR_MISS.is_fatal is False

    def test_fatal_codes_returns_only_fatal(self):
        fatals = ReasonCode.fatal_codes()
        assert len(fatals) > 0
        for rc in fatals:
            assert rc.severity is Severity.FATAL

    def test_fatal_codes_includes_expected(self):
        fatals = ReasonCode.fatal_codes()
        fatal_names = {rc.name for rc in fatals}
        assert "STRENGTH_IC_TOO_LOW" in fatal_names
        assert "REDUNDANCY_HIGH_CORRELATION" in fatal_names
        assert "FEASIBILITY_COVERAGE_LOW" in fatal_names
        assert "POLICY_FORBIDDEN_PATTERN" in fatal_names

    def test_all_codes_have_valid_severity(self):
        for rc in ReasonCode:
            assert isinstance(rc.severity, Severity)
            assert rc.code_str  # non-empty string

    def test_categories_present(self):
        """Verify all expected categories have at least one code."""
        categories = {"STRENGTH", "STABILITY", "REDUNDANCY", "FEASIBILITY", "MECHANISM", "POLICY", "INFO"}
        found = set()
        for rc in ReasonCode:
            prefix = rc.name.split("_")[0]
            found.add(prefix)
        assert categories.issubset(found)


class TestSeverityColours:
    def test_all_severities_have_colour(self):
        for sev in Severity:
            assert sev in SEVERITY_COLOURS
            assert isinstance(SEVERITY_COLOURS[sev], str)
