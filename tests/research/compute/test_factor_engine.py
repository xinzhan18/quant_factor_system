"""Tests for FactorEngine -- DSL and Python factor execution."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import pytest

from research.compute.data_provider import DataProvider
from research.compute.factor_engine import FactorEngine


# -----------------------------------------------------------------------
# Fixtures
# -----------------------------------------------------------------------


def _make_panel(n_dates=20, n_stocks=3):
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
    provider.get_factor_values.return_value = panel[["$close"]].rename(
        columns={"$close": "Rank($close)"}
    )
    provider.get_market_data.return_value = panel
    return provider


# -----------------------------------------------------------------------
# DSL tests
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


# -----------------------------------------------------------------------
# Python file-based tests
# -----------------------------------------------------------------------


class TestFactorEnginePython:
    def test_compute_python_from_file(self, mock_provider, tmp_path):
        factor_file = tmp_path / "test_factor.py"
        factor_file.write_text(
            "import pandas as pd\n"
            "def compute(df, params):\n"
            "    return df['close'].pct_change(5)\n"
        )
        engine = FactorEngine(provider=mock_provider)
        result = engine.compute_python(
            str(factor_file), start="2024-01-01", end="2024-01-31"
        )
        assert isinstance(result, pd.DataFrame)
        assert "factor" in result.columns

    def test_compute_python_with_params(self, mock_provider, tmp_path):
        factor_file = tmp_path / "param_factor.py"
        factor_file.write_text(
            "def compute(df, params):\n"
            "    return df['close'].pct_change(params['period'])\n"
        )
        engine = FactorEngine(provider=mock_provider)
        result = engine.compute_python(
            str(factor_file), start="2024-01-01", end="2024-01-31",
            params={"period": 3},
        )
        assert isinstance(result, pd.DataFrame)

    def test_compute_python_missing_file(self, mock_provider):
        engine = FactorEngine(provider=mock_provider)
        with pytest.raises(FileNotFoundError):
            engine.compute_python(
                "/nonexistent/factor.py", start="2024-01-01", end="2024-01-31"
            )

    def test_compute_python_no_compute_function(self, mock_provider, tmp_path):
        factor_file = tmp_path / "bad_factor.py"
        factor_file.write_text("x = 42\n")
        engine = FactorEngine(provider=mock_provider)
        with pytest.raises(AttributeError, match="must define a compute"):
            engine.compute_python(
                str(factor_file), start="2024-01-01", end="2024-01-31"
            )

    def test_compute_python_wrong_return_type(self, mock_provider, tmp_path):
        factor_file = tmp_path / "wrong_type.py"
        factor_file.write_text(
            "def compute(df, params):\n"
            "    return 42\n"
        )
        engine = FactorEngine(provider=mock_provider)
        with pytest.raises(TypeError, match="must return pd.Series"):
            engine.compute_python(
                str(factor_file), start="2024-01-01", end="2024-01-31"
            )

    def test_compute_python_can_use_any_library(self, mock_provider, tmp_path):
        """Python factors are not restricted — can use scipy, for loops, etc."""
        factor_file = tmp_path / "free_factor.py"
        factor_file.write_text(
            "import numpy as np\n"
            "def compute(df, params):\n"
            "    result = df['close'].copy()\n"
            "    for i in range(5):\n"
            "        result = result + np.random.default_rng(i).normal(0, 0.01, len(result))\n"
            "    return result\n"
        )
        engine = FactorEngine(provider=mock_provider)
        result = engine.compute_python(
            str(factor_file), start="2024-01-01", end="2024-01-31"
        )
        assert isinstance(result, pd.DataFrame)
