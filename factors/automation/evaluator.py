"""Factor evaluator with IC analysis (Spearman)."""

from __future__ import annotations

import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from data.ricequant_source import RiceQuantSource
from data.storage.timescale_storage import TimescaleDB

logger = logging.getLogger(__name__)


class FactorEvaluator:
    """Evaluate factor quality through cross-sectional IC analysis."""

    def __init__(
        self,
        db: Optional[TimescaleDB] = None,
        data_source: Optional[RiceQuantSource] = None,
    ) -> None:
        self.db = db or TimescaleDB()
        self.data_source = data_source or RiceQuantSource()
        self._logger = logger

    def evaluate(
        self,
        factor_df: pd.DataFrame,
        price_df: pd.DataFrame,
        forward_period: int = 1,
    ) -> Dict[str, object]:
        """
        Evaluate factor with daily cross-sectional Spearman IC.

        factor_df must include columns: time, symbol, value
        price_df must include columns: time, symbol, close
        """
        if factor_df.empty or price_df.empty:
            self._logger.warning("Empty input for evaluation")
            return {
                "ic_mean": np.nan,
                "ic_std": np.nan,
                "ic_ir": np.nan,
                "overall_ic": np.nan,
                "overall_p_value": np.nan,
                "n_obs": 0,
                "daily_ic": pd.DataFrame(columns=["time", "ic", "p_value"]),
            }

        factor_long = self._to_long(factor_df, value_name="factor_value")
        price_long = self._to_long(price_df, value_name="close")

        price_long = price_long.sort_values(["symbol", "time"])
        price_long["future_return"] = (
            price_long.groupby("symbol")["close"].pct_change(forward_period).shift(-forward_period)
        )

        merged = factor_long.merge(
            price_long[["time", "symbol", "future_return"]],
            on=["time", "symbol"],
            how="inner",
        ).dropna(subset=["factor_value", "future_return"])

        if merged.empty:
            self._logger.warning("No overlap between factor and future returns")
            return {
                "ic_mean": np.nan,
                "ic_std": np.nan,
                "ic_ir": np.nan,
                "overall_ic": np.nan,
                "overall_p_value": np.nan,
                "n_obs": 0,
                "daily_ic": pd.DataFrame(columns=["time", "ic", "p_value"]),
            }

        daily_rows = []
        for time, group in merged.groupby("time"):
            if group["factor_value"].nunique() < 2 or group["future_return"].nunique() < 2:
                continue
            ic, p_value = spearmanr(group["factor_value"], group["future_return"], nan_policy="omit")
            if np.isnan(ic):
                continue
            daily_rows.append({"time": time, "ic": float(ic), "p_value": float(p_value)})

        daily_ic_df = pd.DataFrame(daily_rows).sort_values("time") if daily_rows else pd.DataFrame(
            columns=["time", "ic", "p_value"]
        )
        overall_ic, overall_p = spearmanr(
            merged["factor_value"], merged["future_return"], nan_policy="omit"
        )

        ic_mean = float(daily_ic_df["ic"].mean()) if not daily_ic_df.empty else np.nan
        ic_std = float(daily_ic_df["ic"].std()) if len(daily_ic_df) > 1 else np.nan
        ic_ir = float(ic_mean / ic_std) if ic_std and not np.isnan(ic_std) and ic_std != 0 else np.nan

        result = {
            "ic_mean": ic_mean,
            "ic_std": ic_std,
            "ic_ir": ic_ir,
            "overall_ic": float(overall_ic) if not np.isnan(overall_ic) else np.nan,
            "overall_p_value": float(overall_p) if not np.isnan(overall_p) else np.nan,
            "n_obs": int(len(merged)),
            "daily_ic": daily_ic_df,
        }
        self._logger.info(
            "Evaluation done: n_obs=%d, ic_mean=%s, overall_ic=%s",
            result["n_obs"],
            result["ic_mean"],
            result["overall_ic"],
        )
        return result

    def _to_long(self, df: pd.DataFrame, value_name: str) -> pd.DataFrame:
        if {"time", "symbol", value_name}.issubset(df.columns):
            return df[["time", "symbol", value_name]].copy()
        if {"time", "symbol", "value"}.issubset(df.columns):
            return df[["time", "symbol", "value"]].rename(columns={"value": value_name})

        if isinstance(df.index, pd.MultiIndex):
            result = df.reset_index()
            candidate_cols = [c for c in result.columns if c not in {"time", "symbol"}]
            if not candidate_cols:
                raise ValueError("Cannot infer value column from DataFrame")
            return result[["time", "symbol", candidate_cols[0]]].rename(columns={candidate_cols[0]: value_name})

        if {"time", "symbol"}.issubset(df.columns):
            candidate_cols = [c for c in df.columns if c not in {"time", "symbol"}]
            if not candidate_cols:
                raise ValueError("Cannot infer value column from DataFrame")
            return df[["time", "symbol", candidate_cols[0]]].rename(columns={candidate_cols[0]: value_name})

        raise ValueError("DataFrame format not supported; expected long format with time/symbol/value")

