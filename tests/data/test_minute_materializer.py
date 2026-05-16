from __future__ import annotations

import numpy as np
import pandas as pd

from data.materializers import MinuteMaterializer
from data.primitive.schema import PrimitiveSpec


def _minute_frame() -> pd.DataFrame:
    rows = []
    times = list(pd.date_range("2024-01-02 09:30", periods=31, freq="1min"))
    times += list(pd.date_range("2024-01-02 14:40", periods=21, freq="1min"))
    for i, ts in enumerate(times):
        rows.append(
            {
                "time": ts,
                "symbol": "SH600000",
                "open": 10.0 + i * 0.01,
                "high": 10.1 + i * 0.01,
                "low": 9.9 + i * 0.01,
                "close": 10.0 + i * 0.02,
                "volume": 100.0 + i,
                "amount": 1000.0 + 10 * i,
            }
        )
    return pd.DataFrame(rows)


def _spec(feature_id: str, template: str, params: dict, data_policy: dict | None = None):
    return PrimitiveSpec.from_dict(
        {
            "feature_id": feature_id,
            "source_type": "minute_bar",
            "source_freq": "1min",
            "output_freq": "daily",
            "template": template,
            "params": params,
            "data_policy": data_policy or {},
        }
    )


def test_materialize_window_return_and_share() -> None:
    data = _minute_frame()

    def loader(start, end, columns):
        return data[columns]

    specs = [
        _spec(
            "open_10m_ret_v1",
            "window_return",
            {"window": "09:30-09:40"},
            {"min_bars": 8},
        ),
        _spec(
            "tail_amount_share_20m_v1",
            "window_share",
            {
                "field": "amount",
                "numerator_window": "14:40-15:00",
                "denominator_window": "09:30-15:00",
            },
        ),
    ]
    panel = MinuteMaterializer(loader).materialize_many(
        specs, "2024-01-02", "2024-01-02"
    )

    idx = (pd.Timestamp("2024-01-02"), "SH600000")
    expected_ret = data.loc[10, "close"] / data.loc[0, "open"] - 1
    assert panel.loc[idx, "open_10m_ret_v1"] == expected_ret

    tail_sum = data.loc[data["time"].dt.time >= pd.Timestamp("14:40").time(), "amount"].sum()
    full_sum = data["amount"].sum()
    assert panel.loc[idx, "tail_amount_share_20m_v1"] == tail_sum / full_sum


def test_materialize_distribution_and_masked_return() -> None:
    data = _minute_frame()
    data.loc[5, "volume"] = 10000.0
    data.loc[5, "close"] = data.loc[4, "close"] * 1.02

    def loader(start, end, columns):
        return data[columns]

    specs = [
        _spec(
            "intraday_vol_v1",
            "distribution_stats",
            {"series": "ret_1m", "stat": "std", "window": "09:30-15:00"},
        ),
        _spec(
            "reverse_imp_pos_v1",
            "masked_return_mean",
            {
                "window": "09:30-15:00",
                "ret_sign": "positive",
                "volume_filter": "mean_plus_std",
                "direction": "negative",
            },
        ),
    ]
    panel = MinuteMaterializer(loader).materialize_many(
        specs, "2024-01-02", "2024-01-02"
    )

    idx = (pd.Timestamp("2024-01-02"), "SH600000")
    assert np.isfinite(panel.loc[idx, "intraday_vol_v1"])
    assert panel.loc[idx, "reverse_imp_pos_v1"] < 0

