"""Tests for BacktestConfig and 3-layer merge."""
from __future__ import annotations

from datetime import date

import pytest

from research.backtest.config import load_default_config


def test_load_default_returns_validated_config():
    cfg = load_default_config(factor_id="F009")
    assert cfg.universe == "csi1000"
    assert cfg.initial_capital == 10_000_000
    assert cfg.signal_recompute is True
    assert cfg.rebalance.freq_days == 5
    assert cfg.cost.commission_bps == 3
    assert cfg.matching.price_adjust == "hfq"
    assert cfg.capital.allow_intraday_netting is False


def test_per_factor_override_takes_precedence_over_defaults(tmp_path, monkeypatch):
    pf = tmp_path / "F009.backtest.yaml"
    pf.write_text("portfolio:\n  holdings_n: 100\n")
    monkeypatch.setattr(
        "research.backtest.config._per_factor_path", lambda fid: pf
    )
    cfg = load_default_config(factor_id="F009")
    assert cfg.portfolio.holdings_n == 100
    assert cfg.portfolio.weight_scheme == "equal"


def test_cli_override_takes_precedence_over_per_factor(tmp_path, monkeypatch):
    pf = tmp_path / "F009.backtest.yaml"
    pf.write_text("portfolio:\n  holdings_n: 100\n")
    monkeypatch.setattr(
        "research.backtest.config._per_factor_path", lambda fid: pf
    )
    cfg = load_default_config(
        factor_id="F009", cli_overrides={"portfolio": {"holdings_n": 30}}
    )
    assert cfg.portfolio.holdings_n == 30


def test_validate_rejects_freq_days_below_2():
    with pytest.raises(ValueError, match="freq_days"):
        load_default_config(
            factor_id="F009", cli_overrides={"rebalance": {"freq_days": 1}}
        )


def test_periods_run_subset_of_train_val_holdout():
    with pytest.raises(ValueError, match="periods.run"):
        load_default_config(
            factor_id="F009", cli_overrides={"periods": {"run": ["nonsense"]}}
        )


def test_stamp_schedule_resolves_for_date():
    cfg = load_default_config(factor_id="F009")
    assert cfg.cost.stamp_bps_at(date(2020, 1, 1)) == 10
    assert cfg.cost.stamp_bps_at(date(2024, 1, 1)) == 5


def test_stamp_bps_raises_for_uncovered_date():
    cfg = load_default_config(factor_id="F009")
    with pytest.raises(ValueError, match="no stamp schedule covers"):
        cfg.cost.stamp_bps_at(date(2014, 1, 1))
