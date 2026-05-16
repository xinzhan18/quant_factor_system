import pandas as pd
import numpy as np
from report.charts.profit_charts import (
    chart_quintile_bar, chart_cumulative_returns, chart_annual_group_returns,
    chart_long_short_cumulative,
)


def _fake_qdaily(n=200, seed=1, start="2020-01-01"):
    rng = np.random.default_rng(seed)
    idx = pd.date_range(start, periods=n, freq="B")
    return pd.DataFrame(rng.normal(0, 0.01, (n, 5)),
                        columns=[f"q{i}" for i in range(1, 6)], index=idx)


def _fake_ls(seed=2):
    rng = np.random.default_rng(seed)
    tr_idx = pd.date_range("2020-01-01", periods=200, freq="B")
    val_idx = pd.date_range("2024-01-01", periods=50, freq="B")
    tr = pd.DataFrame({"long_short": rng.normal(0.002, 0.01, 200)}, index=tr_idx)
    val = pd.DataFrame({"long_short": rng.normal(0.003, 0.01, 50)}, index=val_idx)
    return pd.concat({"train": tr, "validation": val}, names=["split"])


def test_all_profit_charts_return_figure():
    q_train = _fake_qdaily()
    q_val = _fake_qdaily(n=50, seed=3, start="2023-01-01")
    ls = _fake_ls()
    assert chart_quintile_bar(q_train, q_val).data
    assert chart_cumulative_returns(q_train, q_val).data
    assert chart_long_short_cumulative(ls, q_train, q_val).data
    assert chart_annual_group_returns(q_train, q_val).data


def test_cumulative_returns_has_five_quintile_traces_no_ls():
    """L/S is now a separate chart — cumulative_returns shows only Q1-Q5."""
    q_train = _fake_qdaily()
    q_val = _fake_qdaily(n=50, seed=3, start="2023-01-01")
    fig = chart_cumulative_returns(q_train, q_val)
    assert len(fig.data) == 5
    names = [getattr(t, "name", "") or "" for t in fig.data]
    assert not any("L/S" in n for n in names)


def test_cumulative_returns_with_holdout_still_five_traces():
    q_train = _fake_qdaily()
    q_val = _fake_qdaily(n=50, seed=3, start="2023-01-01")
    q_holdout = _fake_qdaily(n=80, seed=5, start="2024-01-01")
    fig = chart_cumulative_returns(q_train, q_val, q_holdout)
    assert len(fig.data) == 5  # still 5 quintile lines, regions are shapes/annotations


def test_long_short_cumulative_handles_holdout_and_missing_val():
    q_train = _fake_qdaily()
    q_val = _fake_qdaily(n=50, seed=3, start="2023-01-01")
    q_holdout = _fake_qdaily(n=80, seed=5, start="2024-01-01")
    ls = _fake_ls()
    fig = chart_long_short_cumulative(ls, q_train, q_val, q_holdout)
    names = [getattr(t, "name", "") or "" for t in fig.data]
    assert any("L/S" in n for n in names)
    # missing val split must not crash
    tr_idx = pd.date_range("2020-01-01", periods=100, freq="B")
    rng = np.random.default_rng(0)
    ls_train_only = pd.concat(
        {"train": pd.DataFrame({"long_short": rng.normal(0, 0.01, 100)}, index=tr_idx)},
        names=["split"],
    )
    fig2 = chart_long_short_cumulative(ls_train_only, q_train, q_val)
    assert fig2.data  # no crash


def test_quintile_bar_holdout_adds_third_group():
    q_train = _fake_qdaily()
    q_val = _fake_qdaily(n=50, seed=3, start="2023-01-01")
    q_holdout = _fake_qdaily(n=80, seed=5, start="2024-01-01")
    fig_no_holdout = chart_quintile_bar(q_train, q_val)
    fig_with_holdout = chart_quintile_bar(q_train, q_val, q_holdout)
    assert len(fig_no_holdout.data) == 2
    assert len(fig_with_holdout.data) == 3


def test_annual_group_returns_shape():
    q_train = _fake_qdaily(n=500)
    q_val = _fake_qdaily(n=50, seed=3, start="2023-01-01")
    fig = chart_annual_group_returns(q_train, q_val)
    z = fig.data[0].z
    assert len(z) >= 1
    assert len(z[0]) == 5
