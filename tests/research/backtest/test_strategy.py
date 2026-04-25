"""Tests for TopKLongOnly + QuintilePortfolio."""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd
import pytest

from research.backtest.strategy import QuintilePortfolio, TopKLongOnly


def test_topk_returns_k_equal_weighted_excluding_nan():
    factor = pd.Series({"A": 1.0, "B": 2.0, "C": np.nan, "D": 3.0, "E": 4.0})
    universe = {"A", "B", "C", "D", "E"}
    s = TopKLongOnly(holdings_n=3, max_single_weight=0.5)
    target = s.target_weights(date(2024, 6, 28), factor, universe, price_view=None)
    assert set(target.index) == {"B", "D", "E"}
    for w in target.values:
        assert w == pytest.approx(1 / 3)


def test_topk_max_single_weight_clamps():
    factor = pd.Series({"A": 1.0, "B": 2.0})
    universe = {"A", "B"}
    s = TopKLongOnly(holdings_n=2, max_single_weight=0.4)
    target = s.target_weights(date(2024, 6, 28), factor, universe, price_view=None)
    assert target.loc["A"] == pytest.approx(0.4)
    assert target.loc["B"] == pytest.approx(0.4)


def test_topk_filters_universe_intersection():
    factor = pd.Series({"A": 1.0, "B": 2.0, "C": 3.0, "X": 99.0})
    universe = {"A", "B", "C"}
    s = TopKLongOnly(holdings_n=2)
    target = s.target_weights(date(2024, 6, 28), factor, universe, price_view=None)
    assert "X" not in target.index
    assert set(target.index) == {"B", "C"}


def test_topk_empty_universe_returns_empty():
    factor = pd.Series({"A": 1.0})
    s = TopKLongOnly(holdings_n=5)
    target = s.target_weights(date(2024, 6, 28), factor, set(), price_view=None)
    assert target.empty


def test_topk_all_nan_returns_empty():
    factor = pd.Series({"A": np.nan, "B": np.nan})
    s = TopKLongOnly(holdings_n=2)
    target = s.target_weights(date(2024, 6, 28), factor, {"A", "B"}, price_view=None)
    assert target.empty


def test_quintile_partitions_universe():
    factor = pd.Series({f"S{i:03d}": float(i) for i in range(100)})
    universe = set(factor.index)
    qp = QuintilePortfolio()
    target_q0 = qp.target_for_quintile(0, factor, universe, price_view=None)
    target_q4 = qp.target_for_quintile(4, factor, universe, price_view=None)
    assert len(target_q0) == 20
    assert len(target_q4) == 20
    assert set(target_q0.index).isdisjoint(set(target_q4.index))


def test_quintile_q4_picks_highest_factor():
    factor = pd.Series({f"S{i:03d}": float(i) for i in range(100)})
    universe = set(factor.index)
    qp = QuintilePortfolio()
    target_q4 = qp.target_for_quintile(4, factor, universe, price_view=None)
    # q=4 should contain the top 20 (highest factor: S080..S099)
    assert all(int(s.replace("S", "")) >= 80 for s in target_q4.index)


def test_quintile_q0_picks_lowest_factor():
    factor = pd.Series({f"S{i:03d}": float(i) for i in range(100)})
    universe = set(factor.index)
    qp = QuintilePortfolio()
    target_q0 = qp.target_for_quintile(0, factor, universe, price_view=None)
    assert all(int(s.replace("S", "")) < 20 for s in target_q0.index)


def test_quintile_default_target_weights_is_top():
    factor = pd.Series({f"S{i:03d}": float(i) for i in range(100)})
    universe = set(factor.index)
    qp = QuintilePortfolio()
    default = qp.target_weights(date(2024, 6, 28), factor, universe, price_view=None)
    q4 = qp.target_for_quintile(4, factor, universe, price_view=None)
    assert set(default.index) == set(q4.index)


def test_quintile_drops_nan_before_partition():
    factor = pd.Series({f"S{i:03d}": float(i) for i in range(100)})
    factor.iloc[0:50] = np.nan   # half the universe is NaN
    universe = set(factor.index)
    qp = QuintilePortfolio()
    target_q4 = qp.target_for_quintile(4, factor, universe, price_view=None)
    # Now only 50 eligible → 10 per quintile
    assert len(target_q4) == 10


def test_quintile_q_out_of_range_raises():
    factor = pd.Series({f"S{i}": float(i) for i in range(50)})
    qp = QuintilePortfolio()
    with pytest.raises(ValueError, match="q must be in"):
        qp.target_for_quintile(5, factor, set(factor.index), price_view=None)


def test_quintile_handles_universe_smaller_than_n_quintiles():
    factor = pd.Series({"A": 1.0, "B": 2.0, "C": 3.0})  # 3 < 5 quintiles
    qp = QuintilePortfolio()
    target = qp.target_for_quintile(4, factor, {"A", "B", "C"}, price_view=None)
    assert target.empty   # size = 3 // 5 = 0
