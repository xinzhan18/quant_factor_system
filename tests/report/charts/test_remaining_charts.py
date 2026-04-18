import pandas as pd
import numpy as np
from report.charts.decay_charts import (
    chart_ic_decay, chart_factor_distribution, chart_coverage,
)
from report.charts.uniqueness_charts import chart_correlation_bar
from report.charts.composite_charts import chart_radar


def test_ic_decay():
    by_h = {
        1: {"validation": {"ic_mean": -0.049}},
        5: {"validation": {"ic_mean": -0.073}},
        10: {"validation": {"ic_mean": -0.083}},
        20: {"validation": {"ic_mean": -0.095}},
        60: {"validation": {"ic_mean": -0.107}},
    }
    fig = chart_ic_decay(by_h)
    assert fig.data
    # x axis monotonically increasing horizons
    assert list(fig.data[0].x) == sorted(fig.data[0].x)


def test_ic_decay_handles_string_keys():
    # YAML sometimes gives string keys for integer horizons
    by_h = {"1": {"validation": {"ic_mean": -0.049}},
            "5": {"validation": {"ic_mean": -0.073}}}
    fig = chart_ic_decay(by_h)
    assert fig.data


def test_factor_distribution():
    hist = pd.DataFrame({
        "bin_edge_lo": np.linspace(-3, 2.88, 50),
        "bin_edge_hi": np.linspace(-2.88, 3, 50),
        "is_freq": np.full(50, 1.0 / 50),
        "oos_freq": np.full(50, 1.0 / 50),
    })
    fig = chart_factor_distribution(hist)
    assert fig.data
    # overlay mode: two traces
    assert len(fig.data) == 2


def test_coverage():
    cov = pd.DataFrame({"coverage": [0.93, 0.95, 0.97]},
                      index=pd.date_range("2024-01-01", periods=3))
    fig = chart_coverage(cov)
    assert fig.data


def test_correlation_bar_sorts_by_abs():
    corrs = {"F001": 0.23, "F002": -0.17, "F003": 0.79, "F004": -0.05}
    fig = chart_correlation_bar(corrs)
    assert fig.data
    # top bar should be F003 (|0.79| is largest)
    assert fig.data[0].x[0] == "F003"


def test_correlation_bar_caps_at_40():
    corrs = {f"F{i:03d}": 0.1 + i * 0.01 for i in range(80)}
    fig = chart_correlation_bar(corrs)
    # capped
    assert len(fig.data[0].x) == 40


def test_radar():
    composite = {
        "predictive_power": 96.2, "signal_stability": 72.3,
        "profitability": 100.0, "monotonicity": 100.0,
        "oos_robustness": 60.3, "uniqueness": 0.0, "decay_resistance": 100.0,
        "score": 75.5, "grade": "A",
    }
    fig = chart_radar(composite)
    assert fig.data
    # Scatterpolar: r should have 8 points (7 dims + close-loop)
    assert len(fig.data[0].r) == 8
