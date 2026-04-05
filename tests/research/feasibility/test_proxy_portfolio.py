"""Tests for research.feasibility.proxy_portfolio."""

import numpy as np
import pandas as pd
import pytest

from research.feasibility.proxy_portfolio import ProxyPortfolio, build_proxy_portfolio


def _make_index(n_dates: int = 10, n_instruments: int = 20, seed: int = 0):
    """Create a MultiIndex (datetime, instrument) test fixture."""
    dates = pd.bdate_range("2023-01-02", periods=n_dates)
    instruments = [f"SH60{i:04d}" for i in range(n_instruments)]
    return pd.MultiIndex.from_product(
        [dates, instruments], names=["datetime", "instrument"]
    )


@pytest.fixture
def signal_and_mask():
    idx = _make_index(n_dates=10, n_instruments=20, seed=42)
    rng = np.random.RandomState(42)
    signal = pd.DataFrame({"factor": rng.randn(len(idx))}, index=idx)
    mask = pd.DataFrame({"tradable": True}, index=idx)
    return signal, mask


class TestBuildProxyPortfolio:
    def test_returns_proxy_portfolio(self, signal_and_mask):
        signal, mask = signal_and_mask
        result = build_proxy_portfolio(signal, mask)
        assert isinstance(result, ProxyPortfolio)

    def test_long_weights_nonneg(self, signal_and_mask):
        signal, mask = signal_and_mask
        result = build_proxy_portfolio(signal, mask)
        assert (result.long_weights["weight"] >= 0).all()

    def test_short_weights_nonpos(self, signal_and_mask):
        signal, mask = signal_and_mask
        result = build_proxy_portfolio(signal, mask)
        assert (result.short_weights["weight"] <= 0).all()

    def test_long_weights_sum_to_one_per_date(self, signal_and_mask):
        signal, mask = signal_and_mask
        result = build_proxy_portfolio(signal, mask)
        per_date = result.long_weights["weight"].groupby(level=0).sum()
        np.testing.assert_allclose(per_date.values, 1.0, atol=1e-10)

    def test_short_weights_sum_to_minus_one_per_date(self, signal_and_mask):
        signal, mask = signal_and_mask
        result = build_proxy_portfolio(signal, mask)
        per_date = result.short_weights["weight"].groupby(level=0).sum()
        np.testing.assert_allclose(per_date.values, -1.0, atol=1e-10)

    def test_abs_weights_equals_sum_of_abs(self, signal_and_mask):
        signal, mask = signal_and_mask
        result = build_proxy_portfolio(signal, mask)
        expected = result.long_weights["weight"].abs() + result.short_weights["weight"].abs()
        pd.testing.assert_series_equal(
            result.abs_weights["weight"], expected, check_names=False
        )

    def test_turnover_is_series_with_correct_dates(self, signal_and_mask):
        signal, mask = signal_and_mask
        result = build_proxy_portfolio(signal, mask)
        dates = signal.index.get_level_values(0).unique()
        assert len(result.turnover) == len(dates)

    def test_tradable_mask_excludes_stocks(self):
        """Stocks where tradable=False must never appear in portfolio."""
        idx = _make_index(n_dates=5, n_instruments=10)
        rng = np.random.RandomState(99)
        signal = pd.DataFrame({"s": rng.randn(len(idx))}, index=idx)
        mask_vals = np.ones(len(idx), dtype=bool)
        # Mark first 2 instruments as untradable on all dates
        untradable = {"SH600000", "SH600001"}
        for i, (dt, inst) in enumerate(idx):
            if inst in untradable:
                mask_vals[i] = False
        mask = pd.DataFrame({"tradable": mask_vals}, index=idx)

        result = build_proxy_portfolio(signal, mask)
        for w_df in [result.long_weights, result.short_weights, result.abs_weights]:
            insts = w_df.index.get_level_values(1).unique()
            for ut in untradable:
                assert ut not in insts

    def test_custom_pct(self, signal_and_mask):
        signal, mask = signal_and_mask
        result = build_proxy_portfolio(signal, mask, long_pct=0.10, short_pct=0.10)
        # With 20 instruments and 10% each leg, expect 2 stocks per leg
        per_date_long = (result.long_weights["weight"] > 0).groupby(level=0).sum()
        assert (per_date_long == 2).all()
