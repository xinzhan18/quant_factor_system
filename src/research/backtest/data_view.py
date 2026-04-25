"""PriceView — wraps the OHLCV+limit_up/down parquet for date/symbol slicing.

The parquet is expected to have a MultiIndex ``(datetime, instrument)``.
Column names with leading ``$`` (qlib-style) are normalized by stripping the
sigil at load time, so callers see plain ``open``/``close``/etc.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class PriceView:
    _df: pd.DataFrame

    @classmethod
    def from_parquet(cls, path: str | Path) -> "PriceView":
        df = pd.read_parquet(path)
        df.columns = [c.lstrip("$") for c in df.columns]
        if df.index.nlevels != 2:
            raise ValueError(
                f"PriceView expects MultiIndex(datetime, instrument); "
                f"got {df.index.nlevels} levels"
            )
        return cls(_df=df)

    @classmethod
    def from_dataframe(cls, df: pd.DataFrame) -> "PriceView":
        df = df.copy()
        df.columns = [c.lstrip("$") for c in df.columns]
        return cls(_df=df)

    @property
    def snapshot_ts(self) -> datetime:
        return self._df.index.get_level_values(0).max().to_pydatetime()

    def slice_eod(self, dt: date, symbols: list[str]) -> pd.DataFrame:
        try:
            day = self._df.xs(pd.Timestamp(dt), level=0)
        except KeyError:
            return pd.DataFrame(columns=self._df.columns)
        present = [s for s in symbols if s in day.index]
        return day.loc[present]

    def slice_panel(
        self, start: date, end: date, symbols: list[str]
    ) -> pd.DataFrame:
        s, e = pd.Timestamp(start), pd.Timestamp(end)
        idx = self._df.index
        mask = (idx.get_level_values(0) >= s) & (idx.get_level_values(0) <= e)
        sub = self._df[mask]
        sub = sub[sub.index.get_level_values(1).isin(symbols)]
        return sub
