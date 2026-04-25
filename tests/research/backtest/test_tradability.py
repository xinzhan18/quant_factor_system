"""Tests for TradabilityProvider (synthetic + DB)."""
from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from research.backtest.data_view import PriceView
from research.backtest.tradability import TradabilityProvider, _board_of_symbol


@pytest.fixture
def st_table():
    """ST: only A on 2024-06-26."""
    idx = pd.MultiIndex.from_tuples(
        [(pd.Timestamp("2024-06-26"), "A")], names=["datetime", "instrument"]
    )
    return pd.DataFrame({"is_st": [True]}, index=idx)


@pytest.fixture
def lifecycle_table():
    return pd.DataFrame(
        dict(
            listing_date=[
                date(2000, 1, 1), date(2024, 1, 1),
                date(2010, 1, 1), date(2010, 1, 1),
            ],
            delisting_date=[None, None, None, None],
            board=["main", "main", "chinext", "star"],
        ),
        index=["A", "NEW", "SZ300001", "SH688001"],
    )


@pytest.fixture
def synth_provider(synthetic_panel, st_table, lifecycle_table):
    view = PriceView.from_dataframe(synthetic_panel)
    return TradabilityProvider.from_data(st_table, lifecycle_table, view)


def test_st_mask_picks_up_pit_flag(synth_provider):
    mask = synth_provider.st_mask(date(2024, 6, 26), ["A", "B"])
    assert mask.loc["A"] is True or mask.loc["A"]
    assert not mask.loc["B"]


def test_st_mask_default_false_when_date_missing(synth_provider):
    mask = synth_provider.st_mask(date(2099, 1, 1), ["A", "B"])
    assert not mask.any()


def test_is_st_scalar(synth_provider):
    assert synth_provider.is_st(date(2024, 6, 26), "A") is True
    assert synth_provider.is_st(date(2024, 6, 26), "B") is False


def test_listing_date(synth_provider):
    assert synth_provider.listing_date("A") == date(2000, 1, 1)
    assert synth_provider.listing_date("UNKNOWN") is None


def test_is_newly_listed_window(synth_provider):
    # 'NEW' listed 2024-01-01; on 2024-06-28 = 179 days
    assert synth_provider.is_newly_listed(date(2024, 1, 1), "NEW", n_days=60) is True
    assert synth_provider.is_newly_listed(date(2024, 1, 30), "NEW", n_days=60) is True
    assert synth_provider.is_newly_listed(date(2024, 6, 28), "NEW", n_days=60) is False


def test_is_newly_listed_falls_back_when_unknown(synth_provider):
    # Unknown symbol → not newly listed (don't block buys for missing data)
    assert synth_provider.is_newly_listed(date(2024, 6, 28), "UNKNOWN", n_days=60) is False


def test_board_of_uses_lifecycle_table(synth_provider):
    assert synth_provider.board_of("SZ300001") == "chinext"
    assert synth_provider.board_of("SH688001") == "star"
    assert synth_provider.board_of("A") == "main"


def test_board_of_falls_back_to_prefix_for_unknown_symbol(synth_provider):
    assert synth_provider.board_of("SH688999") == "star"
    assert synth_provider.board_of("SZ300999") == "chinext"
    assert synth_provider.board_of("BJ800001") == "bse"
    assert synth_provider.board_of("SH600001") == "main"


def test_limit_pct_st_overrides_board(synth_provider):
    # A is ST on 2024-06-26
    assert synth_provider.limit_pct(date(2024, 6, 26), "A") == pytest.approx(0.05)


def test_limit_pct_main_board(synth_provider):
    assert synth_provider.limit_pct(date(2024, 6, 28), "B") == pytest.approx(0.10)


def test_limit_pct_chinext_pre_2020():
    # Test the pure resolver to avoid date-of-st issues
    p = TradabilityProvider.from_data(
        st_table=pd.DataFrame({"is_st": []},
                                index=pd.MultiIndex.from_tuples(
                                    [], names=["datetime", "instrument"]
                                )),
        lifecycle_table=pd.DataFrame(),
    )
    assert p._resolve_limit_pct(date(2019, 1, 1), "chinext", is_st=False) == 0.10
    assert p._resolve_limit_pct(date(2020, 8, 24), "chinext", is_st=False) == 0.20
    assert p._resolve_limit_pct(date(2020, 8, 23), "chinext", is_st=False) == 0.10
    assert p._resolve_limit_pct(date(2021, 1, 1), "star", is_st=False) == 0.20
    assert p._resolve_limit_pct(date(2024, 1, 1), "bse", is_st=False) == 0.30
    assert p._resolve_limit_pct(date(2024, 1, 1), "main", is_st=False) == 0.10
    # ST always wins
    assert p._resolve_limit_pct(date(2024, 1, 1), "chinext", is_st=True) == 0.05


def test_suspended_mask_via_volume_zero(synthetic_panel, st_table, lifecycle_table):
    # Force volume=0 for B on 2024-06-26
    panel = synthetic_panel.copy()
    panel.loc[(pd.Timestamp("2024-06-26"), "B"), "volume"] = 0
    panel.loc[(pd.Timestamp("2024-06-26"), "B"), "amount"] = 0
    view = PriceView.from_dataframe(panel)
    p = TradabilityProvider.from_data(st_table, lifecycle_table, view)
    mask = p.suspended_mask(date(2024, 6, 26), ["A", "B"])
    assert mask.loc["B"] is True or mask.loc["B"]
    assert not mask.loc["A"]


def test_suspended_mask_no_view_returns_all_false():
    p = TradabilityProvider.from_data(
        st_table=pd.DataFrame({"is_st": []},
                                index=pd.MultiIndex.from_tuples(
                                    [], names=["datetime", "instrument"]
                                )),
        lifecycle_table=pd.DataFrame(),
        price_view=None,
    )
    mask = p.suspended_mask(date(2024, 6, 26), ["A", "B"])
    assert not mask.any()


def test_board_of_symbol_module_helper():
    assert _board_of_symbol("SH688001") == "star"
    assert _board_of_symbol("SZ300001") == "chinext"
    assert _board_of_symbol("BJ400001") == "bse"
    assert _board_of_symbol("SH600000") == "main"
