"""Tests for report analytics v2 — pure extractors consuming result.yaml (schema v3)."""

from __future__ import annotations

from typing import Any

import pytest

from report.analytics_v2 import (
    build_summary,
    extract_ic_section,
    extract_profit_section,
    extract_risk_section,
)


def _candidate() -> dict[str, Any]:
    return {
        "candidate_id": "C001",
        "expression": "Std($close, 20)",
        "source_type": "dsl",
        "ic": {
            "train": {"ic_mean": 0.018, "ic_ir": 0.30, "n_days": 1500},
            "validation": {"ic_mean": 0.016, "ic_ir": 0.338, "n_days": 480},
        },
        "quintile": {
            "train": {"monotonicity": 0.95, "ls_mean": 0.007},
            "validation": {
                "q1": -0.003,
                "q2": 0.0,
                "q3": 0.001,
                "q4": 0.002,
                "q5": 0.005,
                "monotonicity": 0.95,
                "ls_mean": 0.007,
                "n_days": 480,
            },
            "ls_stats": {
                "train": {"mean": 0.007, "sharpe": 1.6, "tstat": 3.9},
                "validation": {"mean": 0.007, "sharpe": 1.3, "tstat": 3.5},
            },
        },
        "barra": {
            "style_exposures": {"vol_20d": 0.15},
            "style_r_squared": 0.08,
            "barra_residual_ic": 0.013,
            "barra_residual_icir": 0.251,
            "alpha_survival_ratio": 0.81,
            "dominant_style_exposure": "vol_20d",
            "style_crowding_risk": "low",
        },
        "uniqueness": {"max_lib_corr": 0.30, "nearest_factor_id": "F012"},
    }


class TestExtractIcSection:
    def test_contains_train_and_validation(self) -> None:
        section = extract_ic_section(_candidate())
        assert section["train"]["ic_mean"] == 0.018
        assert section["validation"]["ic_ir"] == 0.338

    def test_empty_candidate_returns_empty_dicts(self) -> None:
        section = extract_ic_section({})
        assert section == {"train": {}, "validation": {}}


class TestExtractProfitSection:
    def test_has_quintile_fields(self) -> None:
        section = extract_profit_section(_candidate())
        assert section["quintile_returns"]["q5"] == 0.005
        assert section["monotonicity"] == 0.95
        assert section["long_short_mean"] == 0.007
        assert section["long_short_n_days"] == 480
        assert section["long_short_sharpe"] == 1.3
        assert section["long_short_tstat"] == 3.5


class TestExtractRiskSection:
    def test_has_barra_fields(self) -> None:
        section = extract_risk_section(_candidate())
        assert section["style_r_squared"] == 0.08
        assert section["alpha_survival_ratio"] == 0.81
        assert section["style_crowding_risk"] == "low"

    def test_empty_candidate_returns_sentinel(self) -> None:
        section = extract_risk_section({})
        assert section["style_exposures"] == {}
        assert section["style_r_squared"] is None


class TestBuildSummary:
    def test_top_fields_populated(self) -> None:
        s = build_summary(_candidate(), "F020")
        assert s["factor_id"] == "F020"
        assert s["ic_mean"] == 0.016
        assert s["ic_ir"] == 0.338
        assert s["monotonicity"] == 0.95
        assert s["alpha_survival"] == 0.81
        assert s["max_lib_corr"] == 0.30
        assert s["nearest_factor"] == "F012"
