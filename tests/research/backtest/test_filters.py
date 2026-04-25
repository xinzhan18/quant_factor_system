"""Tests for TradabilityMask + ExecutionPolicy."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from research.backtest.account import Account, Fill
from research.backtest.calendar import TradeCalendar
from research.backtest.config import FilterConfig
from research.backtest.data_view import PriceView
from research.backtest.filters import ExecutionPolicy, TradabilityMask
from research.backtest.tradability import TradabilityProvider


@pytest.fixture
def filter_config():
    return FilterConfig(
        block_st=True,
        block_suspended=True,
        block_limit_up_at_buy=True,
        block_limit_down_at_sell=True,
        cooldown_days_after_unsuspend=1,
        newly_listed_days=60,
        stale_position_days_max=5,
    )


@pytest.fixture
def small_panel():
    """Hand-built 3-day, 4-symbol panel with controlled price moves."""
    rows = []
    # Mon 6/24: baseline closes
    rows.append((pd.Timestamp("2024-06-24"), "A", 10.0, 10.2, 9.8, 10.0, 1_000_000, 10_000_000))
    rows.append((pd.Timestamp("2024-06-24"), "B", 10.0, 10.2, 9.8, 10.0, 1_000_000, 10_000_000))
    rows.append((pd.Timestamp("2024-06-24"), "C", 10.0, 10.2, 9.8, 10.0, 1_000_000, 10_000_000))
    rows.append((pd.Timestamp("2024-06-24"), "D", 10.0, 10.2, 9.8, 10.0, 0,         0))   # suspended
    # Tue 6/25:
    #   A opens at 11.0 (+10% gap → limit-up at open)
    #   B opens at 9.0  (-10% gap → limit-down at open)
    #   C opens normally at 10.05
    #   D resumes (volume > 0) — should be in cooldown
    rows.append((pd.Timestamp("2024-06-25"), "A", 11.0, 11.1, 11.0, 11.0, 100_000, 1_000_000))
    rows.append((pd.Timestamp("2024-06-25"), "B", 9.0,  9.1,  8.9,  9.0,  100_000, 1_000_000))
    rows.append((pd.Timestamp("2024-06-25"), "C", 10.05, 10.1, 9.95, 10.0, 100_000, 1_000_000))
    rows.append((pd.Timestamp("2024-06-25"), "D", 10.0, 10.1, 9.95, 10.0, 100_000, 1_000_000))
    df = pd.DataFrame(
        rows, columns=["dt", "sym", "open", "high", "low", "close", "volume", "amount"]
    )
    df["limit_up"] = 11.0
    df["limit_down"] = 9.0
    df = df.set_index(["dt", "sym"])
    df.index.names = ["datetime", "instrument"]
    return df


@pytest.fixture
def small_calendar(small_panel):
    days = sorted({d.date() for d in small_panel.index.get_level_values(0)})
    universe = {d: {"A", "B", "C", "D"} for d in days}
    return TradeCalendar.from_data(days, universe)


@pytest.fixture
def small_view(small_panel):
    return PriceView.from_dataframe(small_panel)


@pytest.fixture
def small_provider(small_view):
    # No ST in this fixture, no lifecycle events
    st = pd.DataFrame(
        {"is_st": []},
        index=pd.MultiIndex.from_tuples([], names=["datetime", "instrument"]),
    )
    lifecycle = pd.DataFrame(
        dict(
            listing_date=[date(2000, 1, 1)] * 4,
            delisting_date=[None] * 4,
            board=["main"] * 4,
        ),
        index=["A", "B", "C", "D"],
    )
    return TradabilityProvider.from_data(st, lifecycle, small_view)


def test_can_buy_blocks_limit_up_at_open(
    small_view, small_provider, filter_config, small_calendar
):
    mask = TradabilityMask(small_view, small_provider, filter_config, small_calendar)
    can_buy = mask.can_buy(date(2024, 6, 25), ["A", "B", "C", "D"])
    assert can_buy.loc["A"] is False or not can_buy.loc["A"]   # gapped up
    assert can_buy.loc["C"]                                     # normal


def test_can_sell_blocks_limit_down_at_open(
    small_view, small_provider, filter_config, small_calendar
):
    # Build account holding B with no T+1 lock (bought 2 days ago)
    acc = Account(initial_capital=100_000)
    acc.transact(Fill("buy", date(2024, 6, 23), "B", 1000, 10.0, 0.0, "target_diff"))
    mask = TradabilityMask(small_view, small_provider, filter_config, small_calendar)
    can_sell = mask.can_sell(date(2024, 6, 25), ["B"], acc)
    assert not can_sell.loc["B"]


def test_can_sell_honors_t1_lock(
    small_view, small_provider, filter_config, small_calendar
):
    acc = Account(initial_capital=100_000)
    acc.transact(Fill("buy", date(2024, 6, 25), "C", 100, 10.0, 0.0, "target_diff"))
    mask = TradabilityMask(small_view, small_provider, filter_config, small_calendar)
    can_sell = mask.can_sell(date(2024, 6, 25), ["C"], acc)
    assert not can_sell.loc["C"]


def test_can_buy_blocks_cooldown_after_unsuspend(
    small_view, small_provider, filter_config, small_calendar
):
    mask = TradabilityMask(small_view, small_provider, filter_config, small_calendar)
    # D was suspended on 6/24 (vol=0), resumes 6/25 → in cooldown
    can_buy = mask.can_buy(date(2024, 6, 25), ["D"])
    assert not can_buy.loc["D"]


def test_can_buy_blocks_currently_suspended(
    small_view, small_provider, filter_config, small_calendar
):
    mask = TradabilityMask(small_view, small_provider, filter_config, small_calendar)
    can_buy = mask.can_buy(date(2024, 6, 24), ["D"])
    assert not can_buy.loc["D"]


def test_can_buy_blocks_newly_listed(
    small_view, filter_config, small_calendar
):
    st = pd.DataFrame(
        {"is_st": []},
        index=pd.MultiIndex.from_tuples([], names=["datetime", "instrument"]),
    )
    # A listed 30 days ago < newly_listed_days=60 → blocked
    lc = pd.DataFrame(
        dict(
            listing_date=[date(2024, 5, 26), date(2000, 1, 1), date(2000, 1, 1), date(2000, 1, 1)],
            delisting_date=[None] * 4, board=["main"] * 4,
        ),
        index=["A", "B", "C", "D"],
    )
    p = TradabilityProvider.from_data(st, lc, small_view)
    mask = TradabilityMask(small_view, p, filter_config, small_calendar)
    can_buy = mask.can_buy(date(2024, 6, 25), ["A", "B"])
    assert not can_buy.loc["A"]
    # B not gapped-up if checked? B IS gapped-down on 6/25 — but block_limit_up_at_buy
    # only blocks limit-up; gap-down doesn't block buys. So B should be buyable.
    assert can_buy.loc["B"]


def test_can_buy_empty_input_returns_empty_series(
    small_view, small_provider, filter_config, small_calendar
):
    mask = TradabilityMask(small_view, small_provider, filter_config, small_calendar)
    assert mask.can_buy(date(2024, 6, 25), []).empty


def test_execution_policy_defaults():
    p = ExecutionPolicy()
    assert p.blocked_buy == "drop"
    assert p.blocked_sell == "carry_over_n_days"
    assert p.blocked_sell_max_carry_days == 5
    assert p.capital_shortage == "pro_rata"
    assert p.lot_residual == "floor"
    assert p.nan_factor == "exclude_from_pool"
