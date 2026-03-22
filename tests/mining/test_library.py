"""Tests for FactorLibrary."""

import yaml
import pytest
from pathlib import Path
from mining.library import FactorLibrary


@pytest.fixture
def library(tmp_mining_dir, config):
    lib_dir = Path(config.library_dir)
    (lib_dir / "library.yaml").write_text(yaml.dump({
        "thresholds": {"ic_min": 0.03, "correlation_max": 0.5, "replacement_ic_ratio": 1.3, "replacement_ic_min": 0.05},
        "factors": [],
    }))
    return FactorLibrary(config)


class TestAdmit:
    def test_admit_factor(self, library):
        factor_id = library.admit({
            "name": "VWAP_Dev", "expression": "Neg(Rank(Div(Sub($close, $vwap), $vwap)))",
            "category": "vwap", "batch": "batch_001",
            "metrics": {"ic_mean": 0.065, "ic_std": 0.078, "ic_ir": 0.82, "ic_win_rate": 0.68, "max_correlation": 0.31, "max_corr_factor": None},
        })
        assert factor_id == "001"
        index = library.list_factors()
        assert len(index) == 1
        assert index[0]["id"] == "001"

    def test_admit_increments_id(self, library):
        for i in range(3):
            library.admit({"name": f"Factor_{i}", "expression": "Rank($close)", "category": "momentum", "batch": "batch_001", "metrics": {"ic_mean": 0.05}})
        index = library.list_factors()
        assert len(index) == 3
        assert index[2]["id"] == "003"


class TestReplace:
    def test_replace_factor(self, library):
        library.admit({"name": "Old_Factor", "expression": "Rank($close)", "category": "momentum", "batch": "batch_001", "metrics": {"ic_mean": 0.04}})
        library.replace("001", {"name": "Better_Factor", "expression": "Rank(Div($close, $vwap))", "category": "momentum", "batch": "batch_002", "metrics": {"ic_mean": 0.07}})
        index = library.list_factors()
        assert len(index) == 1
        assert index[0]["name"] == "Better_Factor"
        assert index[0]["id"] == "001"


class TestLoad:
    def test_load_factor_detail(self, library):
        library.admit({"name": "Test", "expression": "Rank($close)", "category": "vwap", "batch": "batch_001", "metrics": {"ic_mean": 0.06}})
        detail = library.load_factor("001")
        assert detail["name"] == "Test"
        assert detail["expression"] == "Rank($close)"


class TestExpressions:
    def test_get_all_expressions(self, library):
        library.admit({"name": "F1", "expression": "Rank($close)", "category": "vwap", "batch": "b1", "metrics": {}})
        library.admit({"name": "F2", "expression": "Rank($vwap)", "category": "vwap", "batch": "b1", "metrics": {}})
        exprs = library.get_all_expressions()
        assert len(exprs) == 2
        assert "Rank($close)" in exprs.values()
