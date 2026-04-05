"""Tests for FactorEngine -- DSL and Python factor execution."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd
import pytest

from research.compute.data_provider import DataProvider
from research.compute.factor_engine import FactorEngine
from research.compute.preprocess import Preprocessor
from research.compute.sandbox import SandboxError


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


def _make_panel(n_dates=20, n_stocks=3):
    """Build a panel DataFrame with OHLCV columns."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2024-01-01", periods=n_dates)
    stocks = [f"SH60000{i}" for i in range(n_stocks)]
    idx = pd.MultiIndex.from_product(
        [dates, stocks], names=["datetime", "instrument"]
    )
    n = len(idx)
    close = 100 + rng.standard_normal(n).cumsum()
    return pd.DataFrame(
        {
            "$open": close + rng.standard_normal(n) * 0.5,
            "$high": close + abs(rng.standard_normal(n)),
            "$low": close - abs(rng.standard_normal(n)),
            "$close": close,
            "$volume": rng.integers(1_000_000, 10_000_000, size=n).astype(float),
            "$amount": rng.integers(10_000_000, 100_000_000, size=n).astype(float),
        },
        index=idx,
    )


@pytest.fixture
def panel():
    return _make_panel()


@pytest.fixture
def mock_provider(panel):
    provider = MagicMock(spec=DataProvider)
    # get_factor_values returns a single-column DF
    provider.get_factor_values.return_value = panel[["$close"]].rename(
        columns={"$close": "Rank($close)"}
    )
    # get_market_data returns the full panel
    provider.get_market_data.return_value = panel
    return provider


# -----------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------


class TestFactorEngineDSL:
    def test_compute_dsl_returns_dataframe(self, mock_provider):
        engine = FactorEngine(provider=mock_provider)
        result = engine.compute_dsl("Rank($close)", "2024-01-01", "2024-01-31")
        assert isinstance(result, pd.DataFrame)
        assert result.index.names == ["datetime", "instrument"]

    def test_compute_dsl_with_preprocess(self, mock_provider):
        engine = FactorEngine(provider=mock_provider)
        result = engine.compute_dsl(
            "Rank($close)", "2024-01-01", "2024-01-31", preprocess=True
        )
        assert isinstance(result, pd.DataFrame)


class TestFactorEnginePython:
    def test_compute_python_simple(self, mock_provider):
        engine = FactorEngine(provider=mock_provider)
        code = "return df['close'].pct_change(5)"
        result = engine.compute_python(
            code=code, start="2024-01-01", end="2024-01-31"
        )
        assert isinstance(result, pd.DataFrame)
        assert "factor" in result.columns

    def test_compute_python_with_params(self, mock_provider):
        engine = FactorEngine(provider=mock_provider)
        code = "return df['close'].pct_change(params['period'])"
        result = engine.compute_python(
            code=code,
            start="2024-01-01",
            end="2024-01-31",
            params={"period": 3},
        )
        assert isinstance(result, pd.DataFrame)

    def test_compute_python_syntax_error(self, mock_provider):
        engine = FactorEngine(provider=mock_provider)
        code = "return df['close'].pct_change(5"  # missing paren
        with pytest.raises(SandboxError):
            engine.compute_python(code=code, start="2024-01-01", end="2024-01-31")

    def test_compute_python_forbidden_import(self, mock_provider):
        engine = FactorEngine(provider=mock_provider)
        code = "import os; return df['close']"
        with pytest.raises(SandboxError):
            engine.compute_python(code=code, start="2024-01-01", end="2024-01-31")

    def test_compute_python_with_ops(self, mock_provider):
        engine = FactorEngine(provider=mock_provider)
        code = "vol = ops.std(df['close'], 5)\nreturn vol"
        result = engine.compute_python(
            code=code, start="2024-01-01", end="2024-01-31"
        )
        assert isinstance(result, pd.DataFrame)
