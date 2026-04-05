"""Shared test fixtures for research.stats tests."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest


def make_panel(
    n_dates: int,
    n_symbols: int,
    start: str,
    rng: np.random.Generator,
    signal: np.ndarray | None = None,
) -> pd.DataFrame:
    """Build a flat [time, symbol, value] panel with controlled properties.

    Args:
        n_dates: Number of business days.
        n_symbols: Number of symbols.
        start: Start date string.
        rng: numpy random Generator (used only when *signal* is None).
        signal: Optional (n_dates, n_symbols) array of values.

    Returns:
        DataFrame with columns [time, symbol, value].
    """
    dates = pd.bdate_range(start, periods=n_dates, freq="B")
    symbols = [f"S{i:03d}" for i in range(n_symbols)]
    rows = []
    for i, d in enumerate(dates):
        for j, s in enumerate(symbols):
            val = signal[i, j] if signal is not None else rng.normal()
            rows.append({"time": d, "symbol": s, "value": val})
    return pd.DataFrame(rows)
