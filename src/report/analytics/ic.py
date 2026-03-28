"""ICAnalyzer -- IC computation and visualization for factor reports.

New interface: compute(merged_df, split_date) takes pre-merged data from
data_prep.merge_factor_price.  Computes both Spearman (RankIC) and Pearson IC
per day cross-sectionally with t-test significance.

Backward-compatible compute_ic() wrapper retained for dashboard/Factors.py.
"""
from __future__ import annotations

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import spearmanr, pearsonr, ttest_1samp
from typing import Dict, List

from report.charts.theme import apply_theme, COLORS


class ICAnalyzer:
    """IC analyzer: compute and visualize Information Coefficients."""

    def __init__(self, factor_name: str = None):
        self.factor_name = factor_name

    # ------------------------------------------------------------------
    # Core compute interface (new)
    # ------------------------------------------------------------------

    def compute(self, merged_df: pd.DataFrame, split_date) -> dict:
        """Compute IC analysis on pre-merged data.

        Args:
            merged_df: Output of data_prep.merge_factor_price with
                       [time, symbol, value, future_return].
            split_date: IS/OOS cutoff date.

        Returns:
            dict with keys:
                summary: {is: {rank_ic_mean, rank_ic_std, ic_mean, ic_std, icir,
                               win_rate, significant_rate, t_stat, p_value, n_days},
                          oos: {same keys}}
                daily_rank_ic: pd.Series (date-indexed)
                daily_pearson_ic: pd.Series (date-indexed)
                annual: [{year, rank_ic, icir, win_rate}, ...]
                monthly_heatmap_data: [[year, month, ic], ...]
        """
        split_date = pd.Timestamp(split_date)
        grouped = merged_df.groupby("time")

        # Compute daily cross-sectional correlations
        daily_rank_ic = self._compute_daily_ic(grouped, method="spearman")
        daily_pearson_ic = self._compute_daily_ic(grouped, method="pearson")

        # Split IS / OOS
        rank_is = daily_rank_ic[daily_rank_ic.index < split_date]
        rank_oos = daily_rank_ic[daily_rank_ic.index >= split_date]
        pearson_is = daily_pearson_ic[daily_pearson_ic.index < split_date]
        pearson_oos = daily_pearson_ic[daily_pearson_ic.index >= split_date]

        # Summaries
        rank_summary_is = self._compute_summary(rank_is, prefix="rank_ic")
        rank_summary_oos = self._compute_summary(rank_oos, prefix="rank_ic")
        pearson_summary_is = self._compute_summary(pearson_is, prefix="ic")
        pearson_summary_oos = self._compute_summary(pearson_oos, prefix="ic")

        # Merge rank and pearson summaries for each period
        is_summary = {**rank_summary_is, **pearson_summary_is}
        oos_summary = {**rank_summary_oos, **pearson_summary_oos}

        # Annual breakdown (based on rank IC)
        annual = self._compute_annual(daily_rank_ic)

        # Monthly heatmap data
        monthly_heatmap_data = self._compute_monthly_heatmap(daily_rank_ic)

        return {
            "summary": {"is": is_summary, "oos": oos_summary},
            "daily_rank_ic": daily_rank_ic,
            "daily_pearson_ic": daily_pearson_ic,
            "annual": annual,
            "monthly_heatmap_data": monthly_heatmap_data,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _compute_daily_ic(self, grouped, method: str = "spearman") -> pd.Series:
        """Compute daily cross-sectional IC (Spearman or Pearson).

        Args:
            grouped: merged_df.groupby("time")
            method: "spearman" or "pearson"

        Returns:
            pd.Series with date index and IC values.
        """
        results = []
        for date, group in grouped:
            if len(group) < 30:
                continue
            if method == "spearman":
                corr, _ = spearmanr(group["value"], group["future_return"])
            else:
                corr, _ = pearsonr(group["value"], group["future_return"])
            results.append({"date": date, "ic": corr})
        if not results:
            return pd.Series(dtype=float, name="ic")
        df = pd.DataFrame(results).set_index("date")["ic"]
        df.index = pd.to_datetime(df.index)
        return df

    def _compute_summary(self, daily_ic_series: pd.Series, prefix: str = "rank_ic") -> dict:
        """Compute summary statistics for a daily IC series.

        Args:
            daily_ic_series: Series of daily IC values.
            prefix: Key prefix for ic_mean / ic_std fields.

        Returns:
            dict with summary statistics.
        """
        ic = daily_ic_series.dropna()
        if len(ic) > 1:
            t_stat, p_value = ttest_1samp(ic, 0)
        else:
            t_stat, p_value = 0.0, 1.0
        return {
            f"{prefix}_mean": float(ic.mean()) if len(ic) > 0 else 0.0,
            f"{prefix}_std": float(ic.std()) if len(ic) > 0 else 0.0,
            "icir": float(ic.mean() / ic.std()) if len(ic) > 0 and ic.std() > 0 else 0.0,
            "win_rate": float((ic > 0).mean()) if len(ic) > 0 else 0.0,
            "significant_rate": float((ic.abs() > 0.02).mean()) if len(ic) > 0 else 0.0,
            "t_stat": float(t_stat),
            "p_value": float(p_value),
            "n_days": len(ic),
        }

    def _compute_annual(self, daily_ic: pd.Series) -> list:
        """Compute annual IC breakdown.

        Args:
            daily_ic: Date-indexed Series of daily rank IC.

        Returns:
            List of dicts with year, rank_ic, icir, win_rate.
        """
        if len(daily_ic) == 0:
            return []
        result = []
        for year, group in daily_ic.groupby(daily_ic.index.year):
            ic = group.dropna()
            if len(ic) < 20:
                continue
            result.append({
                "year": int(year),
                "rank_ic": round(float(ic.mean()), 4),
                "icir": round(float(ic.mean() / ic.std()), 4) if ic.std() > 0 else 0.0,
                "win_rate": round(float((ic > 0).mean()), 4),
            })
        return result

    def _compute_monthly_heatmap(self, daily_ic: pd.Series) -> list:
        """Compute monthly average IC for heatmap visualization.

        Args:
            daily_ic: Date-indexed Series of daily rank IC.

        Returns:
            List of [year, month, ic_mean] triples.
        """
        if len(daily_ic) == 0:
            return []
        ic_df = daily_ic.to_frame("ic")
        ic_df["year"] = ic_df.index.year
        ic_df["month"] = ic_df.index.month
        grouped = ic_df.groupby(["year", "month"])["ic"].mean()
        return [[int(y), int(m), round(float(v), 4)] for (y, m), v in grouped.items()]

    # ------------------------------------------------------------------
    # Chart generation (new)
    # ------------------------------------------------------------------

    def generate_charts(self, result: dict) -> Dict[str, go.Figure]:
        """Generate all IC charts from compute() result.

        Args:
            result: Output of self.compute().

        Returns:
            dict of chart_name -> go.Figure for 5 charts:
                ic_timeseries, ic_distribution, rolling_ic,
                cumulative_ic, monthly_heatmap
        """
        daily_rank_ic = result["daily_rank_ic"]
        split_date = None
        # Infer split_date from summary
        if result["summary"]["oos"]["n_days"] > 0 and result["summary"]["is"]["n_days"] > 0:
            is_end = daily_rank_ic[:].index[
                daily_rank_ic.index < daily_rank_ic.index[result["summary"]["is"]["n_days"] - 1]
                                       + pd.Timedelta(days=1)
            ]
            # Find split: last IS date
            pass

        charts = {}
        charts["ic_timeseries"] = self._chart_ic_timeseries(result)
        charts["ic_distribution"] = self._chart_ic_distribution(result)
        charts["rolling_ic"] = self._chart_rolling_ic(result)
        charts["cumulative_ic"] = self._chart_cumulative_ic(result)
        charts["monthly_heatmap"] = self._chart_monthly_heatmap(result)
        return charts

    def _infer_split_date(self, result: dict):
        """Infer the IS/OOS split date from the result summary."""
        is_n = result["summary"]["is"]["n_days"]
        oos_n = result["summary"]["oos"]["n_days"]
        daily_ic = result["daily_rank_ic"]
        if is_n > 0 and oos_n > 0 and len(daily_ic) > 0:
            sorted_idx = daily_ic.sort_index().index
            if is_n <= len(sorted_idx):
                return sorted_idx[is_n - 1]
        return None

    def _chart_ic_timeseries(self, result: dict) -> go.Figure:
        """Daily IC line with IS/OOS split + 20/60-day MA + +/-0.02 ref lines."""
        daily_ic = result["daily_rank_ic"].sort_index()
        split_date = self._infer_split_date(result)

        fig = go.Figure()

        if split_date is not None:
            is_ic = daily_ic[daily_ic.index <= split_date]
            oos_ic = daily_ic[daily_ic.index > split_date]
            if len(is_ic) > 0:
                fig.add_trace(go.Scatter(
                    x=is_ic.index, y=is_ic.values,
                    mode="lines", name="IS",
                    line=dict(color=COLORS["is_period"], width=1),
                    opacity=0.6,
                ))
            if len(oos_ic) > 0:
                fig.add_trace(go.Scatter(
                    x=oos_ic.index, y=oos_ic.values,
                    mode="lines", name="OOS",
                    line=dict(color=COLORS["oos_period"], width=1),
                    opacity=0.6,
                ))
        else:
            fig.add_trace(go.Scatter(
                x=daily_ic.index, y=daily_ic.values,
                mode="lines", name="Daily IC",
                line=dict(color=COLORS["primary"], width=1),
                opacity=0.6,
            ))

        # Moving averages
        if len(daily_ic) >= 20:
            ma20 = daily_ic.rolling(20, min_periods=10).mean()
            fig.add_trace(go.Scatter(
                x=ma20.index, y=ma20.values,
                mode="lines", name="MA20",
                line=dict(color=COLORS["positive"], width=2),
            ))
        if len(daily_ic) >= 60:
            ma60 = daily_ic.rolling(60, min_periods=30).mean()
            fig.add_trace(go.Scatter(
                x=ma60.index, y=ma60.values,
                mode="lines", name="MA60",
                line=dict(color=COLORS["neutral"], width=2),
            ))

        # Reference lines
        fig.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.5)
        fig.add_hline(y=0.02, line_dash="dot", line_color="blue", opacity=0.3)
        fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", opacity=0.3)

        # Split line annotation
        if split_date is not None:
            split_str = pd.Timestamp(split_date).strftime("%Y-%m-%d")
            fig.add_shape(
                type="line", x0=split_str, x1=split_str,
                y0=0, y1=1, xref="x", yref="paper",
                line=dict(dash="dash", color="gray"),
            )
            fig.add_annotation(
                x=split_str, y=1, xref="x", yref="paper",
                text="IS / OOS Split", showarrow=False, yanchor="bottom",
            )

        title = f"{self.factor_name} IC Time Series" if self.factor_name else "IC Time Series"
        fig.update_layout(height=400, xaxis_title="Date", yaxis_title="IC")
        return apply_theme(fig, title)

    def _chart_ic_distribution(self, result: dict) -> go.Figure:
        """IS vs OOS overlaid histogram of daily IC."""
        daily_ic = result["daily_rank_ic"].sort_index()
        split_date = self._infer_split_date(result)

        fig = go.Figure()

        if split_date is not None:
            is_ic = daily_ic[daily_ic.index <= split_date]
            oos_ic = daily_ic[daily_ic.index > split_date]
            if len(is_ic) > 0:
                fig.add_trace(go.Histogram(
                    x=is_ic.values, name="IS", opacity=0.6,
                    marker_color=COLORS["is_period"],
                    histnorm="probability density",
                ))
            if len(oos_ic) > 0:
                fig.add_trace(go.Histogram(
                    x=oos_ic.values, name="OOS", opacity=0.6,
                    marker_color=COLORS["oos_period"],
                    histnorm="probability density",
                ))
        else:
            fig.add_trace(go.Histogram(
                x=daily_ic.values, name="IC", opacity=0.7,
                marker_color=COLORS["primary"],
                histnorm="probability density",
            ))

        fig.update_layout(barmode="overlay", height=400,
                          xaxis_title="IC", yaxis_title="Density")
        fig.add_vline(x=0, line_dash="dot", line_color="black", opacity=0.5)

        title = f"{self.factor_name} IC Distribution" if self.factor_name else "IC Distribution"
        return apply_theme(fig, title)

    def _chart_rolling_ic(self, result: dict) -> go.Figure:
        """20/60/120-day rolling IC."""
        daily_ic = result["daily_rank_ic"].sort_index()
        fig = go.Figure()

        windows = [20, 60, 120]
        colors = [COLORS["primary"], COLORS["positive"], COLORS["neutral"]]
        for w, color in zip(windows, colors):
            if len(daily_ic) >= w:
                rolling = daily_ic.rolling(w, min_periods=max(10, w // 2)).mean()
                fig.add_trace(go.Scatter(
                    x=rolling.index, y=rolling.values,
                    mode="lines", name=f"IC {w}d",
                    line=dict(color=color, width=2),
                ))

        fig.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.5)
        fig.add_hline(y=0.02, line_dash="dot", line_color="blue", opacity=0.3)
        fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", opacity=0.3)

        fig.update_layout(height=400, xaxis_title="Date", yaxis_title="Rolling IC")
        title = f"{self.factor_name} Rolling IC" if self.factor_name else "Rolling IC"
        return apply_theme(fig, title)

    def _chart_cumulative_ic(self, result: dict) -> go.Figure:
        """Cumulative sum of daily IC."""
        daily_ic = result["daily_rank_ic"].sort_index()
        cum_ic = daily_ic.cumsum()

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=cum_ic.index, y=cum_ic.values,
            mode="lines", name="Cumulative IC",
            line=dict(color=COLORS["primary"], width=2),
        ))
        fig.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.5)

        fig.update_layout(height=350, xaxis_title="Date", yaxis_title="Cumulative IC")
        title = f"{self.factor_name} Cumulative IC" if self.factor_name else "Cumulative IC"
        return apply_theme(fig, title)

    def _chart_monthly_heatmap(self, result: dict) -> go.Figure:
        """Month x Year IC heatmap (RdBu_r)."""
        monthly_data = result["monthly_heatmap_data"]

        if not monthly_data:
            fig = go.Figure()
            fig.update_layout(height=300)
            title = f"{self.factor_name} Monthly IC Heatmap" if self.factor_name else "Monthly IC Heatmap"
            return apply_theme(fig, title)

        years = sorted(set(r[0] for r in monthly_data))
        months = list(range(1, 13))
        z = [
            [next((r[2] for r in monthly_data if r[0] == y and r[1] == m), None)
             for m in months]
            for y in years
        ]

        fig = go.Figure(data=go.Heatmap(
            z=z,
            x=[str(m) for m in months],
            y=[str(y) for y in years],
            colorscale="RdBu_r",
            zmid=0,
        ))
        fig.update_layout(
            height=300,
            xaxis_title="Month",
            yaxis_title="Year",
        )
        title = f"{self.factor_name} Monthly IC Heatmap" if self.factor_name else "Monthly IC Heatmap"
        return apply_theme(fig, title)

    # ------------------------------------------------------------------
    # Backward-compatible wrapper
    # ------------------------------------------------------------------

    def compute_ic(
        self,
        factor_df: pd.DataFrame,
        price_df: pd.DataFrame,
        split_date=None,
        method: str = "spearman",
    ) -> Dict:
        """Backward-compatible wrapper for dashboard/Factors.py.

        Accepts raw factor+price DataFrames, merges them, then delegates
        to the new compute() path.  Returns a dict matching the old interface
        so existing callers (Factors.py, builder.py) keep working.

        Args:
            factor_df: Factor data (time, symbol, value).
            price_df: Price data (time, symbol, close).
            split_date: Train/test split date.
            method: Correlation method (ignored — new impl computes both).

        Returns:
            Dict matching old interface: ic_all, ic_train, ic_test,
            samples_*, rolling_ic DataFrame, etc.
        """
        from report.data_prep import merge_factor_price

        merged = merge_factor_price(factor_df, price_df)

        if len(merged) < 100:
            return {"error": "Insufficient data"}

        # If no split_date, use midpoint
        if split_date is None:
            split_date = merged["time"].median()

        new_result = self.compute(merged, split_date)

        # Map new result to old interface
        daily_rank_ic = new_result["daily_rank_ic"]
        if len(daily_rank_ic) == 0:
            return {"error": "Insufficient data after merge"}

        # Build rolling_ic DataFrame matching old format
        rolling_ic = pd.DataFrame({
            "date": daily_rank_ic.index,
            "IC": daily_rank_ic.values,
        })
        if split_date is not None:
            sd = pd.Timestamp(split_date)
            rolling_ic["period"] = rolling_ic["date"].apply(
                lambda x: "train" if x <= sd else "test"
            )

        result = {
            "ic_all": float(daily_rank_ic.mean()),
            "samples_all": new_result["summary"]["is"]["n_days"] + new_result["summary"]["oos"]["n_days"],
            "rolling_ic": rolling_ic,
        }

        if split_date is not None:
            is_sum = new_result["summary"]["is"]
            oos_sum = new_result["summary"]["oos"]
            result["ic_train"] = is_sum["rank_ic_mean"]
            result["ic_test"] = oos_sum["rank_ic_mean"]
            result["samples_train"] = is_sum["n_days"]
            result["samples_test"] = oos_sum["n_days"]

        return result

    # ------------------------------------------------------------------
    # Legacy builder helpers (retained for builder.py compatibility)
    # ------------------------------------------------------------------

    def compute_ic_summary(self, daily_ic: pd.DataFrame, split_date) -> tuple:
        """Compute IC summary stats for IS and OOS from daily IC DataFrame.

        Retained for builder.py backward compatibility.

        Args:
            daily_ic: DataFrame with columns [date, IC].
            split_date: The IS/OOS split date.

        Returns:
            Tuple of (is_summary, oos_summary).
        """
        split_date = pd.Timestamp(split_date)

        if "period" in daily_ic.columns:
            is_ic = daily_ic[daily_ic["period"] == "train"]["IC"]
            oos_ic = daily_ic[daily_ic["period"] == "test"]["IC"]
        else:
            is_ic = daily_ic[daily_ic["date"] < split_date]["IC"]
            oos_ic = daily_ic[daily_ic["date"] >= split_date]["IC"]

        def _summarize(ic_series):
            ic = ic_series.dropna()
            if len(ic) < 5:
                return {"ic_mean": 0, "ic_std": 0, "ic_ir": 0, "win_rate": 0,
                        "ic_significant_rate": 0, "n_days": 0}
            std = ic.std()
            return {
                "ic_mean": round(float(ic.mean()), 6),
                "ic_std": round(float(std), 6),
                "ic_ir": round(float(ic.mean() / std), 4) if std > 0 else 0,
                "win_rate": round(float((ic > 0).mean()), 4),
                "ic_significant_rate": round(float((ic.abs() > 0.02).mean()), 4),
                "n_days": len(ic),
            }

        return _summarize(is_ic), _summarize(oos_ic)

    def compute_annual_breakdown(self, daily_ic: pd.DataFrame) -> list:
        """Compute annual IC breakdown (no regime lookup).

        Retained for builder.py backward compatibility.

        Args:
            daily_ic: DataFrame with columns [date, IC].

        Returns:
            List of dicts with year, ic_mean, ic_ir, win_rate.
        """
        daily_ic = daily_ic.copy()
        daily_ic["year"] = pd.to_datetime(daily_ic["date"]).dt.year
        result = []
        for year, group in daily_ic.groupby("year"):
            ic = group["IC"].dropna()
            if len(ic) < 20:
                continue
            std = ic.std()
            result.append({
                "year": int(year),
                "ic_mean": round(float(ic.mean()), 4),
                "ic_ir": round(float(ic.mean() / std), 4) if std > 0 else 0,
                "win_rate": round(float((ic > 0).mean()), 4),
            })
        return result

    def compute_monthly_heatmap_data(self, daily_ic: pd.DataFrame) -> list:
        """Compute monthly average IC for heatmap.

        Retained for builder.py backward compatibility.

        Args:
            daily_ic: DataFrame with columns [date, IC].

        Returns:
            List of [year, month, ic_mean] triples.
        """
        daily_ic = daily_ic.copy()
        daily_ic["date"] = pd.to_datetime(daily_ic["date"])
        daily_ic["year"] = daily_ic["date"].dt.year
        daily_ic["month"] = daily_ic["date"].dt.month
        grouped = daily_ic.groupby(["year", "month"])["IC"].mean()
        return [[int(y), int(m), round(float(v), 4)] for (y, m), v in grouped.items()]

    def plot_ic_timeseries(self, rolling_ic_df, split_date=None, title=None, show_legend=True):
        """Legacy chart: IC time series. Delegates to new chart if possible."""
        if title is None:
            title = f"{self.factor_name} IC Time Series" if self.factor_name else "IC Time Series"

        fig = go.Figure()
        if "period" in rolling_ic_df.columns:
            for period in rolling_ic_df["period"].unique():
                data = rolling_ic_df[rolling_ic_df["period"] == period]
                color = COLORS["is_period"] if period == "train" else COLORS["oos_period"]
                fig.add_trace(go.Scatter(
                    x=data["date"], y=data["IC"],
                    mode="lines", name=period,
                    line=dict(color=color, width=1), opacity=0.6,
                ))
        else:
            fig.add_trace(go.Scatter(
                x=rolling_ic_df["date"], y=rolling_ic_df["IC"],
                mode="lines", name="IC",
                line=dict(color=COLORS["primary"], width=1), opacity=0.6,
            ))

        fig.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.5)
        fig.add_hline(y=0.02, line_dash="dot", line_color="blue", opacity=0.3)
        fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", opacity=0.3)

        if split_date:
            split_str = pd.Timestamp(split_date).strftime("%Y-%m-%d")
            fig.add_shape(
                type="line", x0=split_str, x1=split_str,
                y0=0, y1=1, xref="x", yref="paper",
                line=dict(dash="dash", color="gray"),
            )

        fig.update_layout(height=400, xaxis_title="Date", yaxis_title="IC",
                          showlegend=show_legend)
        return apply_theme(fig, title)

    def plot_ic_distribution(self, rolling_ic_df, title=None, show_kde=True):
        """Legacy chart: IC distribution."""
        if title is None:
            title = f"{self.factor_name} IC Distribution" if self.factor_name else "IC Distribution"

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=["IC Histogram", "IC Box Plot"],
            specs=[[{"type": "histogram"}, {"type": "box"}]],
        )

        if "period" in rolling_ic_df.columns:
            for period in rolling_ic_df["period"].unique():
                data = rolling_ic_df[rolling_ic_df["period"] == period]["IC"]
                fig.add_trace(go.Histogram(
                    x=data, name=period, opacity=0.7, histnorm="probability density",
                ), row=1, col=1)
                fig.add_trace(go.Box(
                    y=data, name=period, boxpoints="outliers",
                ), row=1, col=2)
        else:
            fig.add_trace(go.Histogram(
                x=rolling_ic_df["IC"], opacity=0.7, histnorm="probability density",
            ), row=1, col=1)
            fig.add_trace(go.Box(
                y=rolling_ic_df["IC"], boxpoints="outliers",
            ), row=1, col=2)

        fig.update_layout(height=400, showlegend=False)
        return apply_theme(fig, title)

    def plot_rolling_ic_comparison(self, daily_ic, windows=None, title=None):
        """Legacy chart: rolling IC comparison."""
        if windows is None:
            windows = [20, 60, 120]
        if title is None:
            title = f"{self.factor_name} Rolling IC" if self.factor_name else "Rolling IC"

        df = pd.DataFrame({"IC": daily_ic})
        fig = go.Figure()
        colors = [COLORS["primary"], COLORS["positive"], COLORS["neutral"]]
        for i, w in enumerate(windows):
            rolling = df["IC"].rolling(window=w, min_periods=10).mean()
            fig.add_trace(go.Scatter(
                x=rolling.index, y=rolling.values,
                mode="lines", name=f"IC_{w}d",
                line=dict(color=colors[i % len(colors)], width=2),
            ))

        fig.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.5)
        fig.add_hline(y=0.02, line_dash="dot", line_color="blue", opacity=0.3)
        fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", opacity=0.3)
        fig.update_layout(height=400, xaxis_title="Date", yaxis_title="IC")
        return apply_theme(fig, title)

    def plot_cumulative_ic(self, daily_ic_df):
        """Legacy chart: cumulative IC."""
        cum_ic = daily_ic_df["IC"].cumsum()
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=daily_ic_df["date"], y=cum_ic,
            mode="lines", name="Cumulative IC",
            line=dict(color=COLORS["primary"], width=2),
        ))
        fig.add_hline(y=0, line_dash="dot", line_color="black")
        fig.update_layout(height=350, xaxis_title="Date", yaxis_title="Cumulative IC")
        return apply_theme(fig, "Cumulative IC")

    def plot_monthly_heatmap(self, monthly_data):
        """Legacy chart: monthly IC heatmap."""
        years = sorted(set(r[0] for r in monthly_data))
        months = list(range(1, 13))
        z = [
            [next((r[2] for r in monthly_data if r[0] == y and r[1] == m), None)
             for m in months]
            for y in years
        ]
        fig = go.Figure(data=go.Heatmap(
            z=z, x=[str(m) for m in months], y=[str(y) for y in years],
            colorscale="RdBu_r", zmid=0,
        ))
        fig.update_layout(height=300, xaxis_title="Month", yaxis_title="Year")
        return apply_theme(fig, "Monthly IC Heatmap")
