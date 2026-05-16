from __future__ import annotations

import pandas as pd

from research.compute.data_bridge import evaluate_candidates


def _market() -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-02", periods=5)
    idx = pd.MultiIndex.from_product(
        [dates, ["AAA"]], names=["datetime", "instrument"]
    )
    close = pd.Series([10, 11, 12, 13, 14], index=idx, dtype=float)
    return pd.DataFrame(
        {
            "$close": close,
            "$high": close + 1,
            "$low": close - 1,
        }
    )


def test_evaluate_candidates_runs_daily_python_template() -> None:
    market = _market()
    manifest = {
        "candidates": [
            {
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
        ]
    }

    out = evaluate_candidates(
        manifest,
        market_df=market,
        base_tradable_mask=pd.Series(True, index=market.index),
        start="2024-01-02",
        end="2024-01-08",
    )

    assert len(out) == 1
    cand = out[0]
    assert cand.source_type == "daily_python"
    assert cand.factor_backend == "daily_python"
    assert cand.factor_series.notna().sum() == 3
