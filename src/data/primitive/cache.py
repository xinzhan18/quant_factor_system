"""Parquet cache for materialized daily primitive values."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from data.primitive.schema import PrimitiveSpec


class PrimitiveCache:
    """Read/write final daily primitive values."""

    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def cache_file(self, spec: PrimitiveSpec) -> Path:
        return (
            self.root
            / f"feature_id={spec.feature_id}"
            / f"spec_hash={spec.spec_hash}"
            / "values.parquet"
        )

    def get(self, spec: PrimitiveSpec, start: str, end: str) -> pd.DataFrame | None:
        path = self.cache_file(spec)
        if not path.exists():
            return None
        df = pd.read_parquet(path)
        if df.empty:
            return None
        df = _ensure_mi(df)
        dt = df.index.get_level_values("datetime")
        start_ts = pd.Timestamp(start)
        end_ts = pd.Timestamp(end)
        if dt.min() > start_ts or dt.max() < end_ts:
            return None
        mask = (dt >= start_ts) & (dt <= end_ts)
        return df.loc[mask, [spec.feature_id]]

    def put(self, spec: PrimitiveSpec, values: pd.DataFrame) -> Path:
        path = self.cache_file(spec)
        path.parent.mkdir(parents=True, exist_ok=True)
        df = _ensure_mi(values)
        if spec.feature_id not in df.columns:
            raise ValueError(f"cache put missing column: {spec.feature_id}")
        df[[spec.feature_id]].to_parquet(path)
        return path


def _ensure_mi(df: pd.DataFrame) -> pd.DataFrame:
    if isinstance(df.index, pd.MultiIndex):
        out = df.copy()
        out.index.names = ["datetime", "instrument"]
        return out.sort_index()
    required = {"datetime", "instrument"}
    if required.issubset(df.columns):
        out = df.copy()
        out["datetime"] = pd.to_datetime(out["datetime"])
        return out.set_index(["datetime", "instrument"]).sort_index()
    if {"date", "symbol"}.issubset(df.columns):
        out = df.copy()
        out["datetime"] = pd.to_datetime(out["date"])
        out["instrument"] = out["symbol"]
        return out.set_index(["datetime", "instrument"]).sort_index()
    raise ValueError("primitive cache expects MultiIndex or datetime/instrument columns")

