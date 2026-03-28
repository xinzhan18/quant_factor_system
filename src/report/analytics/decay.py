"""DecayAnalyzer -- IC decay, autocorrelation, and returns decay analysis.

Merged from:
  - mining/report/builder.py (compute_decay, compute_autocorrelation,
    plot_ic_decay, plot_autocorrelation)
  - visualization/group_returns.py (plot_returns_decay)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import List


class DecayAnalyzer:
    """Analyze factor signal persistence: IC decay, autocorrelation, returns decay."""

    def __init__(self, factor_name: str = None):
        self.factor_name = factor_name

    # ------------------------------------------------------------------
    # Source A: mining/report/builder.py
    # ------------------------------------------------------------------

    def compute_decay(
        self,
        flat_factor: pd.DataFrame,
        price_df: pd.DataFrame,
        periods: List[int] | None = None,
    ) -> dict:
        """Compute IC decay across multiple holding periods.

        Args:
            flat_factor: Factor data (time, symbol, value).
            price_df: Price data (time, symbol, close).
            periods: Holding periods in days. Defaults to [1, 5, 10, 20, 60].

        Returns:
            Dict with 'ic_by_period' (list of {period, ic, ratio}) and
            'half_life_days' (int or None).
        """
        if periods is None:
            periods = [1, 5, 10, 20, 60]

        merged = pd.merge(flat_factor, price_df, on=["time", "symbol"], how="inner")
        merged = merged.sort_values(["symbol", "time"])
        results = []
        base_ic = None
        for period in periods:
            merged[f"ret_{period}"] = merged.groupby("symbol")["close"].pct_change(period).shift(-period)
            valid = merged.dropna(subset=["value", f"ret_{period}"])
            if len(valid) < 100:
                continue
            daily_ic = valid.groupby("time").apply(
                lambda x: x["value"].corr(x[f"ret_{period}"], method="spearman") if len(x) > 3 else np.nan
            ).dropna()
            ic = float(daily_ic.mean())
            if base_ic is None:
                base_ic = ic
            ratio = abs(ic / base_ic) if base_ic != 0 else 0
            results.append({"period": period, "ic": round(ic, 6), "ratio": round(ratio, 4)})

        # Estimate half-life
        half_life = None
        for r in results:
            if r["ratio"] <= 0.5:
                half_life = r["period"]
                break

        return {"ic_by_period": results, "half_life_days": half_life}

    def compute_autocorrelation(self, factor_values: pd.DataFrame) -> list:
        """Compute factor value autocorrelation at selected lags.

        Args:
            factor_values: Multi-indexed DataFrame (datetime, instrument) with
                           factor values in the first column.

        Returns:
            List of {lag, corr} dicts.
        """
        result = []
        unique_dates = factor_values.index.get_level_values("datetime").unique()
        for lag in [1, 2, 3, 5, 10, 15, 20]:
            corrs = []
            for date in unique_dates[lag:]:
                try:
                    date_loc = unique_dates.get_loc(date)
                    if date_loc < lag:
                        continue
                    current = factor_values.xs(date, level="datetime").iloc[:, 0]
                    prev_date = unique_dates[date_loc - lag]
                    prev = factor_values.xs(prev_date, level="datetime").iloc[:, 0]
                    common = current.index.intersection(prev.index)
                    if len(common) > 10:
                        corrs.append(current[common].corr(prev[common], method="spearman"))
                except (KeyError, IndexError):
                    continue
                if len(corrs) >= 50:
                    break
            if corrs:
                result.append({"lag": lag, "corr": round(float(np.mean(corrs)), 4)})
        return result

    def plot_ic_decay(self, decay_result: dict, name: str = None) -> go.Figure:
        """Plot IC decay bar chart.

        Args:
            decay_result: Dict returned by compute_decay (must have 'ic_by_period').
            name: Factor name for chart title.

        Returns:
            Plotly Figure.
        """
        if name is None:
            name = self.factor_name or ""

        ic_by_period = decay_result["ic_by_period"]
        periods = [str(d["period"]) + "d" for d in ic_by_period]
        ics = [d["ic"] for d in ic_by_period]
        fig = go.Figure(data=go.Bar(x=periods, y=ics))
        fig.add_hline(y=0, line_dash="dot")
        fig.update_layout(
            title=f"{name} IC Decay".strip(),
            template="plotly_white",
            height=350,
        )
        return fig

    def plot_autocorrelation(self, autocorr: list, name: str = None) -> go.Figure:
        """Plot factor autocorrelation curve.

        Args:
            autocorr: List of {lag, corr} dicts returned by compute_autocorrelation.
            name: Factor name for chart title.

        Returns:
            Plotly Figure.
        """
        if name is None:
            name = self.factor_name or ""

        lags = [a["lag"] for a in autocorr]
        corrs = [a["corr"] for a in autocorr]
        fig = go.Figure(data=go.Scatter(x=lags, y=corrs, mode="lines+markers"))
        fig.update_layout(
            title=f"{name} Factor Autocorrelation".strip(),
            template="plotly_white",
            height=350,
            xaxis_title="Lag (days)",
            yaxis_title="Spearman Correlation",
        )
        return fig

    # ------------------------------------------------------------------
    # Source B: visualization/group_returns.py
    # ------------------------------------------------------------------

    def plot_returns_decay(
        self,
        factor_df: pd.DataFrame,
        price_df: pd.DataFrame,
        holding_periods: List[int] | None = None,
        title: str = None,
    ) -> go.Figure:
        """Plot returns decay -- IC at different holding periods.

        Args:
            factor_df: Factor data (time, symbol, value).
            price_df: Price data (time, symbol, close).
            holding_periods: Holding periods in days.
            title: Chart title.

        Returns:
            Plotly Figure.
        """
        if holding_periods is None:
            holding_periods = [1, 5, 10, 20, 60]

        if title is None:
            title = f"{self.factor_name} Returns Decay" if self.factor_name else "Returns Decay"

        merged = pd.merge(factor_df, price_df, on=["time", "symbol"], how="inner")
        merged = merged.sort_values(["symbol", "time"])

        decay_results = []

        for period in holding_periods:
            merged[f"return_{period}d"] = merged.groupby("symbol")["close"].pct_change(period)

            valid_data = merged.dropna(subset=["value", f"return_{period}d"])
            if len(valid_data) > 100:
                ic = valid_data["value"].corr(valid_data[f"return_{period}d"])
                decay_results.append({
                    "holding_period": f"{period}d",
                    "period": period,
                    "ic": ic,
                })

        decay_df = pd.DataFrame(decay_results)

        fig = px.bar(
            decay_df,
            x="holding_period",
            y="ic",
            title=title,
            labels={"holding_period": "Holding Period", "ic": "IC"},
        )

        fig.add_hline(y=0, line_dash="dot", line_color="black")

        fig.update_layout(template="plotly_white", height=400)

        return fig
