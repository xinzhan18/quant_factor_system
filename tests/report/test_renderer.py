"""Tests for ReportRenderer."""
import os

import pytest

from report.renderer import ReportRenderer


@pytest.fixture
def minimal_report_data():
    return {
        "factor": {
            "id": "001", "name": "test_factor", "expression": "Std($close, 20)",
            "category": "volatility", "batch": "batch_001", "admitted_at": "2026-03-23",
        },
        "preprocessing": {
            "filter_suspend": True, "filter_limit": True, "winsorize_method": "mad",
            "winsorize_n": 5.0, "standardize_method": "zscore", "neutralize_mode": "none",
        },
        "kpi": {
            "ic_mean_is": -0.058, "ic_mean_oos": -0.057, "ic_ir": -0.304,
            "ic_win_rate": 0.375, "monotonicity": -0.9, "ls_return": -0.22,
            "composite_grade": "C+",
        },
        "distribution": {"stats_is": {"mean": 0.03, "std": 0.02, "skewness": 2.0, "kurtosis": 8.0, "coverage": 0.96, "nan_ratio": 0.04}, "stats_oos": None, "charts": {}},
        "ic_analysis": {"summary": {"is": {"ic_mean": -0.058, "ic_std": 0.19, "ic_ir": -0.304, "win_rate": 0.375, "ic_significant_rate": 0.62, "n_days": 1200}, "oos": {"ic_mean": -0.057, "ic_std": 0.185, "ic_ir": -0.308, "win_rate": 0.382, "ic_significant_rate": 0.64, "n_days": 60}}, "annual": [], "monthly_heatmap_data": [], "charts": {}},
        "quintile": {"stats": [], "ls_stats": {}, "charts": {}},
        "decay": {"ic_by_period": [], "autocorrelation": [], "half_life_days": None, "charts": {}},
        "scores": {"dimensions": [{"name": "Predictive Power", "score": 45, "grade": "C"}], "composite": {"score": 45, "grade": "C"}, "charts": {}},
    }


@pytest.fixture
def minimal_narrative():
    return {
        "factor_metadata": {"name_cn": "测试因子", "expression_latex": "\\sigma_{20}"},
        "construction_logic": {"formula_decomposition": "公式分解...", "parameter_rationale": "参数选择...", "preprocessing_notes": "预处理..."},
        "economic_interpretation": {"theoretical_foundations": "理论基础...", "attribution_angles": [{"title": "角度1", "icon": "X", "body": "内容..."}], "china_context": "A股特殊性..."},
        "section_interpretations": {"distribution": "分布解读...", "ic_annual": "年度IC...", "ic_monthly": "月度IC...", "quintile": "分层解读...", "decay": "衰减解读...", "composite": "综合评分..."},
        "critical_review": {"one_liner": "一句话总结", "body": "详细批评...", "key_weaknesses": [{"title": "弱点1", "detail": "描述..."}], "improvement_directions": ["建议1"]},
    }


class TestReportRenderer:
    def test_render_produces_html(self, minimal_report_data, minimal_narrative):
        renderer = ReportRenderer()
        html = renderer.render(minimal_report_data, minimal_narrative)
        assert "<!DOCTYPE html>" in html
        assert "test_factor" in html

    def test_render_contains_kpi(self, minimal_report_data, minimal_narrative):
        renderer = ReportRenderer()
        html = renderer.render(minimal_report_data, minimal_narrative)
        assert "-0.058" in html
        assert "C+" in html

    def test_render_contains_narrative(self, minimal_report_data, minimal_narrative):
        renderer = ReportRenderer()
        html = renderer.render(minimal_report_data, minimal_narrative)
        assert "公式分解" in html
        assert "一句话总结" in html

    def test_save_to_file(self, minimal_report_data, minimal_narrative, tmp_path):
        renderer = ReportRenderer()
        path = renderer.render_to_file(minimal_report_data, minimal_narrative, str(tmp_path), "001")
        assert os.path.exists(path)
        assert path.endswith(".html")
        content = open(path, encoding="utf-8").read()
        assert "<!DOCTYPE html>" in content

    def test_render_with_missing_narrative_keys(self, minimal_report_data):
        renderer = ReportRenderer()
        partial_narrative = {
            "factor_metadata": {"name_cn": "测试", "expression_latex": "x"},
        }
        html = renderer.render(minimal_report_data, partial_narrative)
        assert "<!DOCTYPE html>" in html
