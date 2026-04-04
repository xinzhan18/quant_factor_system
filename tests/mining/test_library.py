"""Tests for FactorLibrary."""

import yaml
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
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
        # New fields
        assert index[0]["long_leg"] == "high"
        assert index[0]["evaluation_version"] == "v2"

    def test_admit_negative_ic_long_leg_low(self, library):
        factor_id = library.admit({
            "name": "Neg_IC", "expression": "Std($close, 20)",
            "category": "volatility", "batch": "batch_001",
            "metrics": {"ic_mean": -0.05},
        })
        detail = library.load_factor(factor_id)
        assert detail["long_leg"] == "low"
        assert detail["evaluation_version"] == "v2"

    def test_admit_ic_mean_is_fallback(self, library):
        """When ic_mean is missing, fall back to ic_mean_is."""
        factor_id = library.admit({
            "name": "Fallback", "expression": "Rank($close)",
            "category": "momentum", "batch": "batch_001",
            "metrics": {"ic_mean_is": -0.03},  # no ic_mean key
        })
        detail = library.load_factor(factor_id)
        assert detail["long_leg"] == "low"
        idx = library.list_factors()
        assert idx[0]["ic_mean"] == -0.03

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
        # Schema should match admit
        assert index[0]["long_leg"] == "high"
        assert index[0]["evaluation_version"] == "v2"

    def test_replace_schema_matches_admit(self, library):
        """replace() must produce the same detail YAML fields as admit()."""
        library.admit({"name": "Old", "expression": "Rank($close)", "category": "momentum",
                       "batch": "b1", "metrics": {"ic_mean": 0.04}})
        library.replace("001", {"name": "New", "expression": "Rank($volume)",
                                "category": "volume", "batch": "b2",
                                "metrics": {"ic_mean": -0.06}})
        detail = library.load_factor("001")
        assert detail["long_leg"] == "low"
        assert detail["evaluation_version"] == "v2"
        assert detail["replaces"] == "001"
        assert "source" in detail


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


class TestPublisherIntegration:
    def test_admit_calls_publisher_when_values_present(self, library):
        with patch("mining.publisher.FactorPublisher") as MockPub:
            mock_instance = MockPub.return_value
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_instance.publish.return_value = "/reports/factor_001.html"

            factor = {
                "name": "Test", "expression": "Rank($close)", "category": "momentum",
                "batch": "b1", "metrics": {"ic_mean": 0.05},
                "stage3": {"ic_mean_is": 0.05, "ic_ir_is": 0.8, "ic_mean_oos": 0.04,
                           "ic_ir_oos": 0.6, "ic_win_rate": 0.65, "ls_return": 0.03, "monotonicity": 0.9},
                "_factor_values": MagicMock(),
                "_factor_values_oos": MagicMock(),
            }
            factor_id = library.admit(factor)
            assert factor_id == "001"
            mock_instance.publish.assert_called_once()

    def test_admit_skips_publisher_when_no_values(self, library):
        with patch("mining.publisher.FactorPublisher") as MockPub:
            factor = {
                "name": "Test", "expression": "Rank($close)", "category": "momentum",
                "batch": "b1", "metrics": {"ic_mean": 0.05},
            }
            library.admit(factor)
            MockPub.assert_not_called()

    def test_replace_calls_publisher_when_values_present(self, library):
        library.admit({
            "name": "Old", "expression": "Rank($close)", "category": "momentum",
            "batch": "b1", "metrics": {"ic_mean": 0.04},
        })
        with patch("mining.publisher.FactorPublisher") as MockPub:
            mock_instance = MockPub.return_value
            mock_instance.__enter__ = MagicMock(return_value=mock_instance)
            mock_instance.__exit__ = MagicMock(return_value=False)
            mock_instance.publish.return_value = "/reports/factor_001.html"

            new_factor = {
                "name": "Better", "expression": "Rank(Div($close, $vwap))",
                "category": "momentum", "batch": "b2", "metrics": {"ic_mean": 0.07},
                "_factor_values": MagicMock(),
                "_factor_values_oos": MagicMock(),
            }
            library.replace("001", new_factor)
            mock_instance.publish.assert_called_once()


