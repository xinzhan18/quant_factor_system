"""Batch materializer for minute-bar derived daily primitives.

V0 intentionally supports a small fixed template set and uses pandas only,
because the repository does not currently depend on Polars/DuckDB.
"""

from __future__ import annotations

from datetime import time
from typing import Callable

import numpy as np
import pandas as pd

from data.primitive.schema import PrimitiveSpec

MinuteDataLoader = Callable[[str, str, list[str]], pd.DataFrame]


class MinuteMaterializer:
    """Materialize multiple minute primitive specs in one minute-data load."""

    BASE_COLUMNS = ["time", "symbol", "open", "high", "low", "close", "volume", "amount"]

    def __init__(self, loader: MinuteDataLoader) -> None:
        self.loader = loader

    def materialize_many(
        self,
        specs: list[PrimitiveSpec],
        start: str,
        end: str,
    ) -> pd.DataFrame:
        if not specs:
            return pd.DataFrame()
        df = self.loader(start, end, self.BASE_COLUMNS)
        if df.empty:
            return _empty_panel([s.feature_id for s in specs])
        base = _prepare_minute_frame(df)

        outputs: list[pd.DataFrame] = []
        for spec in specs:
            outputs.append(self._materialize_one(base, spec))

        panel = pd.concat(outputs, axis=1).sort_index()
        panel.index.names = ["datetime", "instrument"]
        return panel

    def _materialize_one(self, df: pd.DataFrame, spec: PrimitiveSpec) -> pd.DataFrame:
        template = spec.template
        if template == "window_return":
            return _window_return(df, spec)
        if template == "window_share":
            return _window_share(df, spec)
        if template == "distribution_stats":
            return _distribution_stats(df, spec)
        if template == "masked_return_mean":
            return _masked_return_mean(df, spec)
        if template == "price_volume_corr":
            return _price_volume_corr(df, spec)
        raise ValueError(f"unsupported primitive template: {template}")


def _prepare_minute_frame(df: pd.DataFrame) -> pd.DataFrame:
    required = {"time", "symbol"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"minute frame missing columns: {sorted(missing)}")
    out = df.copy()
    out["time"] = pd.to_datetime(out["time"])
    out["date"] = out["time"].dt.normalize()
    out["tod"] = out["time"].dt.time
    out = out.sort_values(["symbol", "time"])
    if "close" in out.columns:
        out["ret_1m"] = out.groupby(["symbol", "date"])["close"].pct_change()
    return out


def _parse_time(value: str) -> time:
    hour, minute = value.split(":")[:2]
    return time(int(hour), int(minute))


def _window_mask(df: pd.DataFrame, window: str) -> pd.Series:
    start_s, end_s = window.split("-")
    start_t = _parse_time(start_s)
    end_t = _parse_time(end_s)
    return (df["tod"] >= start_t) & (df["tod"] <= end_t)


def _to_panel(df: pd.DataFrame, feature_id: str) -> pd.DataFrame:
    if df.empty:
        return _empty_panel([feature_id])
    out = df.rename(columns={"date": "datetime", "symbol": "instrument"})
    out["datetime"] = pd.to_datetime(out["datetime"])
    return out.set_index(["datetime", "instrument"])[[feature_id]].sort_index()


def _empty_panel(columns: list[str]) -> pd.DataFrame:
    idx = pd.MultiIndex.from_tuples([], names=["datetime", "instrument"])
    return pd.DataFrame(columns=columns, index=idx, dtype=float)


def _window_return(df: pd.DataFrame, spec: PrimitiveSpec) -> pd.DataFrame:
    window = spec.params["window"]
    min_obs = int(spec.data_policy.get("min_bars", spec.data_policy.get("min_obs", 1)))
    w = df.loc[_window_mask(df, window)].copy()
    if w.empty:
        return _empty_panel([spec.feature_id])
    grp = w.groupby(["date", "symbol"], sort=True)
    agg = grp.agg(
        first_open=("open", "first"),
        last_close=("close", "last"),
        n_bars=("close", "count"),
    ).reset_index()
    value = agg["last_close"] / agg["first_open"] - 1
    agg[spec.feature_id] = np.where(
        (agg["n_bars"] >= min_obs) & (agg["first_open"] > 0),
        value,
        np.nan,
    )
    return _to_panel(agg[["date", "symbol", spec.feature_id]], spec.feature_id)


