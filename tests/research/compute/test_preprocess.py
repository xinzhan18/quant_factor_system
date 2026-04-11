"""Tests for vectorized preprocess (winsorize MAD + cross-sectional z-score)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from research.compute.preprocess import (
    PreprocessConfig,
    _from_wide,
    _to_wide,
    preprocess_factor,
    winsorize_mad,
    zscore_cross_section,
)


def _make_factor_series(
    n_dates: int = 10, n_stocks: int = 8, seed: int = 42
) -> pd.Series:
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2024-01-01", periods=n_dates)
    stocks = [f"SYM{i:02d}" for i in range(n_stocks)]
    idx = pd.MultiIndex.from_product([dates, stocks], names=["time", "symbol"])
    values = rng.standard_normal(len(idx))
    return pd.Series(values, index=idx, name="factor")


class TestLongWideRoundtrip:
    def test_roundtrip_preserves_values(self) -> None:
        s = _make_factor_series(n_dates=5, n_stocks=3)
        wide = _to_wide(s)
        back = _from_wide(wide, name=s.name)
        pd.testing.assert_series_equal(
            back.sort_index(), s.sort_index(), check_names=True
        )

    def test_to_wide_rejects_flat_index(self) -> None:
        s = pd.Series([1.0, 2.0, 3.0])
        with pytest.raises(ValueError, match="MultiIndex"):
            _to_wide(s)


class TestWinsorizeMad:
    def test_zero_mad_collapses_row(self) -> None:
        # Row 0: [1,1,1,1,100] — median=1, abs_dev=[0,0,0,0,99],
        # MAD=0, half_width=0, lower=upper=1 → everything clipped to 1.
        wide = pd.DataFrame(
            [[1.0, 1.0, 1.0, 1.0, 100.0]],
            index=pd.DatetimeIndex(["2024-01-02"], name="time"),
            columns=pd.Index([f"SYM{i}" for i in range(5)], name="symbol"),
        )
        out = winsorize_mad(wide, k=5.0, scale=1.4826)
        assert (out.iloc[0] == 1.0).all()

    def test_pass_through_at_default_k(self) -> None:
        # k=5, scale=1.4826 → half_width=7.413*MAD, well outside [1,5]
        wide = pd.DataFrame(
            [[1.0, 2.0, 3.0, 4.0, 5.0]],
            index=pd.DatetimeIndex(["2024-01-03"], name="time"),
            columns=pd.Index([f"SYM{i}" for i in range(5)], name="symbol"),
        )
        out = winsorize_mad(wide, k=5.0, scale=1.4826)
        np.testing.assert_array_almost_equal(
            out.iloc[0].values, [1.0, 2.0, 3.0, 4.0, 5.0]
        )

    def test_symmetric_clipping(self) -> None:
        # [1,2,3,4,5,100,-100] — median=3, abs_dev=[2,1,0,1,2,97,103],
        # sorted=[0,1,1,2,2,97,103], MAD=median=2
        # half_width = k * 1.4826 * 2 = 2*k*1.4826
        # At k=1: half_width=2.9652, lower=0.0348, upper=5.9652
        wide = pd.DataFrame(
            [[1.0, 2.0, 3.0, 4.0, 5.0, 100.0, -100.0]],
            index=pd.DatetimeIndex(["2024-01-02"], name="time"),
            columns=pd.Index([f"SYM{i}" for i in range(7)], name="symbol"),
        )
        out = winsorize_mad(wide, k=1.0, scale=1.4826)
        row = out.iloc[0].values
        assert row.min() == pytest.approx(0.0348, abs=1e-3)
        assert row.max() == pytest.approx(5.9652, abs=1e-3)

    def test_nan_preserved(self) -> None:
        wide = pd.DataFrame(
            [[1.0, 2.0, np.nan, 4.0, 5.0]],
            index=pd.DatetimeIndex(["2024-01-02"], name="time"),
            columns=pd.Index([f"SYM{i}" for i in range(5)], name="symbol"),
        )
        out = winsorize_mad(wide, k=5.0, scale=1.4826)
        assert pd.isna(out.iloc[0, 2])


class TestZscoreCrossSection:
    def test_mean_zero_std_one_per_row(self) -> None:
        s = _make_factor_series(n_dates=20, n_stocks=50)
        wide = _to_wide(s)
        out = zscore_cross_section(wide)
        means = out.mean(axis=1, skipna=True)
        stds = out.std(axis=1, ddof=0, skipna=True)
        np.testing.assert_array_almost_equal(means.values, 0.0, decimal=10)
        np.testing.assert_array_almost_equal(stds.values, 1.0, decimal=10)

    def test_constant_row_collapses_to_zero(self) -> None:
        wide = pd.DataFrame(
            [[2.0, 2.0, 2.0, 2.0, 2.0]],
            index=pd.DatetimeIndex(["2024-01-02"], name="time"),
            columns=pd.Index([f"SYM{i}" for i in range(5)], name="symbol"),
        )
        out = zscore_cross_section(wide)
        assert (out.iloc[0] == 0.0).all()

    def test_nan_preserved(self) -> None:
        wide = pd.DataFrame(
            [[1.0, 2.0, np.nan, 4.0, 5.0]],
            index=pd.DatetimeIndex(["2024-01-02"], name="time"),
            columns=pd.Index([f"SYM{i}" for i in range(5)], name="symbol"),
        )
        out = zscore_cross_section(wide)
        assert pd.isna(out.iloc[0, 2])
        non_nan = out.iloc[0].dropna()
        assert non_nan.mean() == pytest.approx(0.0, abs=1e-10)


class TestPreprocessFactorPipeline:
    def test_end_to_end_preserves_shape(self) -> None:
        s = _make_factor_series(n_dates=30, n_stocks=20)
        cfg = PreprocessConfig(winsorize_mad_k=5.0, winsorize_mad_scale=1.4826)
        out = preprocess_factor(s, cfg)
        assert out.shape == s.shape
        assert out.index.equals(s.index)

    def test_zscore_true_recenters(self) -> None:
        s = _make_factor_series(n_dates=10, n_stocks=20)
        cfg = PreprocessConfig(zscore=True)
        out = preprocess_factor(s, cfg)
        wide = _to_wide(out)
        means = wide.mean(axis=1, skipna=True)
        np.testing.assert_array_almost_equal(means.values, 0.0, decimal=10)

    def test_zscore_disabled(self) -> None:
        s = _make_factor_series(n_dates=10, n_stocks=20)
        cfg = PreprocessConfig(zscore=False)
        out = preprocess_factor(s, cfg)
        wide = _to_wide(out)
        row_means = wide.mean(axis=1, skipna=True).abs()
        # Without z-score the row means are not forced to zero
        assert (row_means > 1e-6).any()

    def test_tradable_mask_filters(self) -> None:
        s = _make_factor_series(n_dates=5, n_stocks=4)
        mask = pd.Series(True, index=s.index, name="tradable")
        first_date = s.index.get_level_values("time")[0]
        mask.loc[(first_date, "SYM00")] = False

        cfg = PreprocessConfig()
        out = preprocess_factor(s, cfg, tradable_mask=mask)
        assert pd.isna(out.loc[(first_date, "SYM00")])

    def test_idempotent_on_already_clean(self) -> None:
        s = _make_factor_series(n_dates=20, n_stocks=30)
        cfg = PreprocessConfig()
        out1 = preprocess_factor(s, cfg)
        out2 = preprocess_factor(out1, cfg)
        pd.testing.assert_series_equal(out1, out2, atol=1e-10)
