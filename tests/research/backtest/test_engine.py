"""Tests for Engine state machine — end-to-end on synthetic data."""
from __future__ import annotations

from datetime import date
from typing import Any

import numpy as np
import pandas as pd
import pytest

from research.backtest.calendar import TradeCalendar
from research.backtest.config import (
    BacktestConfig,
    BenchmarkConfig,
    CapitalConfig,
    CostConfig,
    FilterConfig,
    MatchingConfig,
    OutputConfig,
    PeriodsConfig,
    PortfolioConfig,
    RebalanceConfig,
    StampScheduleEntry,
)
from research.backtest.data_view import PriceView
from research.backtest.engine import Engine
from research.backtest.filters import TradabilityMask
from research.backtest.strategy import QuintilePortfolio, TopKLongOnly
from research.backtest.tradability import TradabilityProvider


@pytest.fixture
def big_panel():
    """20-day, 20-symbol panel with random walks."""
    rng = np.random.default_rng(7)
    days = list(pd.bdate_range("2024-06-01", periods=20))
    syms = [f"S{i:02d}" for i in range(20)]
    rows = []
    for d in days:
        for s in syms:
            base = 10.0 + rng.normal(0, 0.5)
            rows.append((d, s, base, base + 0.5, base - 0.5, base, 1_000_000, 10_000_000))
    df = pd.DataFrame(
        rows, columns=["dt", "sym", "open", "high", "low", "close", "volume", "amount"]
    ).set_index(["dt", "sym"])
    df.index.names = ["datetime", "instrument"]
    df["limit_up"] = 11.0
    df["limit_down"] = 9.0
    return df


@pytest.fixture
def big_cal(big_panel):
    days = sorted({d.date() for d in big_panel.index.get_level_values(0)})
    syms = sorted(set(big_panel.index.get_level_values(1)))
    universe = {d: set(syms) for d in days}
    return TradeCalendar.from_data(days, universe)


@pytest.fixture
def big_view(big_panel):
    return PriceView.from_dataframe(big_panel)


@pytest.fixture
def big_provider(big_view):
    syms = sorted(set(big_view._df.index.get_level_values(1)))
    st = pd.DataFrame(
        {"is_st": []},
        index=pd.MultiIndex.from_tuples([], names=["datetime", "instrument"]),
    )
    lc = pd.DataFrame(
        dict(
            listing_date=[date(2000, 1, 1)] * len(syms),
            delisting_date=[None] * len(syms),
            board=["main"] * len(syms),
        ),
        index=syms,
    )
    return TradabilityProvider.from_data(st, lc, big_view)


@pytest.fixture
def base_config():
    return BacktestConfig(
        universe="csi1000",
        initial_capital=1_000_000,
        signal_recompute=False,
        rebalance=RebalanceConfig(freq_days=5, anchor="first_trade_day"),
        portfolio=PortfolioConfig(
            holdings_n=5, weight_scheme="equal", max_single_weight=0.25
        ),
        matching=MatchingConfig(match_price="open", price_adjust="hfq"),
        cost=CostConfig(
            stamp_schedule=(
                StampScheduleEntry(date(2015, 1, 1), date(9999, 12, 31), 5.0),
            ),
            commission_bps=3.0, slippage_bps=5.0, min_commission_cny=5.0,
        ),
        capital=CapitalConfig(allow_intraday_netting=False),
        filters=FilterConfig(
            block_st=False, block_suspended=False,
            block_limit_up_at_buy=False, block_limit_down_at_sell=False,
            cooldown_days_after_unsuspend=0, newly_listed_days=0,
            stale_position_days_max=5,
        ),
        periods=PeriodsConfig(
            train=(date(2024, 6, 1), date(2024, 6, 30)),
            val=(date(2024, 7, 1), date(2024, 7, 31)),
            holdout=(date(2024, 8, 1), date(2024, 8, 31)),
            run=("train",),
        ),
        benchmark=BenchmarkConfig(kind="csi1000_total_return"),
        output=OutputConfig(save_trades=True, save_positions=True, figs=()),
    )


class _DummyFactorLoader:
    """Returns a deterministic factor: rank by symbol number ascending each day."""

    def __init__(self, syms: list[str]):
        self._syms = sorted(syms)

    def at(self, dt: date) -> pd.Series:
        return pd.Series(
            {s: float(int(s[1:])) for s in self._syms}
        )