def _window_share(df: pd.DataFrame, spec: PrimitiveSpec) -> pd.DataFrame:
    field = spec.params["field"]
    numerator_window = spec.params["numerator_window"]
    denominator_window = spec.params["denominator_window"]
    num = (
        df.loc[_window_mask(df, numerator_window)]
        .groupby(["date", "symbol"], sort=True)[field]
        .sum()
        .rename("num")
    )
    den = (
        df.loc[_window_mask(df, denominator_window)]
        .groupby(["date", "symbol"], sort=True)[field]
        .sum()
        .rename("den")
    )
    agg = pd.concat([num, den], axis=1).reset_index()
    agg[spec.feature_id] = np.where(agg["den"] > 0, agg["num"] / agg["den"], np.nan)
    return _to_panel(agg[["date", "symbol", spec.feature_id]], spec.feature_id)


def _distribution_stats(df: pd.DataFrame, spec: PrimitiveSpec) -> pd.DataFrame:
    series = spec.params.get("series", "ret_1m")
    stat = spec.params["stat"]
    window = spec.params.get("window")
    w = df.loc[_window_mask(df, window)].copy() if window else df.copy()
    if series == "volume_share":
        total = w.groupby(["date", "symbol"])["volume"].transform("sum")
        w["volume_share"] = np.where(total > 0, w["volume"] / total, np.nan)
    if series == "amount_share":
        total = w.groupby(["date", "symbol"])["amount"].transform("sum")
        w["amount_share"] = np.where(total > 0, w["amount"] / total, np.nan)

    grp = w.groupby(["date", "symbol"], sort=True)[series]
    if stat == "std":
        agg = grp.std().reset_index(name=spec.feature_id)
    elif stat == "skew":
        agg = grp.skew().reset_index(name=spec.feature_id)
    elif stat == "kurt":
        agg = grp.apply(pd.Series.kurt).reset_index(name=spec.feature_id)
    elif stat == "hhi":
        agg = grp.apply(lambda s: float(np.nansum(np.square(s)))).reset_index(
            name=spec.feature_id
        )
    else:
        raise ValueError(f"unsupported distribution stat: {stat}")
    return _to_panel(agg, spec.feature_id)


def _masked_return_mean(df: pd.DataFrame, spec: PrimitiveSpec) -> pd.DataFrame:
    window = spec.params.get("window")
    w = df.loc[_window_mask(df, window)].copy() if window else df.copy()
    volume_filter = spec.params.get("volume_filter", "none")
    if volume_filter == "mean_plus_std":
        grp = w.groupby(["date", "symbol"])["volume"]
        vol_mean = grp.transform("mean")
        vol_std = grp.transform("std").fillna(0)
        mask = w["volume"] > (vol_mean + vol_std)
    elif volume_filter == "none":
        mask = pd.Series(True, index=w.index)
    else:
        raise ValueError(f"unsupported volume_filter: {volume_filter}")

    ret_sign = spec.params.get("ret_sign")
    if ret_sign == "positive":
        mask &= w["ret_1m"] > 0
    elif ret_sign == "negative":
        mask &= w["ret_1m"] < 0
    elif ret_sign not in (None, "any"):
        raise ValueError(f"unsupported ret_sign: {ret_sign}")

    direction = spec.params.get("direction", "raw")
    agg = (
        w.loc[mask]
        .groupby(["date", "symbol"], sort=True)["ret_1m"]
        .mean()
        .reset_index(name=spec.feature_id)
    )
    if direction == "negative":
        agg[spec.feature_id] = -agg[spec.feature_id]
    elif direction != "raw":
        raise ValueError(f"unsupported direction: {direction}")
    return _to_panel(agg, spec.feature_id)


def _price_volume_corr(df: pd.DataFrame, spec: PrimitiveSpec) -> pd.DataFrame:
    x = spec.params.get("x", "ret_1m")
    y = spec.params.get("y", "amount")
    window = spec.params.get("window")
    w = df.loc[_window_mask(df, window)].copy() if window else df.copy()
    corr = (
        w.groupby(["date", "symbol"], sort=True)
        .apply(lambda g: g[x].corr(g[y]))
        .reset_index(name=spec.feature_id)
    )
    return _to_panel(corr, spec.feature_id)

