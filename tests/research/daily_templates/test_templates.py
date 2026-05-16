from __future__ import annotations

import numpy as np
import pandas as pd

from research.daily_templates import run_template
from research.daily_templates.expression import evaluate_expression


def _panel() -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=6)
    symbols = ["AAA", "BBB"]
    idx = pd.MultiIndex.from_product([dates, symbols], names=["datetime", "instrument"])
    rows = []
    for date_pos, _ in enumerate(dates):
        for sym in symbols:
            offset = 0 if sym == "AAA" else 10
            close = 10.0 + date_pos + offset
            rows.append(
                {
                    "$close": close,
                    "$high": close + 1.0,
                    "$low": close - 1.0,
                    "$turnover_rate": float(date_pos + 1),
                }
            )
    return pd.DataFrame(rows, index=idx)


def test_evaluate_prefix_expression() -> None:
    df = _panel()
    out = evaluate_expression({"expression": "Sub(Div($high,$low),1)"}, df)
    expected = df["$high"] / df["$low"] - 1
    pd.testing.assert_series_equal(out, expected, check_names=False)


def test_quantile_split_spread_matches_manual_last_window() -> None:
    df = _panel()
    out = run_template(
        "quantile_split_spread",
        df,
        {
            "value": {"expression": "Sub(Div($high,$low),1)"},
            "sorter": {"field": "$close"},
            "window": 4,
            "top_quantile": 0.25,
            "bottom_quantile": 0.25,
            "min_count": 1,
        },
    )

    aaa = df.xs("AAA", level="instrument")
    last = aaa.iloc[-4:]
    value = last["$high"] / last["$low"] - 1
    sorter = last["$close"]
    top = value[sorter >= np.nanquantile(sorter, 0.75)].mean()
    bottom = value[sorter <= np.nanquantile(sorter, 0.25)].mean()
    assert np.isclose(out.loc[(aaa.index[-1], "AAA")], top - bottom)


def test_conditional_rolling_mean() -> None:
    df = _panel()
    out = run_template(
        "conditional_rolling_mean",
        df,
        {
            "value": {"field": "$close"},
            "condition": {"expression": "Gt($turnover_rate,3)"},
            "window": 3,
            "min_count": 1,
        },
    )

    # For AAA on the final date, the last 3 closes are 13,14,15 and all
    # pass turnover > 3, so the conditional mean is 14.
    last_date = df.index.get_level_values(0).unique()[-1]
    assert np.isclose(out.loc[(last_date, "AAA")], 14.0)