class TestPythonFactorAdmission:
    """Tests for admitting Python-source factors."""

    _PYTHON_CODE = "return df['close'].rolling(params['window']).std()"

    def _make_python_factor(self, **overrides):
        base = {
            "name": "rolling_std_python",
            "source": "python",
            "expression": None,
            "code": self._PYTHON_CODE,
            "category": "volatility",
            "batch": "batch_019",
            "logic_id": "logic_042",
            "lineage": {"parent": "std_returns_20", "mutation": "param_change"},
            "params": {"window": 20},
            "param_space": {"window": [5, 10, 20, 40]},
            "metrics": {"ic_mean": 0.048, "ic_std": 0.062, "ic_ir": 0.77},
        }
        base.update(overrides)
        return base

    def test_admit_python_factor(self, library, tmp_mining_dir):
        """Python factor is admitted and gets an ID."""
        factor = self._make_python_factor()
        factor_id = library.admit(factor)
        assert factor_id == "001"
        index = library.list_factors()
        assert len(index) == 1
        assert index[0]["id"] == "001"
        assert index[0]["source"] == "python"

    def test_python_factor_file_persisted(self, library, tmp_mining_dir):
        """A .py file is written to storage/python_factors/ after admission."""
        factor = self._make_python_factor()
        # Point the python_factors_dir to a temp subdir
        python_factors_dir = tmp_mining_dir / "python_factors"
        library._config.python_factors_dir = str(python_factors_dir)

        factor_id = library.admit(factor)

        py_path = python_factors_dir / f"F{factor_id}_rolling_std_python.py"
        assert py_path.exists(), f"Expected .py file at {py_path}"
        content = py_path.read_text()
        assert "rolling_std_python" in content
        assert self._PYTHON_CODE in content
        assert "META" in content
        assert "def compute" in content

    def test_python_factor_file_code_path_stored(self, library, tmp_mining_dir):
        """Detail YAML for Python factor stores code_path, source, logic_id, lineage."""
        factor = self._make_python_factor()
        python_factors_dir = tmp_mining_dir / "python_factors"
        library._config.python_factors_dir = str(python_factors_dir)

        factor_id = library.admit(factor)

        detail = library.load_factor(factor_id)
        assert detail["source"] == "python"
        assert detail["code_path"] is not None
        assert detail["logic_id"] == "logic_042"
        assert detail["lineage"]["parent"] == "std_returns_20"
        assert detail["expression"] is None

    def test_dsl_factor_still_works(self, library, tmp_mining_dir):
        """Existing DSL admission is unchanged — no regression."""
        dsl_factor = {
            "name": "rank_close",
            "expression": "Rank($close)",
            "category": "momentum",
            "batch": "b1",
            "metrics": {"ic_mean": 0.04},
        }
        factor_id = library.admit(dsl_factor)
        assert factor_id == "001"
        detail = library.load_factor("001")
        assert detail["expression"] == "Rank($close)"
        assert detail.get("source", "dsl") == "dsl"

    def test_list_includes_source(self, library, tmp_mining_dir):
        """list_factors() returns source field for both DSL and Python factors."""
        library.admit({
            "name": "dsl_factor",
            "expression": "Rank($close)",
            "category": "momentum",
            "batch": "b1",
            "metrics": {"ic_mean": 0.04},
        })
        python_factors_dir = tmp_mining_dir / "python_factors"
        library._config.python_factors_dir = str(python_factors_dir)
        library.admit(self._make_python_factor())

        factors = library.list_factors()
        assert len(factors) == 2
        sources = {f["name"]: f.get("source", "dsl") for f in factors}
        assert sources["dsl_factor"] == "dsl"
        assert sources["rolling_std_python"] == "python"
