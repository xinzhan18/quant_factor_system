"""Tests for DataProvider -- Qlib D.features wrapper with parquet caching."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from research.compute.cache import FactorValueCache
from research.compute.data_provider import DataProvider
from research.compute.universe import UniverseManager


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


def _make_multiindex_df(n_dates=5, n_stocks=3, col_name="factor"):
    """Build a small (datetime, instrument) MultiIndex DataFrame."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2024-01-01", periods=n_dates)
    stocks = [f"SH60000{i}" for i in range(n_stocks)]
    idx = pd.MultiIndex.from_product(
        [dates, stocks], names=["datetime", "instrument"]
    )
    return pd.DataFrame({col_name: rng.standard_normal(len(idx))}, index=idx)


@pytest.fixture
def cache(tmp_path):
    return FactorValueCache(cache_dir=str(tmp_path / "cache"))


@pytest.fixture
def mock_universe():
    um = MagicMock(spec=UniverseManager)
    um.resolve.return_value = {"csi1000": "dict"}
    return um


# -----------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------


class TestDataProvider:
    @patch("qlib.data.D")
    def test_get_factor_values(self, mock_d, mock_universe, cache):
        expected = _make_multiindex_df(col_name="Rank($close)")
        mock_d.features.return_value = expected

        provider = DataProvider(universe=mock_universe, cache=cache)
        result = provider.get_factor_values("Rank($close)", "2024-01-01", "2024-01-07")

        pd.testing.assert_frame_equal(result, expected)
        mock_d.features.assert_called_once()

    @patch("qlib.data.D")
    def test_get_factor_values_cached(self, mock_d, mock_universe, cache):
        expected = _make_multiindex_df(col_name="Rank($close)")
        mock_d.features.return_value = expected

        provider = DataProvider(universe=mock_universe, cache=cache)
        provider.get_factor_values("Rank($close)", "2024-01-01", "2024-01-07")
        provider.get_factor_values("Rank($close)", "2024-01-01", "2024-01-07")

        # D.features should only be called once; second call served from cache
        assert mock_d.features.call_count == 1

    @patch("qlib.data.D")
    def test_get_factor_values_no_cache(self, mock_d, mock_universe, cache):
        expected = _make_multiindex_df(col_name="Rank($close)")
        mock_d.features.return_value = expected

        provider = DataProvider(universe=mock_universe, cache=cache, use_cache=False)
        provider.get_factor_values("Rank($close)", "2024-01-01", "2024-01-07")
        provider.get_factor_values("Rank($close)", "2024-01-01", "2024-01-07")

        # Without cache, D.features is called twice
        assert mock_d.features.call_count == 2

    @patch("qlib.data.D")
    def test_get_returns(self, mock_d, mock_universe, cache):
        expected = _make_multiindex_df(col_name="Ref($close, -1) / $close - 1")
        mock_d.features.return_value = expected

        provider = DataProvider(universe=mock_universe, cache=cache)
        result = provider.get_returns("2024-01-01", "2024-01-07", horizon=1)

        assert "return_1d" in result.columns
        assert len(result) == len(expected)

    @patch("qlib.data.D")
    def test_get_market_data(self, mock_d, mock_universe, cache):
        idx = pd.MultiIndex.from_product(
            [pd.bdate_range("2024-01-01", periods=3), ["SH600000"]],
            names=["datetime", "instrument"],
        )
        expected = pd.DataFrame(
            {"$close": [10.0, 10.1, 10.2], "$volume": [1e6, 2e6, 3e6]},
            index=idx,
        )
        mock_d.features.return_value = expected

        provider = DataProvider(universe=mock_universe, cache=cache)
        result = provider.get_market_data(
            ["$close", "$volume"], "2024-01-01", "2024-01-03"
        )

        assert "$close" in result.columns
        assert "$volume" in result.columns
