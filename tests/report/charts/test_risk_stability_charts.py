from report.charts.risk_charts import chart_style_exposure_bar, chart_alpha_waterfall
from report.charts.stability_charts import chart_stability_panel


def test_style_exposure_bar():
    barra = {
        "style_exposures": {
            "log_circ_cap": 0.05, "str_1m": 0.32,
            "vol_20d": 0.27, "turnover_20d": 0.29, "ep_ratio": 0.08,
        },
        "style_r_squared": 0.335,
        "barra_residual_ic": -0.026,
        "alpha_survival_ratio": 0.364,
    }
    fig = chart_style_exposure_bar(barra)
    assert fig.data
    assert set(fig.data[0].x) == set(barra["style_exposures"])


def test_alpha_waterfall_two_stages():
    barra = {"barra_residual_ic": -0.026, "alpha_survival_ratio": 0.364}
    fig = chart_alpha_waterfall(-0.065, barra)
    assert fig.data
    assert len(fig.data[0].y) == 2


def test_stability_panel_has_both_subplots():
    candidate = {
        "ic": {"train_validation_decay": 1.09},
        "stability": {"split_stability": {
            "split_ic_means": [-0.48, -0.54, -0.52, -0.50],
            "sign_consistency": 1.0,
            "dispersion": 0.08,
        }},
    }
    fig = chart_stability_panel(candidate)
    # two bar traces: left = 4 windows, right = 3 summary metrics
    assert len(fig.data) == 2
    assert len(fig.data[0].y) == 4
    assert len(fig.data[1].y) == 3


def test_stability_panel_handles_empty_windows():
    candidate = {"ic": {}, "stability": {"split_stability": {"split_ic_means": []}}}
    fig = chart_stability_panel(candidate)
    assert fig is not None  # no crash


def test_alpha_waterfall_handles_missing_residual():
    # With no residual / no contributions → 2-stage bar fallback
    fig = chart_alpha_waterfall(-0.065, {})
    assert fig.data
    assert fig.data[0].type == "bar"


def test_alpha_waterfall_uses_style_contributions():
    barra = {
        "barra_residual_ic": -0.010,
        "alpha_survival_ratio": 0.25,
        "style_contributions": [
            {"style": "vol_20d", "delta_ic": 0.025, "pct": 83.3, "ic_without": -0.035},
            {"style": "turnover_20d", "delta_ic": 0.004, "pct": 13.3, "ic_without": -0.014},
            {"style": "log_circ_cap", "delta_ic": 0.001, "pct": 3.3, "ic_without": -0.011},
        ],
    }
    fig = chart_alpha_waterfall(-0.040, barra)
    assert fig.data
    trace = fig.data[0]
    assert trace.type == "waterfall"
    # Raw + 3 styles + (maybe joint) + Residual
    assert len(trace.x) >= 5
    # First is Raw absolute, last is Residual total
    assert "Raw" in trace.x[0]
    assert "Residual" in trace.x[-1]
    # Measures: first absolute, last total
    assert trace.measure[0] == "absolute"
    assert trace.measure[-1] == "total"


def test_alpha_waterfall_ignores_none_delta_contributions():
    barra = {
        "barra_residual_ic": -0.01,
        "style_contributions": [
            {"style": "vol_20d", "delta_ic": 0.02, "pct": 80.0, "ic_without": -0.03},
            {"style": "bad_style", "delta_ic": None, "pct": None, "ic_without": None},
        ],
    }
    fig = chart_alpha_waterfall(-0.04, barra)
    # Only the non-None contribution drives a drop bar
    labels = list(fig.data[0].x)
    assert any("vol_20d" in lbl for lbl in labels)
    assert not any("bad_style" in lbl for lbl in labels)
