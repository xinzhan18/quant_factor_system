"""Export daily primitive panels to Qlib day-bin feature files."""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np
import pandas as pd


class QlibDailyFeatureExporter:
    """Write daily primitive columns into a Qlib-compatible day directory."""

    def __init__(self, qlib_dir: str | Path) -> None:
        self.qlib_dir = Path(qlib_dir).expanduser()

    def export_panel(self, panel: pd.DataFrame, fields: list[str] | None = None) -> None:
        if panel.empty:
            return
        if not isinstance(panel.index, pd.MultiIndex):
            raise ValueError("export_panel expects MultiIndex(datetime, instrument)")

        df = panel.copy()
        df.index.names = ["datetime", "instrument"]
        fields = fields or list(df.columns)
        calendar = self._calendar(df)
        self._write_calendar(calendar)
        self._ensure_instruments(df, calendar)

        flat = df.reset_index()
        flat["date"] = pd.to_datetime(flat["datetime"]).dt.strftime("%Y-%m-%d")
        for symbol, grp in flat.groupby("instrument"):
            self._write_symbol(str(symbol), grp, fields, calendar)

    def _calendar(self, df: pd.DataFrame) -> list[str]:
        cal_path = self.qlib_dir / "calendars" / "day.txt"
        if cal_path.exists():
            existing = [x for x in cal_path.read_text().splitlines() if x.strip()]
        else:
            existing = []
        dates = sorted(
            pd.to_datetime(df.index.get_level_values("datetime"))
            .strftime("%Y-%m-%d")
            .unique()
            .tolist()
        )
        return sorted(set(existing) | set(dates))

    def _write_calendar(self, calendar: list[str]) -> None:
        path = self.qlib_dir / "calendars" / "day.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(calendar) + "\n", encoding="utf-8")

    def _ensure_instruments(self, df: pd.DataFrame, calendar: list[str]) -> None:
        inst_path = self.qlib_dir / "instruments" / "all.txt"
        inst_path.parent.mkdir(parents=True, exist_ok=True)
        symbols = sorted(str(s) for s in df.index.get_level_values("instrument").unique())
        start = calendar[0]
        end = calendar[-1]
        if inst_path.exists():
            existing = {line.split("\t")[0]: line for line in inst_path.read_text().splitlines() if line.strip()}
        else:
            existing = {}
        for sym in symbols:
            existing[sym] = f"{sym}\t{start}\t{end}"
        inst_path.write_text("\n".join(existing[s] for s in sorted(existing)) + "\n", encoding="utf-8")

    def _write_symbol(
        self,
        symbol: str,
        data: pd.DataFrame,
        fields: list[str],
        calendar: list[str],
    ) -> None:
        sym_dir = self.qlib_dir / "features" / symbol
        sym_dir.mkdir(parents=True, exist_ok=True)
        data = data.set_index("date")
        for field in fields:
            if field not in data.columns:
                continue
            values: list[float] = []
            for day in calendar:
                if day in data.index:
                    row = data.loc[day]
                    if isinstance(row, pd.DataFrame):
                        row = row.iloc[0]
                    val = row[field]
                    values.append(float(val) if not pd.isna(val) else float("nan"))
                else:
                    values.append(float("nan"))
            self._write_bin(sym_dir / f"{field}.day.bin", values)

    @staticmethod
    def _write_bin(path: Path, values: list[float]) -> None:
        start_idx = 0
        for i, value in enumerate(values):
            if not np.isnan(value):
                start_idx = i
                break
        with open(path, "wb") as f:
            f.write(struct.pack("<f", float(start_idx)))
            for value in values[start_idx:]:
                f.write(struct.pack("<f", float(value)))

