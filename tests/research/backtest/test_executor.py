"""Tests for Executor — target diff + mask + cost + lot floor."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from research.backtest.account import Account, Fill
from research.backtest.calendar import TradeCalendar
from research.backtest.config import (
    CostConfig,
    FilterConfig,
    StampScheduleEntry,
)
from research.backtest.data_view import PriceView
from research.backtest.executor import Executor, LOT_SIZE
from research.backtest.filters import ExecutionPolicy, TradabilityMask
from research.backtest.tradability import TradabilityProvider


@pytest.fixture
def cost_cfg():
    return CostConfig(
        stamp_schedule=(
            StampScheduleEntry(date(2015, 1, 1), date(9999, 12, 31), 5.0),
        ),
        commission_bps=3.0, slippage_bps=5.0, min_commission_cny=5.0,
    )


@pytest.fixture
def filter_cfg_open():
    return FilterConfig(
        block_st=False, block_suspended=False,
        block_limit_up_at_buy=False, block_limit_down_at_sell=False,
        cooldown_days_after_unsuspend=0, newly_listed_days=0,
        stale_position_days_max=5,
    )


@pytest.fixture
def filter_cfg_block_all():
    return FilterConfig(
        block_st=True, block_suspended=True,
        block_limit_up_at_buy=True, block_limit_down_at_sell=True,
        cooldown_days_after_unsuspend=1, newly_listed_days=60,
        stale_position_days_max=5,
    )


@pytest.fixture
def panel():
    rows = []
    for d in pd.bdate_range("2024-06-24", "2024-06-28"):
        for s in ["A", "B", "C"]:
            rows.append((d, s, 10.0, 10.5, 9.5, 10.0, 1_000_000, 10_000_000))
    df = pd.DataFrame(
        rows,
        columns=["dt", "sym", "open", "high", "low", "close", "volume", "amount"],
    ).set_index(["dt", "sym"])
    df.index.names = ["datetime", "instrument"]
    df["limit_up"] = 11.0
    df["limit_down"] = 9.0
    return df


@pytest.fixture
def view(panel):
    return PriceView.from_dataframe(panel)


@pytest.fixture
def cal(panel):
    days = sorted({d.date() for d in panel.index.get_level_values(0)})
    universe = {d: {"A", "B", "C"} for d in days}
    return TradeCalendar.from_data(days, universe)


@pytest.fixture
def provider(view):
    st = pd.DataFrame(
        {"is_st": []},
        index=pd.MultiIndex.from_tuples([], names=["datetime", "instrument"]),
    )
    lc = pd.DataFrame(
        dict(
            listing_date=[date(2000, 1, 1)] * 3,
            delisting_date=[None] * 3,
            board=["main"] * 3,
        ),
        index=["A", "B", "C"],
    )
    return TradabilityProvider.from_data(st, lc, view)


@pytest.fixture
def mask_pass_all(view, provider, filter_cfg_open, cal):
    return TradabilityMask(view, provider, filter_cfg_open, cal)


@pytest.fixture
def mask_block_buys(view, provider, filter_cfg_open, cal):
    """Mask that always blocks buys but allows sells."""
    class _M(TradabilityMask):
        def can_buy(self, exec_date, symbols):
            return pd.Series(False, index=list(symbols))
    return _M(view, provider, filter_cfg_open, cal)


def test_target_diff_generates_buy(view, mask_pass_all, cost_cfg):
    acc = Account(initial_capital=1_000_000)
    target = pd.Series({"A": 0.5})  # 500k at 10 = 50_000 shares = 500 lots
    e = Executor()
    fills = e.execute(
        date(2024, 6, 25), target, acc, mask_pass_all, view,
        cost_cfg, ExecutionPolicy(), allow_intraday_netting=False,
    )
    buys = [f for f in fills if f.side == "buy" and f.shares > 0]
    assert len(buys) == 1
    assert buys[0].symbol == "A"
    assert buys[0].shares == 50_000


def test_lot_floor_rounds_to_100s(view, mask_pass_all, cost_cfg):
    # 10_500 → 10.5 lots → floor to 10 lots = 1000 shares
    acc = Account(initial_capital=10_500)
    target = pd.Series({"A": 1.0})
    e = Executor()
    fills = e.execute(
        date(2024, 6, 25), target, acc, mask_pass_all, view,
        cost_cfg, ExecutionPolicy(), allow_intraday_netting=False,
    )
    buy = next(f for f in fills if f.side == "buy" and f.shares > 0)
    assert buy.shares % LOT_SIZE == 0
    assert buy.shares == 1000


def test_blocked_buy_logs_zero_share_entry(view, mask_block_buys, cost_cfg):
    acc = Account(initial_capital=100_000)
    target = pd.Series({"A": 1.0})
    e = Executor()
    fills = e.execute(
        date(2024, 6, 25), target, acc, mask_block_buys, view,
        cost_cfg, ExecutionPolicy(), allow_intraday_netting=False,
    )
    blocked = [f for f in fills if f.reason == "blocked_buy"]
    assert len(blocked) == 1
    assert blocked[0].shares == 0
    # Account untouched
    assert acc.cash == 100_000


def test_diff_generates_sell_for_held_above_target(
    view, mask_pass_all, cost_cfg
):
    acc = Account(initial_capital=100_000)
    acc.transact(Fill("buy", date(2024, 6, 23), "A", 1000, 10.0, 0.0, "target_diff"))
    target = pd.Series({"A": 0.0})   # liquidate A
    e = Executor()
    fills = e.execute(
        date(2024, 6, 25), target, acc, mask_pass_all, view,
        cost_cfg, ExecutionPolicy(), allow_intraday_netting=False,
    )
    sells = [f for f in fills if f.side == "sell" and f.shares > 0]
    assert len(sells) == 1
    assert sells[0].shares == 1000


def test_intraday_netting_false_uses_only_cash(
    view, mask_pass_all, cost_cfg
):
    acc = Account(initial_capital=10_000)
    # Pre-load with 1000 shares of B (bought 2 days ago, so unlocked)
    acc.transact(Fill("buy", date(2024, 6, 23), "B", 1000, 10.0, 0.0, "target_diff"))
    # On 6/25, sell B and buy A; pending cash from sell shouldn't fund buy
    target = pd.Series({"B": 0.0, "A": 1.0})
    e = Executor()
    fills = e.execute(
        date(2024, 6, 25), target, acc, mask_pass_all, view,
        cost_cfg, ExecutionPolicy(), allow_intraday_netting=False,
    )
    bought_shares = sum(f.shares for f in fills if f.side == "buy" and f.shares > 0)
    # Original cash was 10000 - 10000 = 0 → should buy 0 shares (pro-rata scale 0)
    assert bought_shares == 0


def test_intraday_netting_true_reuses_sell_proceeds(
    view, mask_pass_all, cost_cfg
):
    acc = Account(initial_capital=10_000)
    acc.transact(Fill("buy", date(2024, 6, 23), "B", 1000, 10.0, 0.0, "target_diff"))
    target = pd.Series({"B": 0.0, "A": 1.0})
    e = Executor()
    fills = e.execute(
        date(2024, 6, 25), target, acc, mask_pass_all, view,
        cost_cfg, ExecutionPolicy(), allow_intraday_netting=True,
    )
    bought = sum(f.shares for f in fills if f.side == "buy" and f.shares > 0)
    assert bought > 0


def test_no_target_no_holdings_returns_empty(view, mask_pass_all, cost_cfg):
    acc = Account(initial_capital=100_000)
    e = Executor()
    fills = e.execute(
        date(2024, 6, 25), pd.Series(dtype=float), acc, mask_pass_all, view,
        cost_cfg, ExecutionPolicy(), allow_intraday_netting=False,
    )
    assert fills == []


def test_capital_pro_rata_scales_buys(view, mask_pass_all, cost_cfg):
    acc = Account(initial_capital=10_000)
    # Want 100% in A AND 100% in B → 200% target → must scale to 50% each
    target = pd.Series({"A": 1.0, "B": 1.0})
    e = Executor()
    fills = e.execute(
        date(2024, 6, 25), target, acc, mask_pass_all, view,
        cost_cfg, ExecutionPolicy(capital_shortage="pro_rata"),
        allow_intraday_netting=False,
    )
    buys = [f for f in fills if f.side == "buy" and f.shares > 0]
    # Total notional must not exceed initial cash
    total_notional = sum(f.fill_price * f.shares + f.cost_cny for f in buys)
    assert total_notional <= 10_000 + 1
