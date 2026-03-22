"""Tests for data/loaders.py — mining factor loading."""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch


class TestGetAvailableFactors:
    def test_returns_factor_list(self):
        from data.loaders import get_available_factors

        mock_conn = MagicMock()
        mock_df = pd.DataFrame([
            {"factor_id": "001", "name": "VWAP_Dev", "expression": "Rank($close)",
             "category": "vwap", "ic_mean": 0.05, "ic_ir": 0.8, "admitted_at": "2026-03-22"},
        ])
        with patch("data.loaders.pd.read_sql", return_value=mock_df):
            result = get_available_factors(mock_conn)
        assert len(result) == 1
        assert result[0]["factor_id"] == "001"
        assert result[0]["name"] == "VWAP_Dev"

    def test_returns_empty_list(self):
        from data.loaders import get_available_factors

        mock_conn = MagicMock()
        with patch("data.loaders.pd.read_sql", return_value=pd.DataFrame()):
            result = get_available_factors(mock_conn)
        assert result == []


class TestGetFactorData:
    def test_returns_dataframe(self):
        from data.loaders import get_factor_data

        mock_conn = MagicMock()
        mock_df = pd.DataFrame({
            "symbol": ["SH600000", "SH600001"],
            "time": pd.to_datetime(["2024-01-02", "2024-01-02"]),
            "value": [1.5, -0.3],
        })
        with patch("data.loaders.pd.read_sql", return_value=mock_df):
            df, err = get_factor_data("001", mock_conn)
        assert err is None
        assert len(df) == 2
        assert list(df.columns) == ["symbol", "time", "value"]

    def test_returns_none_for_empty(self):
        from data.loaders import get_factor_data

        mock_conn = MagicMock()
        with patch("data.loaders.pd.read_sql", return_value=pd.DataFrame()):
            df, err = get_factor_data("999", mock_conn)
        assert df is None
        assert "No data" in err


class TestGetFactorMetrics:
    def test_returns_dict(self):
        from data.loaders import get_factor_metrics

        mock_conn = MagicMock()
        mock_df = pd.DataFrame([{
            "factor_id": "001", "name": "Test", "ic_mean": 0.05,
        }])
        with patch("data.loaders.pd.read_sql", return_value=mock_df):
            result = get_factor_metrics("001", mock_conn)
        assert result["factor_id"] == "001"
        assert result["ic_mean"] == 0.05

    def test_returns_none_for_missing(self):
        from data.loaders import get_factor_metrics

        mock_conn = MagicMock()
        with patch("data.loaders.pd.read_sql", return_value=pd.DataFrame()):
            result = get_factor_metrics("999", mock_conn)
        assert result is None
