from report.charts.risk_charts import chart_style_exposure_bar, chart_alpha_waterfall
from report.charts.stability_charts import chart_support_window_ic, chart_stability_summary


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
    # x axis should list the 5 styles
    assert set(fig.data[0].x) == set(barra["style_exposures"])


def test_alpha_waterfall_two_stages():
    barra = {"barra_residual_ic": -0.026, "alpha_survival_ratio": 0.364}
    fig = chart_alpha_waterfall(-0.065, barra)
    assert fig.data
    # bar chart with 2 bars: raw, residual
    assert len(fig.data[0].y) == 2


def test_support_window_ic():
    stab = {
        "split_ic_means": [-0.48, -0.54, -0.52, -0.50],
        "sign_consistency": 1.0,
        "dispersion": 0.08,
    }
    fig = chart_support_window_ic(stab)
    assert fig.data
    assert len(fig.data[0].y) == 4


def test_stability_summary():
    candidate = {
        "ic": {"train_validation_decay": 1.09},
        "stability": {"split_stability": {"sign_consistency": 1.0, "dispersion": 0.08}},
    }
    fig = chart_stability_summary(candidate)
    assert fig.data
    # 3 rows: IS→Val decay, Sign consistency, Dispersion
    assert len(fig.data[0].y) == 3


def test_alpha_waterfall_handles_missing_residual():
    # If barra_residual_ic not populated, fall back to raw IC (no crash)
    fig = chart_alpha_waterfall(-0.065, {})
    assert fig.data


def test_support_window_ic_handles_empty_list():
    fig = chart_support_window_ic({"split_ic_means": []})
    assert fig is not None  # no crash, even if empty
