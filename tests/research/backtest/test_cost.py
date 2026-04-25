"""Tests for CostModel."""
from __future__ import annotations

from datetime import date

import pytest

from research.backtest.config import CostConfig, StampScheduleEntry
from research.backtest.cost import compute_cost


@pytest.fixture
def cost_cfg():
    return CostConfig(
        stamp_schedule=(
            StampScheduleEntry(date(2015, 1, 1), date(2023, 8, 27), 10.0),
            StampScheduleEntry(date(2023, 8, 28), date(9999, 12, 31), 5.0),
        ),
        commission_bps=3.0,
        slippage_bps=5.0,
        min_commission_cny=5.0,
    )


def test_buy_cost_no_stamp(cost_cfg):
    # 1000 × 10 = 10_000 notional; commission 3bps=3, but min 5; slippage 5bps=5
    # buy: no stamp; total = max(3, 5) + 5 = 10
    cost = compute_cost("buy", price=10.0, shares=1000, dt=date(2020, 1, 1), config=cost_cfg)
    assert cost == pytest.approx(10.0)


def test_sell_cost_pre_2023_with_10bps_stamp(cost_cfg):
    # notional 10_000; commission max(3,5)=5; slippage 5; stamp 10bps=10; total 20
    cost = compute_cost("sell", price=10.0, shares=1000, dt=date(2020, 1, 1), config=cost_cfg)
    assert cost == pytest.approx(20.0)


def test_sell_cost_post_2023_with_5bps_stamp(cost_cfg):
    # post 2023-08-28: stamp 5bps; total = 5 + 5 + 5 = 15
    cost = compute_cost("sell", price=10.0, shares=1000, dt=date(2024, 1, 1), config=cost_cfg)
    assert cost == pytest.approx(15.0)


def test_min_commission_floor(cost_cfg):
    # 100 × 1 = 100 notional; commission 3bps=0.03 → floor 5; slippage 5bps=0.05
    cost = compute_cost("buy", price=1.0, shares=100, dt=date(2020, 1, 1), config=cost_cfg)
    assert cost == pytest.approx(5.05)


def test_commission_no_floor_when_above_min(cost_cfg):
    # large notional: 100_000 × 10 = 1M; commission 3bps=300 (above 5 floor)
    # buy, no stamp: 300 + 500 = 800
    cost = compute_cost("buy", price=10.0, shares=100_000, dt=date(2020, 1, 1), config=cost_cfg)
    assert cost == pytest.approx(800.0)


def test_stamp_regime_change_boundary(cost_cfg):
    # 2023-08-27 = 10bps; 2023-08-28 = 5bps
    pre = compute_cost("sell", 10.0, 1000, date(2023, 8, 27), cost_cfg)
    post = compute_cost("sell", 10.0, 1000, date(2023, 8, 28), cost_cfg)
    assert pre == pytest.approx(20.0)   # 5 + 5 + 10
    assert post == pytest.approx(15.0)  # 5 + 5 + 5
