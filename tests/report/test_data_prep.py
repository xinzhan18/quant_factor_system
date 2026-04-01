import pandas as pd
import numpy as np
import pytest
from report.data_prep import merge_factor_price, split_is_oos


def _make_factor_df(n_dates=20, n_stocks=5):
    dates = pd.bdate_range("2023-01-01", periods=n_dates)
    rows = []
    for d in dates:
        for s in [f"S{i:03d}" for i in range(n_stocks)]:
            rows.append({"time": d, "symbol": s, "value": np.random.randn()})
    return pd.DataFrame(rows)


def _make_price_df(n_dates=20, n_stocks=5):
    dates = pd.bdate_range("2023-01-01", periods=n_dates)
    rows = []
    for d in dates:
        for s in [f"S{i:03d}" for i in range(n_stocks)]:
            rows.append({"time": d, "symbol": s, "close": 10 + np.random.randn()})
    return pd.DataFrame(rows)


class TestMergeFactorPrice:
    def test_basic_merge(self):
        fdf = _make_factor_df()
        pdf = _make_price_df()
        merged = merge_factor_price(fdf, pdf)
        assert "value" in merged.columns
        assert "future_return" in merged.columns
        assert not merged["future_return"].isna().any()
        assert len(merged) < len(fdf)

    def test_mad_clip(self):
        fdf = _make_factor_df(n_dates=50)
        pdf = _make_price_df(n_dates=50)
        pdf.loc[pdf.index[5], "close"] = 1000.0
        merged = merge_factor_price(fdf, pdf, clip_method="mad", clip_k=5)
        assert merged["future_return"].dropna().abs().max() < 1.0

    def test_fixed_clip(self):
        fdf = _make_factor_df(n_dates=50)
        pdf = _make_price_df(n_dates=50)
        merged = merge_factor_price(fdf, pdf, clip_method="fixed", clip_threshold=0.11)
        assert (merged["future_return"].dropna().abs() <= 0.11).all()


class TestSplitIsOos:
    def test_split(self):
        fdf = _make_factor_df(n_dates=100)
        pdf = _make_price_df(n_dates=100)
        merged = merge_factor_price(fdf, pdf)
        split_date = merged["time"].quantile(0.7)
        is_df, oos_df = split_is_oos(merged, split_date)
        assert len(is_df) > 0
        assert len(oos_df) > 0
        assert is_df["time"].max() < oos_df["time"].min()
