"""Tests for UniverseManager -- stock universe resolution."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from research.compute.universe import UniverseManager


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


@pytest.fixture
def mock_d():
    """Patch qlib.data.D for all tests.

    D is imported lazily inside methods via ``from qlib.data import D``,
    so we patch the qlib.data module's D attribute.
    """
    with patch("qlib.data.D") as mock:
        yield mock


# -----------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------


class TestUniverseManager:
    def test_default_name(self):
        um = UniverseManager()
        assert um.name == "csi1000"

    def test_custom_name(self):
        um = UniverseManager("csi300")
        assert um.name == "csi300"

    def test_resolve_returns_instrument_dict(self, mock_d):
        mock_d.instruments.return_value = {"csi1000": ("2020-01-01", "2024-12-31")}
        um = UniverseManager("csi1000")
        result = um.resolve()
        assert result == {"csi1000": ("2020-01-01", "2024-12-31")}
        mock_d.instruments.assert_called_once_with("csi1000")

    def test_resolve_caches_result(self, mock_d):
        mock_d.instruments.return_value = {"all": "dict"}
        um = UniverseManager("all")
        um.resolve()
        um.resolve()
        # Should only call D.instruments once due to caching
        assert mock_d.instruments.call_count == 1

    def test_resolve_fallback_on_error(self, mock_d):
        mock_d.instruments.side_effect = [Exception("not found"), {"all": "fallback"}]
        um = UniverseManager("nonexistent")
        result = um.resolve()
        assert result == {"all": "fallback"}
        assert mock_d.instruments.call_count == 2

    def test_stock_list(self, mock_d):
        mock_d.instruments.return_value = {"csi1000": "dict"}
        idx = pd.MultiIndex.from_tuples(
            [
                (pd.Timestamp("2024-06-03"), "SH600000"),
                (pd.Timestamp("2024-06-03"), "SH600001"),
                (pd.Timestamp("2024-06-04"), "SH600000"),
                (pd.Timestamp("2024-06-04"), "SH600001"),
            ],
            names=["datetime", "instrument"],
        )
        mock_d.features.return_value = pd.DataFrame(
            {"$close": [10.0, 11.0, 10.1, 11.1]}, index=idx
        )
        um = UniverseManager("csi1000")
        stocks = um.stock_list()
        assert set(stocks) == {"SH600000", "SH600001"}

    def test_stock_list_caches(self, mock_d):
        mock_d.instruments.return_value = {"csi1000": "dict"}
        idx = pd.MultiIndex.from_tuples(
            [(pd.Timestamp("2024-06-03"), "SH600000")],
            names=["datetime", "instrument"],
        )
        mock_d.features.return_value = pd.DataFrame({"$close": [10.0]}, index=idx)
        um = UniverseManager("csi1000")
        um.stock_list()
        um.stock_list()
        assert mock_d.features.call_count == 1

    def test_reset_clears_cache(self, mock_d):
        mock_d.instruments.return_value = {"csi1000": "dict"}
        um = UniverseManager("csi1000")
        um.resolve()
        um.reset()
        assert um._inst_dict is None
        assert um._stock_list is None
        um.resolve()
        assert mock_d.instruments.call_count == 2
