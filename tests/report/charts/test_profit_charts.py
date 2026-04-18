import pandas as pd
import numpy as np
from report.charts.profit_charts import (
    chart_quintile_bar, chart_quintile_returns_oos,
    chart_cumulative_returns, chart_long_short, chart_annual_group_returns,
)


def _fake_qdaily(n=200, seed=1):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2020-01-01", periods=n, freq="B")
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
    q_val = _fake_qdaily(n=50, seed=3)
    ls = _fake_ls()
    assert chart_quintile_bar(q_train, q_val).data
    assert chart_quintile_returns_oos(q_val).data
    assert chart_cumulative_returns(q_train, q_val).data
    assert chart_long_short(ls).data
    assert chart_annual_group_returns(q_train, q_val).data


def test_cumulative_returns_has_five_traces():
    q_train = _fake_qdaily()
    q_val = _fake_qdaily(n=50, seed=3)
    fig = chart_cumulative_returns(q_train, q_val)
    # one trace per quintile
    assert len(fig.data) == 5


def test_long_short_handles_missing_validation_split():
    tr_idx = pd.date_range("2020-01-01", periods=100, freq="B")
    rng = np.random.default_rng(0)
    ls = pd.concat({"train": pd.DataFrame({"long_short": rng.normal(0, 0.01, 100)}, index=tr_idx)},
                    names=["split"])
    fig = chart_long_short(ls)
    assert fig.data  # no crash


def test_annual_group_returns_shape():
    q_train = _fake_qdaily(n=500)  # 2 years worth
    q_val = _fake_qdaily(n=50, seed=3)
    fig = chart_annual_group_returns(q_train, q_val)
    # heatmap z: year × quintile (5 cols)
    z = fig.data[0].z
    assert len(z) >= 1
    assert len(z[0]) == 5
