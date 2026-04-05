"""Tests for risk/neutralization.py — cap-neutral regression.

Ported from the old tests/research/stats/test_risk_model.py.
"""

import numpy as np
import pandas as pd

from research.risk.neutralization import neutralize_cap


def _make_wide(n_dates=30, n_stocks=50, seed=42):
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2022-01-01", periods=n_dates)
    stocks = [f"S{i:03d}" for i in range(n_stocks)]
    values = rng.normal(0, 1, size=(n_dates, n_stocks))
    return pd.DataFrame(values, index=dates, columns=stocks)


class TestNeutralizeCap:
    def test_residuals_uncorrelated_with_cap(self):
        rng = np.random.default_rng(123)
        n_dates, n_stocks = 30, 50
        dates = pd.bdate_range("2022-01-01", periods=n_dates)
        stocks = [f"S{i:03d}" for i in range(n_stocks)]

        cap_raw = rng.lognormal(mean=10, sigma=1, size=(n_dates, n_stocks))
        cap_wide = pd.DataFrame(cap_raw, index=dates, columns=stocks)

        # Factor = 3 * log(cap) + noise => should be neutralized away
        factor_wide = 3.0 * np.log(cap_wide) + rng.normal(0, 0.5, size=(n_dates, n_stocks))

        residual = neutralize_cap(factor_wide, cap_wide)

        # Residual should have near-zero correlation with log(cap)
        for date in dates[:5]:
            r = residual.loc[date].dropna().values
            c = np.log(cap_wide.loc[date].values)
            corr = np.corrcoef(r[np.isfinite(r)], c[np.isfinite(r)])[0, 1]
            assert abs(corr) < 0.15

    def test_empty_input(self):
        factor = pd.DataFrame()
        cap = pd.DataFrame()
        result = neutralize_cap(factor, cap)
        assert result.empty

    def test_insufficient_obs(self):
        dates = pd.bdate_range("2022-01-01", periods=5)
        stocks = [f"S{i}" for i in range(10)]  # below min_obs=30
        factor = pd.DataFrame(
            np.random.randn(5, 10), index=dates, columns=stocks
        )
        cap = pd.DataFrame(
            np.random.lognormal(10, 1, size=(5, 10)), index=dates, columns=stocks
        )
        result = neutralize_cap(factor, cap, min_obs=30)
        # All NaN because n_stocks < min_obs
        assert result.isna().all().all()

    def test_shape_preserved(self):
        factor = _make_wide()
        cap_wide = pd.DataFrame(
            np.random.default_rng(99).lognormal(10, 1, size=factor.shape),
            index=factor.index, columns=factor.columns,
        )
        result = neutralize_cap(factor, cap_wide, min_obs=10)
        assert result.shape == factor.shape
