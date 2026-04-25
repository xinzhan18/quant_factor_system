"""Shared fixtures for backtest tests."""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def synthetic_panel():
    """Tiny synthetic OHLCV panel for 5 trading days × 4 symbols (no events)."""
    dates = pd.bdate_range("2024-06-24", "2024-06-28")  # Mon-Fri
    syms = ["A", "B", "C", "D"]
    idx = pd.MultiIndex.from_product([dates, syms], names=["datetime", "instrument"])
    n = len(idx)
    rng = np.random.default_rng(42)
    df = pd.DataFrame(
        dict(
            open=10.0 + rng.normal(0, 0.1, n),
            high=10.2 + rng.normal(0, 0.1, n),
            low=9.8 + rng.normal(0, 0.1, n),
            close=10.0 + rng.normal(0, 0.1, n),
            volume=1_000_000 + rng.integers(0, 100_000, n),
            amount=10_000_000 + rng.normal(0, 1_000_000, n),
            limit_up=11.0,
            limit_down=9.0,
            returns_1d=rng.normal(0, 0.01, n),
        ),
        index=idx,
    )
    return df
