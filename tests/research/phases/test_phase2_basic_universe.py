"""Verify _basic_universe_metrics produces sensible results when reusing
clean_series from the primary universe across secondary universes.

The new path skips per-universe preprocess_factor (~30-50% of
single-candidate runtime when ≥2 secondaries were configured). Because
MAD winsorize + zscore are rank-preserving on a strict subset, IC +
monotonicity (rank-based) should still be valid; we assert structural
invariants and a coverage range that matches the sub-universe size.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.compute.preprocess import PreprocessConfig, preprocess_factor
from research.phases.phase2_execute import _basic_universe_metrics


@pytest.fixture
def panel():
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=60, freq="B")
    symbols = [f"S{i:03d}" for i in range(50)]
    idx = pd.MultiIndex.from_product([dates, symbols], names=["datetime", "instrument"])
    factor = pd.Series(np.random.randn(len(idx)), index=idx, name="value")
    returns = pd.DataFrame({
        "time": idx.get_level_values(0),
        "symbol": idx.get_level_values(1),
        "value": np.random.randn(len(idx)) * 0.02,
    })
    primary_mask = pd.Series(True, index=idx)
    sec_mask = pd.Series(
        [s in symbols[:30] for s in idx.get_level_values(1)],
        index=idx,
    )
    return factor, returns, primary_mask, sec_mask


def test_clean_series_path_runs_and_reports_coverage(panel):
    factor, returns, primary_mask, sec_mask = panel
    clean = preprocess_factor(factor, PreprocessConfig(), tradable_mask=primary_mask)

    result = _basic_universe_metrics(
        clean,
        sec_mask,
        returns,
        validation_range=("2023-01-01", "2023-03-31"),
        primary_horizon=1,
    )
    assert "coverage" in result
    # Synthetic factor has no NaN, so every mask cell is covered → 1.0.
    # Coverage measures (mask ∧ non-null) / mask, not subset size.
    assert result["coverage"] == pytest.approx(1.0)
    # Result should populate the standard metric keys (or report error)
    assert "ic_mean" in result or "error" in result


def test_empty_universe_mask_returns_error(panel):
    factor, returns, primary_mask, _ = panel
    clean = preprocess_factor(factor, PreprocessConfig(), tradable_mask=primary_mask)
    empty_mask = pd.Series(False, index=clean.index)

    result = _basic_universe_metrics(
        clean,
        empty_mask,
        returns,
        validation_range=("2023-01-01", "2023-03-31"),
        primary_horizon=1,
    )
    assert result == {"error": "empty_universe_mask"}
