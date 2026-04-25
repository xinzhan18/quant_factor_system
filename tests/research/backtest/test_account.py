"""Tests for Account (T+1 lock + pending cash + writeoff)."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from research.backtest.account import Account, Fill


def test_buy_locks_shares_until_next_day():
    acc = Account(initial_capital=1_000_000)
    acc.transact(
        Fill(
            side="buy", date=date(2024, 6, 28), symbol="SH600000",
            shares=1000, fill_price=10.0, cost_cny=10.0, reason="target_diff",
        )
    )
    assert acc.cash == pytest.approx(1_000_000 - 10_000 - 10)
    assert acc.available_shares("SH600000", date(2024, 6, 28)) == 0
    assert acc.available_shares("SH600000", date(2024, 6, 29)) == 1000


def test_sell_proceeds_to_pending_cash_then_settle():
    acc = Account(initial_capital=100_000)
    acc.transact(
        Fill("buy", date(2024, 6, 28), "SH600000", 1000, 10.0, 10.0, "target_diff")
    )
    acc.transact(
        Fill("sell", date(2024, 7, 1), "SH600000", 1000, 11.0, 15.0, "target_diff")
    )
    assert acc.cash == pytest.approx(100_000 - 10_000 - 10)
    assert acc.pending_cash == pytest.approx(11_000 - 15)
    acc.settle_cash(on_date=date(2024, 7, 2))
    assert acc.pending_cash == 0
    assert acc.cash == pytest.approx(100_000 - 10_000 - 10 + 11_000 - 15)


def test_settle_cash_only_releases_strictly_earlier_dates():
    acc = Account(initial_capital=100_000)
    acc.transact(
        Fill("buy", date(2024, 6, 28), "SH600000", 1000, 10.0, 0.0, "target_diff")
    )
    acc.transact(
        Fill("sell", date(2024, 7, 1), "SH600000", 1000, 10.0, 0.0, "target_diff")
    )
    # Same-day settle does NOT release that day's pending
    acc.settle_cash(on_date=date(2024, 7, 1))
    assert acc.pending_cash == pytest.approx(10_000)
    # Next day does
    acc.settle_cash(on_date=date(2024, 7, 2))
    assert acc.pending_cash == 0


def test_mark_to_market_uses_last_close():
    acc = Account(initial_capital=100_000)
    acc.transact(
        Fill("buy", date(2024, 6, 28), "SH600000", 1000, 10.0, 0.0, "target_diff")
    )
    prices = pd.Series({"SH600000": 12.0})
    equity = acc.mark_to_market(date(2024, 7, 1), prices)
    assert equity == pytest.approx(100_000 - 10_000 + 12_000)


def test_mark_to_market_reuses_last_close_when_price_missing():
    acc = Account(initial_capital=100_000)
    acc.transact(
        Fill("buy", date(2024, 6, 28), "SH600000", 1000, 10.0, 0.0, "target_diff")
    )
    # First mark establishes last_close
    acc.mark_to_market(date(2024, 6, 28), pd.Series({"SH600000": 10.0}))
    # Second mark missing the symbol: should fall back to last_close
    eq = acc.mark_to_market(date(2024, 7, 1), pd.Series(dtype=float))
    assert eq == pytest.approx(100_000 - 10_000 + 10_000)


def test_force_liquidate_delisted_credits_cash_immediately():
    acc = Account(initial_capital=100_000)
    acc.transact(
        Fill("buy", date(2024, 6, 28), "SH600000", 1000, 10.0, 0.0, "target_diff")
    )
    acc.transact(
        Fill(
            "sell", date(2024, 7, 1), "SH600000", 1000, 10.0, 0.0,
            reason="delisted_writeoff",
        )
    )
    assert acc.cash == pytest.approx(100_000 - 10_000 + 10_000)
    assert acc.pending_cash == 0


def test_sell_more_than_held_raises():
    acc = Account(initial_capital=100_000)
    acc.transact(
        Fill("buy", date(2024, 6, 28), "SH600000", 100, 10.0, 0.0, "target_diff")
    )
    with pytest.raises(ValueError, match="sell exceeds holdings"):
        acc.transact(
            Fill("sell", date(2024, 7, 1), "SH600000", 200, 10.0, 0.0, "target_diff")
        )


def test_zero_share_fill_is_noop():
    """Blocked-trade log entries arrive with shares=0; must not change state."""
    acc = Account(initial_capital=100_000)
    acc.transact(Fill("buy", date(2024, 6, 28), "SH600000", 0, 10.0, 0.0, "blocked_buy"))
    assert acc.cash == 100_000
    assert "SH600000" not in acc.held_symbols()


def test_held_symbols_excludes_fully_sold():
    acc = Account(initial_capital=100_000)
    acc.transact(Fill("buy", date(2024, 6, 28), "SH600000", 100, 10.0, 0.0, "target_diff"))
    acc.transact(Fill("sell", date(2024, 7, 1), "SH600000", 100, 10.0, 0.0, "target_diff"))
    assert "SH600000" not in acc.held_symbols()


def test_positions_snapshot_returns_dataframe():
    acc = Account(initial_capital=100_000)
    acc.transact(
        Fill("buy", date(2024, 6, 28), "SH600000", 1000, 10.0, 0.0, "target_diff")
    )
    acc.mark_to_market(date(2024, 6, 28), pd.Series({"SH600000": 10.0}))
    snap = acc.positions_snapshot(date(2024, 6, 28))
    assert len(snap) == 1
    assert snap.iloc[0]["symbol"] == "SH600000"
    assert snap.iloc[0]["shares"] == 1000