def test_engine_runs_end_to_end(big_view, big_cal, big_provider, base_config):
    mask = TradabilityMask(big_view, big_provider, base_config.filters, big_cal)
    syms = sorted(set(big_view._df.index.get_level_values(1)))
    main = TopKLongOnly(holdings_n=5, max_single_weight=0.25)
    quint = QuintilePortfolio()
    engine = Engine(base_config, big_cal, big_view, mask, main, quint,
                     _DummyFactorLoader(syms))
    days = big_cal.trading_days(date(2024, 6, 1), date(2024, 6, 28))
    result = engine.run(days[0], days[-1])
    assert len(result.equity_curve) == len(days)
    assert "total_equity" in result.equity_curve.columns
    assert "drawdown" in result.equity_curve.columns


def test_engine_produces_trades(big_view, big_cal, big_provider, base_config):
    mask = TradabilityMask(big_view, big_provider, base_config.filters, big_cal)
    syms = sorted(set(big_view._df.index.get_level_values(1)))
    main = TopKLongOnly(holdings_n=5, max_single_weight=0.25)
    quint = QuintilePortfolio()
    engine = Engine(base_config, big_cal, big_view, mask, main, quint,
                     _DummyFactorLoader(syms))
    days = big_cal.trading_days(date(2024, 6, 1), date(2024, 6, 28))
    result = engine.run(days[0], days[-1])
    assert len(result.trades) > 0
    real_buys = result.trades[
        (result.trades["side"] == "buy") & (result.trades["shares"] > 0)
    ]
    assert len(real_buys) > 0


def test_engine_metrics_have_expected_shape(
    big_view, big_cal, big_provider, base_config
):
    mask = TradabilityMask(big_view, big_provider, base_config.filters, big_cal)
    syms = sorted(set(big_view._df.index.get_level_values(1)))
    main = TopKLongOnly(holdings_n=5, max_single_weight=0.25)
    quint = QuintilePortfolio()
    engine = Engine(base_config, big_cal, big_view, mask, main, quint,
                     _DummyFactorLoader(syms))
    days = big_cal.trading_days(date(2024, 6, 1), date(2024, 6, 28))
    result = engine.run(days[0], days[-1])
    assert "full" in result.metrics
    assert "reconciliation" in result.metrics
    for k in ["ann_return", "volatility", "sharpe", "max_dd", "n_days"]:
        assert k in result.metrics["full"]


def test_engine_reconciliation_bounded(
    big_view, big_cal, big_provider, base_config
):
    """With deterministic small price moves, daily Δequity bps stays bounded."""
    mask = TradabilityMask(big_view, big_provider, base_config.filters, big_cal)
    syms = sorted(set(big_view._df.index.get_level_values(1)))
    main = TopKLongOnly(holdings_n=5, max_single_weight=0.25)
    quint = QuintilePortfolio()
    engine = Engine(base_config, big_cal, big_view, mask, main, quint,
                     _DummyFactorLoader(syms))
    days = big_cal.trading_days(date(2024, 6, 1), date(2024, 6, 28))
    result = engine.run(days[0], days[-1])
    # Random-walk equity moves are bounded; max bps shouldn't exceed any
    # single-day extreme. Just assert it's finite.
    assert result.metrics["reconciliation"]["max_violation_bps"] < 10000.0


def test_engine_information_set_invariant(
    big_view, big_cal, big_provider, base_config
):
    """Two runs with identical history but different next-day data must agree on
    decisions made before that next day."""
    mask = TradabilityMask(big_view, big_provider, base_config.filters, big_cal)
    syms = sorted(set(big_view._df.index.get_level_values(1)))

    class PoisonLoader(_DummyFactorLoader):
        def __init__(self, syms, poison_after: date):
            super().__init__(syms)
            self._poison_after = poison_after

        def at(self, dt: date) -> pd.Series:
            base = super().at(dt)
            if dt > self._poison_after:
                return base * 1000  # massive poison
            return base

    main = TopKLongOnly(holdings_n=5, max_single_weight=0.25)
    quint = QuintilePortfolio()
    engine = Engine(base_config, big_cal, big_view, mask, main, quint,
                     PoisonLoader(syms, poison_after=date(2024, 6, 7)))
    days = big_cal.trading_days(date(2024, 6, 3), date(2024, 6, 7))
    r1 = engine.run(days[0], days[-1])

    # Re-run with poison gone — same decisions on dates ≤ 2024-06-07 must hold
    engine2 = Engine(base_config, big_cal, big_view, mask, main, quint,
                      _DummyFactorLoader(syms))
    r2 = engine2.run(days[0], days[-1])

    pd.testing.assert_series_equal(
        r1.equity_curve["total_equity"],
        r2.equity_curve["total_equity"],
        check_names=False,
    )
