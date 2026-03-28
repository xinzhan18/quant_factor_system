"""Data synchronization: TimescaleDB -> Qlib binary format."""

from __future__ import annotations

import logging
import struct
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class DataSynchronizer:
    """Sync TimescaleDB data to Qlib-compatible format.

    Creates the directory structure that Qlib expects:
      qlib_dir/
        calendars/day.txt
        instruments/all.txt
        features/<SYMBOL>/<field>.day.bin
    """

    FIELDS = ["open", "high", "low", "close", "volume", "amount"]
    AUX_FIELDS = ["limit_up", "limit_down"]
    FIELD_MAP = {
        "open": "$open", "high": "$high", "low": "$low",
        "close": "$close", "volume": "$volume", "amount": "$amount",
    }

    def __init__(self, db, qlib_dir: str = "~/.qlib/qlib_data/cn_data_1d"):
        self.db = db
        self.qlib_dir = Path(qlib_dir).expanduser()

    def sync_daily(
        self,
        start: str = "2015-01-01",
        end: Optional[str] = None,
    ) -> None:
        """Export TimescaleDB market_daily to Qlib directory format."""
        if end is None:
            end = str(datetime.now().date())

        logger.info("Syncing daily data %s to %s", start, end)

        # Query data
        df = self.db.query_price(
            symbols=None, frequency="daily", start=start, end=end,
        )
        if df.empty:
            logger.warning("No data returned from TimescaleDB")
            return

        # Ensure column names
        if "time" not in df.columns and "timestamp" in df.columns:
            df = df.rename(columns={"timestamp": "time"})

        # Convert symbols to Qlib format
        if "symbol" in df.columns:
            df["symbol"] = df["symbol"].apply(self.to_qlib_symbol)

        df["time"] = pd.to_datetime(df["time"])
        df = df.sort_values(["symbol", "time"])

        # Compute derived fields
        df["vwap"] = df.get("vwap", df[["open", "high", "low", "close"]].mean(axis=1))
        df["returns"] = df.groupby("symbol")["close"].pct_change()

        # Forward returns for IC evaluation: close_tomorrow / close_today - 1
        df["returns_1d"] = df.groupby("symbol")["close"].shift(-1) / df["close"] - 1

        # Create directory structure
        self._create_dirs()

        # Write calendar
        trading_days = sorted(df["time"].dt.strftime("%Y-%m-%d").unique())
        self._write_calendar(trading_days)

        # Write instruments
        symbols = sorted(df["symbol"].unique())
        min_date = df["time"].min().strftime("%Y-%m-%d")
        max_date = df["time"].max().strftime("%Y-%m-%d")
        self._write_instruments(symbols, min_date, max_date)

        # Write features per symbol
        all_fields = self.FIELDS + ["vwap", "returns", "returns_1d"]
        for af in self.AUX_FIELDS:
            if af in df.columns:
                all_fields.append(af)
        for symbol, group in df.groupby("symbol"):
            self._write_symbol_features(str(symbol), group, all_fields, trading_days)

        logger.info("Sync complete: %d symbols, %d days", len(symbols), len(trading_days))

    def _create_dirs(self) -> None:
        (self.qlib_dir / "calendars").mkdir(parents=True, exist_ok=True)
        (self.qlib_dir / "instruments").mkdir(parents=True, exist_ok=True)
        (self.qlib_dir / "features").mkdir(parents=True, exist_ok=True)

    def _write_calendar(self, trading_days: list) -> None:
        cal_path = self.qlib_dir / "calendars" / "day.txt"
        cal_path.write_text("\n".join(trading_days) + "\n")

    def _write_instruments(self, symbols: list, start: str, end: str) -> None:
        inst_path = self.qlib_dir / "instruments" / "all.txt"
        lines = [f"{sym}\t{start}\t{end}" for sym in symbols]
        inst_path.write_text("\n".join(lines) + "\n")

    def _write_symbol_features(
        self, symbol: str, data: pd.DataFrame, fields: list, calendar: list
    ) -> None:
        """Write Qlib binary feature files for one symbol."""
        sym_dir = self.qlib_dir / "features" / symbol
        sym_dir.mkdir(parents=True, exist_ok=True)

        # Align data to calendar
        data = data.set_index(data["time"].dt.strftime("%Y-%m-%d"))

        for field in fields:
            if field not in data.columns:
                continue
            values = []
            for day in calendar:
                if day in data.index:
                    row = data.loc[day]
                    if isinstance(row, pd.DataFrame):
                        row = row.iloc[0]
                    val = float(row[field]) if not pd.isna(row[field]) else float("nan")
                else:
                    val = float("nan")
                values.append(val)

            # Write as Qlib binary format:
            #   header: start_index as float32 (first non-NaN calendar index)
            #   data:   float32 values for each calendar day
            start_idx = 0
            for i, v in enumerate(values):
                if not np.isnan(v):
                    start_idx = i
                    break

            bin_path = sym_dir / f"{field}.day.bin"
            with open(bin_path, "wb") as f:
                f.write(struct.pack("<f", float(start_idx)))
                for v in values:
                    f.write(struct.pack("<f", v))

    def sync_minute_aggregates(self, start: str = "2024-01-01", end: str = None) -> None:
        """Aggregate 1min data into daily features and write to Qlib format.

        Features computed:
          $intraday_vol   : std of 1min returns within day
          $intraday_skew  : skewness of 1min returns within day
          $intraday_kurt  : kurtosis of 1min returns within day
          $vwap_dev       : actual VWAP vs simple average deviation
          $volume_conc    : volume Herfindahl concentration index
          $high_low_range : (high - low) / close
          $morning_momentum : morning session (9:30-11:30) return
          $afternoon_ret  : afternoon session (13:00-15:00) return
        """
        if end is None:
            end = str(datetime.now().date())

        logger.info("Syncing minute aggregates %s to %s", start, end)

        df = self.db.query_price(symbols=None, frequency="1min", start=start, end=end)
        if df.empty:
            logger.warning("No 1min data returned")
            return

        if "time" not in df.columns and "timestamp" in df.columns:
            df = df.rename(columns={"timestamp": "time"})
        if "symbol" in df.columns:
            df["symbol"] = df["symbol"].apply(self.to_qlib_symbol)

        df["time"] = pd.to_datetime(df["time"])
        df["date"] = df["time"].dt.date.astype(str)
        df = df.sort_values(["symbol", "time"])

        # 1min returns
        df["ret_1min"] = df.groupby(["symbol", "date"])["close"].pct_change()

        agg_rows = []
        for (sym, date), group in df.groupby(["symbol", "date"]):
            rets = group["ret_1min"].dropna()
            row = {"symbol": sym, "date": date}
            row["intraday_vol"] = float(rets.std()) if len(rets) > 1 else 0.0
            row["intraday_skew"] = float(rets.skew()) if len(rets) > 2 else 0.0
            row["intraday_kurt"] = float(rets.kurtosis()) if len(rets) > 3 else 0.0

            avg_price = group["close"].mean()
            vwap_actual = (group["close"] * group["volume"]).sum() / group["volume"].sum() if group["volume"].sum() > 0 else avg_price
            row["vwap_dev"] = float((vwap_actual - avg_price) / avg_price) if avg_price != 0 else 0.0

            vol_shares = group["volume"] / group["volume"].sum() if group["volume"].sum() > 0 else 0
            row["volume_conc"] = float((vol_shares ** 2).sum())

            row["high_low_range"] = float((group["high"].max() - group["low"].min()) / group["close"].iloc[-1]) if group["close"].iloc[-1] != 0 else 0.0

            # Morning: 9:30-11:30, Afternoon: 13:00-15:00
            morning = group[(group["time"].dt.hour < 12)]
            afternoon = group[(group["time"].dt.hour >= 13)]
            row["morning_momentum"] = float(morning["close"].iloc[-1] / morning["close"].iloc[0] - 1) if len(morning) > 1 else 0.0
            row["afternoon_ret"] = float(afternoon["close"].iloc[-1] / afternoon["close"].iloc[0] - 1) if len(afternoon) > 1 else 0.0

            agg_rows.append(row)

        if not agg_rows:
            return

        agg_df = pd.DataFrame(agg_rows)

        # Read existing calendar
        cal_path = self.qlib_dir / "calendars" / "day.txt"
        if cal_path.exists():
            calendar = cal_path.read_text().strip().split("\n")
        else:
            calendar = sorted(agg_df["date"].unique())

        minute_fields = ["intraday_vol", "intraday_skew", "intraday_kurt",
                         "vwap_dev", "volume_conc", "high_low_range",
                         "morning_momentum", "afternoon_ret"]

        for symbol, grp in agg_df.groupby("symbol"):
            grp = grp.rename(columns={"date": "time"})
            grp["time"] = pd.to_datetime(grp["time"])
            self._write_symbol_features(str(symbol), grp, minute_fields, calendar)

        logger.info("Minute aggregates sync complete: %d symbols", agg_df["symbol"].nunique())

    def incremental_update(self) -> None:
        """Incremental update: sync only data newer than the last calendar entry."""
        cal_path = self.qlib_dir / "calendars" / "day.txt"
        if not cal_path.exists():
            logger.info("No existing calendar; running full sync")
            self.sync_daily()
            return

        lines = cal_path.read_text().strip().split("\n")
        last_date = lines[-1] if lines else "2015-01-01"
        logger.info("Incremental sync from %s", last_date)
        self.sync_daily(start=last_date)

    @staticmethod
    def to_qlib_symbol(symbol: str) -> str:
        """Convert symbol to Qlib format: 600000.SH -> SH600000."""
        if "." in symbol:
            code, exchange = symbol.split(".")
            return f"{exchange}{code}"
        return symbol
