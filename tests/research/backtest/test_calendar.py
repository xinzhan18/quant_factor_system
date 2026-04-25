"""Tests for TradeCalendar (synthetic + DB)."""
from __future__ import annotations

import os
from datetime import date

import pytest

from research.backtest.calendar import TradeCalendar


@pytest.fixture
def synth_cal():
    """Trading days = all weekdays Jun 24 – Jul 5 2024 minus simulated holiday."""
    import pandas as pd

    days = list(pd.bdate_range("2024-06-24", "2024-07-05").date)
    # Simulate a holiday on 2024-07-01 (Mon)
    days = [d for d in days if d != date(2024, 7, 1)]
    universe = {d: {"A", "B", "C"} for d in days}
    return TradeCalendar.from_data(days, universe)


def test_trading_days_inclusive(synth_cal):
    days = synth_cal.trading_days(date(2024, 6, 24), date(2024, 6, 28))
    assert len(days) == 5  # Mon-Fri


def test_trading_days_excludes_simulated_holiday(synth_cal):
    days = synth_cal.trading_days(date(2024, 7, 1), date(2024, 7, 5))
    assert date(2024, 7, 1) not in days
    assert date(2024, 7, 2) in days


def test_add_trading_days_skips_holiday(synth_cal):
    # Fri 2024-06-28 + 1 → Tue 2024-07-02 (skip simulated holiday Mon)
    assert synth_cal.add_trading_days(date(2024, 6, 28), 1) == date(2024, 7, 2)


def test_add_trading_days_negative_offset(synth_cal):
    assert synth_cal.add_trading_days(date(2024, 7, 2), -1) == date(2024, 6, 28)


def test_universe_at(synth_cal):
    assert synth_cal.universe_at(date(2024, 6, 28)) == {"A", "B", "C"}
    assert synth_cal.universe_at(date(2099, 1, 1)) == set()


def test_rebalance_schedule_monday_anchor(synth_cal):
    sched = synth_cal.rebalance_schedule(
        start=date(2024, 6, 24), end=date(2024, 7, 5),
        freq_days=5, anchor="monday",
    )
    # First Monday in range = 2024-06-24; +5 trading days (skip 7/1 holiday) = 2024-07-02
    assert sched[0] == date(2024, 6, 24)
    assert sched[1] == date(2024, 7, 2)


def test_rebalance_schedule_first_trade_day_anchor(synth_cal):
    sched = synth_cal.rebalance_schedule(
        start=date(2024, 6, 25), end=date(2024, 7, 5),
        freq_days=3, anchor="first_trade_day",
    )
    assert sched[0] == date(2024, 6, 25)


def test_rebalance_schedule_custom_date_anchor(synth_cal):
    sched = synth_cal.rebalance_schedule(
        start=date(2024, 6, 24), end=date(2024, 7, 5),
        freq_days=5, anchor=date(2024, 6, 26),
    )
    assert sched[0] == date(2024, 6, 26)


def test_rebalance_schedule_bad_anchor_raises(synth_cal):
    with pytest.raises(ValueError, match="bad anchor"):
        synth_cal.rebalance_schedule(
            start=date(2024, 6, 24), end=date(2024, 7, 5),
            freq_days=5, anchor="quarterly",
        )


# DB-backed test (only runs if DB available)

@pytest.mark.skipif(
    not os.environ.get("TIMESCALE_PASSWORD"),
    reason="TIMESCALE_PASSWORD not set; skipping DB integration",
)
def test_from_db_smoke():
    cal = TradeCalendar.from_db()
    assert len(cal.trading_days(date(2024, 6, 1), date(2024, 6, 30))) > 15
    syms = cal.universe_at(date(2023, 6, 28))
    assert len(syms) >= 800
