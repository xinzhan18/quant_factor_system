from __future__ import annotations

import pandas as pd

from research.compute.daily_python_backend import run_daily_python_candidate


def _market() -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=5)
    symbols = ["AAA"]
    idx = pd.MultiIndex.from_product([dates, symbols], names=["datetime", "instrument"])
    close = pd.Series([10, 11, 12, 13, 14], index=idx, dtype=float)
    return pd.DataFrame(
        {
            "$close": close,
            "$high": close + 1,
            "$low": close - 1,
        }
    )


def test_run_daily_python_quantile_split_candidate() -> None:
    candidate = {
        "candidate_id": "C001",
        "source_type": "daily_python",
        "factor_logic": {
            "backend": "daily_python",
            "template": "quantile_split_spread",
            "params": {
                "value": {"expression": "Sub(Div($high,$low),1)"},
                "sorter": {"field": "$close"},
                "window": 3,
                "top_quantile": 1 / 3,
                "bottom_quantile": 1 / 3,
                "min_count": 1,
            },
        },
    }

    out = run_daily_python_candidate(
        candidate,
        _market(),
        start="2024-01-02",
        end="2024-01-08",
    )

    assert out.name == "C001"
    assert out.notna().sum() == 3
