"""Tests for sandbox.py — isolated execution of Python factor code snippets.

Tests follow the TDD spec:
    test_simple_factor              — basic pct_change factor → returns Series
    test_factor_with_ops            — uses ops.std, ops.cs_rank → works
    test_factor_with_params         — uses params['period'] → works
    test_timeout                    — sleep(100) with timeout=2 → SandboxError("timeout")
    test_syntax_error               — bad syntax → SandboxError("SyntaxError")
    test_runtime_error              — 1/0 → SandboxError("ZeroDivisionError")
    test_restricted_import          — import os → SandboxError("import")
    test_return_type_must_be_series — return 42 → SandboxError("Series")
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from mining.sandbox import SandboxError, run_factor_in_sandbox


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def panel_df() -> pd.DataFrame:
    """20 business days × 3 instruments with OHLCV columns."""
    rng = np.random.default_rng(42)
    dates = pd.bdate_range("2024-01-01", periods=20)
    instruments = ["A", "B", "C"]

    index = pd.MultiIndex.from_product(
        [dates, instruments], names=["datetime", "instrument"]
    )
    n = len(index)
    close = 100 + rng.standard_normal(n).cumsum()
    volume = rng.integers(1_000_000, 10_000_000, size=n).astype(float)
    return pd.DataFrame({"close": close, "volume": volume}, index=index)


# ---------------------------------------------------------------------------
# TestSandboxExecution
# ---------------------------------------------------------------------------


class TestSandboxExecution:
    def test_simple_factor(self, panel_df):
        """Simple pct_change factor should return a pd.Series with the same index."""
        code = "return df['close'].pct_change(5)"
        result = run_factor_in_sandbox(code, panel_df, params={})
        assert isinstance(result, pd.Series), f"Expected pd.Series, got {type(result)}"
        assert len(result) == len(panel_df)

    def test_factor_with_ops(self, panel_df):
        """Factor that uses ops.std and ops.cs_rank should execute successfully."""
        code = (
            "vol = ops.std(df['close'], 5)\n"
            "return ops.cs_rank(vol)"
        )
        result = run_factor_in_sandbox(code, panel_df, params={})
        assert isinstance(result, pd.Series)
        assert len(result) == len(panel_df)

    def test_factor_with_params(self, panel_df):
        """Factor that reads params['period'] should use the supplied value."""
        code = "return df['close'].pct_change(params['period'])"
        result = run_factor_in_sandbox(code, panel_df, params={"period": 3})
        assert isinstance(result, pd.Series)
        assert len(result) == len(panel_df)

    def test_timeout(self, panel_df):
        """Code that sleeps beyond the timeout should raise SandboxError with 'timeout'."""
        code = "import time; time.sleep(100); return df['close']"
        with pytest.raises(SandboxError) as exc_info:
            run_factor_in_sandbox(code, panel_df, params={}, timeout=2)
        assert "timeout" in str(exc_info.value).lower()

    def test_syntax_error(self, panel_df):
        """Malformed Python should raise SandboxError with 'SyntaxError'."""
        code = "return df['close'].pct_change(5"  # missing closing paren
        with pytest.raises(SandboxError) as exc_info:
            run_factor_in_sandbox(code, panel_df, params={})
        assert "SyntaxError" in str(exc_info.value)

    def test_runtime_error(self, panel_df):
        """ZeroDivisionError at runtime should raise SandboxError with 'ZeroDivisionError'."""
        code = "x = 1 / 0; return df['close']"
        with pytest.raises(SandboxError) as exc_info:
            run_factor_in_sandbox(code, panel_df, params={})
        assert "ZeroDivisionError" in str(exc_info.value)

    def test_restricted_import(self, panel_df):
        """Attempting to import a forbidden module should raise SandboxError with 'import'."""
        code = "import os; return df['close']"
        with pytest.raises(SandboxError) as exc_info:
            run_factor_in_sandbox(code, panel_df, params={})
        assert "import" in str(exc_info.value).lower()

    def test_return_type_must_be_series(self, panel_df):
        """Returning a non-Series value should raise SandboxError with 'Series'."""
        code = "return 42"
        with pytest.raises(SandboxError) as exc_info:
            run_factor_in_sandbox(code, panel_df, params={})
        assert "Series" in str(exc_info.value)
