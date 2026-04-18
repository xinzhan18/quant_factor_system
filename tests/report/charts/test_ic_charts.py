import pandas as pd
import numpy as np
from report.charts.ic_charts import (
    chart_ic_timeseries, chart_rolling_ic,
    chart_ic_distribution, chart_monthly_heatmap,
)


def _fake_ic_daily():
    dates = pd.date_range("2020-01-01", periods=600, freq="B")
    rng = np.random.default_rng(0)
    return pd.concat({
        "train": pd.DataFrame({"ic": rng.normal(-0.02, 0.1, 400)}, index=dates[:400]),
        "validation": pd.DataFrame({"ic": rng.normal(-0.05, 0.1, 200)}, index=dates[400:]),
    }, names=["split"])


def test_all_ic_charts_return_figure():
    ic = _fake_ic_daily()
    for fn in (chart_ic_timeseries, chart_rolling_ic,
               chart_ic_distribution, chart_monthly_heatmap):
        fig = fn(ic)
        assert fig is not None
        assert hasattr(fig, "data") and len(fig.data) > 0


def test_ic_timeseries_has_separate_traces_for_is_and_oos():
    ic = _fake_ic_daily()
    fig = chart_ic_timeseries(ic)
    trace_names = [getattr(t, "name", None) for t in fig.data]
    assert "Train" in trace_names or any("rain" in (n or "") for n in trace_names)
    assert "Validation" in trace_names or any("alid" in (n or "") for n in trace_names)


def test_ic_timeseries_has_cumulative_panel():
    ic = _fake_ic_daily()
    fig = chart_ic_timeseries(ic)
    trace_names = [getattr(t, "name", None) for t in fig.data]
    assert any("umulative" in (n or "") for n in trace_names)


def test_monthly_heatmap_shape():
    ic = _fake_ic_daily()
    fig = chart_monthly_heatmap(ic)
    z = fig.data[0].z
    assert len(z) >= 1


def test_charts_handle_empty_split():
    dates = pd.date_range("2020-01-01", periods=100, freq="B")
    rng = np.random.default_rng(1)
    ic = pd.concat({
        "train": pd.DataFrame({"ic": rng.normal(0, 0.1, 100)}, index=dates),
    }, names=["split"])
    for fn in (chart_ic_timeseries, chart_rolling_ic,
               chart_ic_distribution, chart_monthly_heatmap):
        fig = fn(ic)
        assert fig is not None
