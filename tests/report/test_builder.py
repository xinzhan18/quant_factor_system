"""Integration test for ReportDataBuilder -- mocked DB."""
import pandas as pd
import numpy as np
import pytest
from unittest.mock import patch, MagicMock
from report.builder import ReportDataBuilder


def _mock_factor_metadata():
    return {
        "id": "001", "name": "test_factor",
        "expression": "Std($close, 20)",
        "category": "volatility", "batch": "test_batch",
        "admitted_at": "2026-01-01",
    }


def _mock_db_data(n_dates=200, n_stocks=50):
    """Returns flat DataFrames matching the new _load_data_from_db() format."""
    np.random.seed(42)
    dates = pd.bdate_range("2022-01-01", periods=n_dates)
    factor_rows, price_rows = [], []
    for d in dates:
        for s in [f"S{i:03d}" for i in range(n_stocks)]:
            fv = np.random.randn()
            close = 10 + 0.05 * fv + np.random.randn() * 0.3
            factor_rows.append({"time": d, "symbol": s, "value": fv})
            price_rows.append({"time": d, "symbol": s, "close": abs(close)})
    return pd.DataFrame(factor_rows), pd.DataFrame(price_rows)


class TestReportDataBuilder:
    @patch.object(ReportDataBuilder, "_load_factor_metadata")
    @patch.object(ReportDataBuilder, "_load_data_from_db")
    @patch.object(ReportDataBuilder, "_load_library_factors")
    def test_build_returns_new_schema(self, mock_lib, mock_db, mock_meta):
        mock_meta.return_value = _mock_factor_metadata()
        fdf, pdf = _mock_db_data()
        mock_db.return_value = (fdf, pdf)
        mock_lib.return_value = {}

        builder = ReportDataBuilder("001")
        result = builder.build()

        assert "factor" in result
        assert "predictive_power" in result
        assert "profitability" in result
        assert "decay_tradability" in result
        assert "uniqueness" in result
        assert "composite" in result

    @patch.object(ReportDataBuilder, "_load_factor_metadata")
    @patch.object(ReportDataBuilder, "_load_data_from_db")
    @patch.object(ReportDataBuilder, "_load_library_factors")
    def test_composite_has_seven_dimensions(self, mock_lib, mock_db, mock_meta):
        mock_meta.return_value = _mock_factor_metadata()
        fdf, pdf = _mock_db_data()
        mock_db.return_value = (fdf, pdf)
        mock_lib.return_value = {}

        builder = ReportDataBuilder("001")
        result = builder.build()
        assert len(result["composite"]["dimensions"]) == 7

    @patch.object(ReportDataBuilder, "_load_factor_metadata")
    @patch.object(ReportDataBuilder, "_load_data_from_db")
    @patch.object(ReportDataBuilder, "_load_library_factors")
    def test_predictive_power_has_ic_summary(self, mock_lib, mock_db, mock_meta):
        mock_meta.return_value = _mock_factor_metadata()
        fdf, pdf = _mock_db_data()
        mock_db.return_value = (fdf, pdf)
        mock_lib.return_value = {}

        builder = ReportDataBuilder("001")
        result = builder.build()

        pp = result["predictive_power"]
        assert "summary" in pp
        assert "is" in pp["summary"]
        assert "oos" in pp["summary"]
        assert "charts" in pp

    @patch.object(ReportDataBuilder, "_load_factor_metadata")
    @patch.object(ReportDataBuilder, "_load_data_from_db")
    @patch.object(ReportDataBuilder, "_load_library_factors")
    def test_profitability_has_stats_and_ls(self, mock_lib, mock_db, mock_meta):
        mock_meta.return_value = _mock_factor_metadata()
        fdf, pdf = _mock_db_data()
        mock_db.return_value = (fdf, pdf)
        mock_lib.return_value = {}

        builder = ReportDataBuilder("001")
        result = builder.build()

        prof = result["profitability"]
        assert "stats" in prof
        assert "ls_stats" in prof
        assert "monotonicity" in prof
        assert "charts" in prof

    @patch.object(ReportDataBuilder, "_load_factor_metadata")
    @patch.object(ReportDataBuilder, "_load_data_from_db")
    @patch.object(ReportDataBuilder, "_load_library_factors")
    def test_decay_has_ic_by_period(self, mock_lib, mock_db, mock_meta):
        mock_meta.return_value = _mock_factor_metadata()
        fdf, pdf = _mock_db_data()
        mock_db.return_value = (fdf, pdf)
        mock_lib.return_value = {}

        builder = ReportDataBuilder("001")
        result = builder.build()

        decay = result["decay_tradability"]
        assert "ic_by_period" in decay
        assert "charts" in decay

    @patch.object(ReportDataBuilder, "_load_factor_metadata")
    @patch.object(ReportDataBuilder, "_load_data_from_db")
    @patch.object(ReportDataBuilder, "_load_library_factors")
    def test_uniqueness_with_empty_library(self, mock_lib, mock_db, mock_meta):
        mock_meta.return_value = _mock_factor_metadata()
        fdf, pdf = _mock_db_data()
        mock_db.return_value = (fdf, pdf)
        mock_lib.return_value = {}

        builder = ReportDataBuilder("001")
        result = builder.build()

        uniq = result["uniqueness"]
        assert uniq["max_corr"] == 0.0
        assert uniq["max_corr_factor"] == ""
        assert "charts" in uniq

    @patch.object(ReportDataBuilder, "_load_factor_metadata")
    @patch.object(ReportDataBuilder, "_load_data_from_db")
    @patch.object(ReportDataBuilder, "_load_library_factors")
    def test_factor_metadata_in_result(self, mock_lib, mock_db, mock_meta):
        mock_meta.return_value = _mock_factor_metadata()
        fdf, pdf = _mock_db_data()
        mock_db.return_value = (fdf, pdf)
        mock_lib.return_value = {}

        builder = ReportDataBuilder("001")
        result = builder.build()

        assert result["factor"]["id"] == "001"
        assert result["factor"]["name"] == "test_factor"
        assert result["factor"]["data_level"] == "L0"
