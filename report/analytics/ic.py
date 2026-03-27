"""ICAnalyzer -- IC computation and visualization for factor reports.

Merged from:
  - visualization/ic_analyzer.py (full class)
  - mining/report/builder.py (IC summary, annual breakdown, monthly heatmap,
    cumulative IC chart, monthly heatmap chart)
"""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats as sp_stats
from typing import Dict, List
from datetime import datetime

# Market regime lookup (CSI 300 annual returns)
_REGIME_LOOKUP = {
    2015: "bear", 2016: "sideways", 2017: "bull", 2018: "bear", 2019: "bull",
    2020: "bull", 2021: "sideways", 2022: "bear", 2023: "bear", 2024: "sideways",
    2025: "sideways",
}


class ICAnalyzer:
    """IC analyzer: compute and visualize Information Coefficients."""

    def __init__(self, factor_name: str = None):
        self.factor_name = factor_name
        self.ic_results: Dict[str, pd.DataFrame] = {}

    # ------------------------------------------------------------------
    # Source A: visualization/ic_analyzer.py
    # ------------------------------------------------------------------

    def compute_ic(
        self,
        factor_df: pd.DataFrame,
        price_df: pd.DataFrame,
        split_date: datetime = None,
        method: str = "spearman",
    ) -> Dict:
        """Compute IC from factor and price DataFrames.

        Args:
            factor_df: Factor data (time, symbol, value).
            price_df: Price data (time, symbol, close).
            split_date: Train/test split date.
            method: Correlation method (pearson/spearman).

        Returns:
            Dict with IC results including rolling_ic DataFrame.
        """
        merged = pd.merge(factor_df, price_df, on=["time", "symbol"], how="inner")

        if len(merged) < 100:
            return {"error": "Insufficient data"}

        merged = merged.sort_values(["symbol", "time"])
        merged["future_return"] = merged.groupby("symbol")["close"].pct_change().shift(-1)
        merged = merged.dropna(subset=["value", "future_return"])
        merged = merged[merged["future_return"].abs() < 0.11]

        if len(merged) < 100:
            return {"error": "Insufficient data after merge"}

        if split_date:
            merged["period"] = merged["time"].apply(
                lambda x: "train" if x <= split_date else "test"
            )

        result = {}

        periods = ["train", "test"] if split_date else ["all"]
        for period in periods:
            if period == "all":
                period_data = merged
            else:
                period_data = merged[merged["period"] == period]

            if len(period_data) > 100:
                ic = period_data["value"].corr(period_data["future_return"], method=method)
                result[f"ic_{period}"] = ic
                result[f"samples_{period}"] = len(period_data)
                result[f"start_{period}"] = period_data["time"].min().strftime("%Y-%m-%d")
                result[f"end_{period}"] = period_data["time"].max().strftime("%Y-%m-%d")

        result["ic_all"] = merged["value"].corr(merged["future_return"], method=method)
        result["samples_all"] = len(merged)

        daily_ic = merged.groupby("time").apply(
            lambda x: x["value"].corr(x["future_return"], method=method)
            if x["future_return"].std() > 0
            else 0
        ).reset_index()
        daily_ic.columns = ["date", "IC"]

        if split_date:
            daily_ic["period"] = daily_ic["date"].apply(
                lambda x: "train" if x <= split_date else "test"
            )

        result["rolling_ic"] = daily_ic

        return result

    def plot_ic_timeseries(
        self,
        rolling_ic_df: pd.DataFrame,
        split_date: datetime = None,
        title: str = None,
        show_legend: bool = True,
    ) -> go.Figure:
        """Plot IC time series with optional train/test split line.

        Args:
            rolling_ic_df: Rolling IC data (date, IC, period).
            split_date: Split date for annotation.
            title: Chart title.
            show_legend: Whether to show legend.

        Returns:
            Plotly Figure.
        """
        if title is None:
            title = f"{self.factor_name} IC Time Series" if self.factor_name else "IC Time Series"

        color_map = {"train": "green", "test": "red", "all": "blue"}

        fig = px.line(
            rolling_ic_df,
            x="date",
            y="IC",
            color="period" if "period" in rolling_ic_df.columns else None,
            title=title,
            color_discrete_map=color_map if "period" in rolling_ic_df.columns else None,
        )

        fig.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.5)
        fig.add_hline(y=0.02, line_dash="dot", line_color="blue", opacity=0.5)
        fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", opacity=0.5)

        if split_date:
            split_x = split_date.strftime("%Y-%m-%d") if hasattr(split_date, "strftime") else str(split_date)
            fig.add_shape(
                type="line",
                x0=split_x, x1=split_x,
                y0=0, y1=1,
                xref="x", yref="paper",
                line=dict(dash="dash", color="gray"),
            )
            fig.add_annotation(
                x=split_x, y=1,
                xref="x", yref="paper",
                text="Train/Test Split",
                showarrow=False,
                yanchor="bottom",
            )

        fig.update_layout(
            template="plotly_white",
            showlegend=show_legend,
            height=400,
            xaxis_title="Date",
            yaxis_title="IC",
        )

        return fig

    def plot_ic_distribution(
        self,
        rolling_ic_df: pd.DataFrame,
        title: str = None,
        show_kde: bool = True,
    ) -> go.Figure:
        """Plot IC distribution histogram and box plot.

        Args:
            rolling_ic_df: Rolling IC data.
            title: Chart title.
            show_kde: Whether to show KDE (reserved).

        Returns:
            Plotly Figure.
        """
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
                fig.add_trace(
                    go.Histogram(
                        x=data,
                        name=period,
                        opacity=0.7,
                        histnorm="probability density",
                    ),
                    row=1, col=1,
                )
        else:
            fig.add_trace(
                go.Histogram(
                    x=rolling_ic_df["IC"],
                    opacity=0.7,
                    histnorm="probability density",
                ),
                row=1, col=1,
            )

        if "period" in rolling_ic_df.columns:
            for period in rolling_ic_df["period"].unique():
                data = rolling_ic_df[rolling_ic_df["period"] == period]["IC"]
                fig.add_trace(
                    go.Box(y=data, name=period, boxpoints="outliers"),
                    row=1, col=2,
                )
        else:
            fig.add_trace(
                go.Box(y=rolling_ic_df["IC"], boxpoints="outliers"),
                row=1, col=2,
            )

        fig.add_hline(y=0, line_dash="dot", line_color="black", row=1, col=1)
        fig.add_hline(y=0.02, line_dash="dot", line_color="blue", row=1, col=1)

        fig.update_layout(
            title=title,
            template="plotly_white",
            height=400,
            showlegend=False,
        )

        return fig

    def plot_rolling_ic_comparison(
        self,
        daily_ic: pd.Series,
        windows: List[int] = [20, 60, 120],
        title: str = None,
    ) -> go.Figure:
        """Plot multi-window rolling IC comparison.

        Args:
            daily_ic: Daily IC Series.
            windows: Window sizes.
            title: Chart title.

        Returns:
            Plotly Figure.
        """
        if title is None:
            title = f"{self.factor_name} Rolling IC Comparison" if self.factor_name else "Rolling IC Comparison"

        df = pd.DataFrame({"IC": daily_ic})
        for w in windows:
            df[f"IC_{w}d"] = df["IC"].rolling(window=w, min_periods=10).mean()

        fig = px.line(
            df,
            title=title,
            labels={"value": "IC", "index": "Date"},
        )

        fig.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.5)
        fig.add_hline(y=0.02, line_dash="dot", line_color="blue", opacity=0.5)
        fig.add_hline(y=-0.02, line_dash="dot", line_color="blue", opacity=0.5)

        fig.update_layout(
            template="plotly_white",
            height=400,
            xaxis_title="Date",
            yaxis_title="IC",
        )

        return fig

    def compute_ic_statistics(self, rolling_ic_df: pd.DataFrame) -> pd.DataFrame:
        """Compute IC statistics (count, mean, std, min, max, median, win_rate, ic_rate).

        Args:
            rolling_ic_df: Rolling IC data.

        Returns:
            Statistics DataFrame.
        """
        if "period" in rolling_ic_df.columns:
            stats = rolling_ic_df.groupby("period")["IC"].agg(
                ["count", "mean", "std", "min", "max", "median"]
            )
            win_rate = rolling_ic_df.groupby("period").apply(
                lambda x: (x["IC"] > 0).mean()
            )
            ic_rate = rolling_ic_df.groupby("period").apply(
                lambda x: (x["IC"].abs() > 0.02).mean()
            )
            stats["win_rate"] = win_rate
            stats["ic_rate"] = ic_rate
        else:
            stats = pd.DataFrame(
                {"IC": rolling_ic_df["IC"].agg(["count", "mean", "std", "min", "max", "median"])}
            ).T
            stats["win_rate"] = (rolling_ic_df["IC"] > 0).mean()
            stats["ic_rate"] = (rolling_ic_df["IC"].abs() > 0.02).mean()

        return stats

    def generate_ic_report(
        self,
        factor_df: pd.DataFrame,
        price_df: pd.DataFrame,
        split_date: datetime = None,
        output_dir: str = None,
    ) -> Dict:
        """Generate a complete IC analysis report.

        Args:
            factor_df: Factor data.
            price_df: Price data.
            split_date: Train/test split date.
            output_dir: Output directory (unused, kept for API compat).

        Returns:
            Report dict with charts and statistics.
        """
        result = self.compute_ic(factor_df, price_df, split_date)

        if "error" in result:
            return result

        report = {
            "factor_name": self.factor_name,
            "ic_all": result["ic_all"],
            "samples_all": result["samples_all"],
            "ic_stats": None,
            "charts": {},
        }

        if split_date:
            report["ic_train"] = result.get("ic_train")
            report["ic_test"] = result.get("ic_test")
            report["samples_train"] = result.get("samples_train")
            report["samples_test"] = result.get("samples_test")

        report["charts"]["ic_timeseries"] = self.plot_ic_timeseries(
            result["rolling_ic"], split_date
        )
        report["charts"]["ic_distribution"] = self.plot_ic_distribution(
            result["rolling_ic"]
        )
        report["charts"]["rolling_ic"] = self.plot_rolling_ic_comparison(
            result["rolling_ic"].set_index("date")["IC"]
        )
        report["ic_stats"] = self.compute_ic_statistics(result["rolling_ic"])

        return report

    # ------------------------------------------------------------------
    # Source B: mining/report/builder.py
    # ------------------------------------------------------------------

    def compute_ic_summary(self, daily_ic: pd.DataFrame, split_date) -> tuple[dict, dict]:
        """Compute IC summary stats for IS and OOS from daily IC DataFrame.

        Args:
            daily_ic: DataFrame with columns [date, IC] and optionally [period].
            split_date: The IS/OOS split date.

        Returns:
            Tuple of (is_summary, oos_summary) dicts with keys:
            ic_mean, ic_std, ic_ir, win_rate, ic_significant_rate, n_days.
        """
        def _summarize(ic_series):
            if len(ic_series) < 5:
                return {"ic_mean": 0, "ic_std": 0, "ic_ir": 0, "win_rate": 0, "ic_significant_rate": 0, "n_days": 0}
            m = float(ic_series.mean())
            s = float(ic_series.std())
            return {
                "ic_mean": round(m, 6),
                "ic_std": round(s, 6),
                "ic_ir": round(m / s, 4) if s > 0 else 0,
                "win_rate": round(float((ic_series > 0).mean()), 4),
                "ic_significant_rate": round(float((ic_series.abs() > 0.02).mean()), 4),
                "n_days": len(ic_series),
            }

        if "period" in daily_ic.columns:
            is_ic = daily_ic[daily_ic["period"] == "train"]["IC"]
            oos_ic = daily_ic[daily_ic["period"] == "test"]["IC"]
        else:
            is_ic = daily_ic[daily_ic["date"] < split_date]["IC"]
            oos_ic = daily_ic[daily_ic["date"] >= split_date]["IC"]

        return _summarize(is_ic), _summarize(oos_ic)

    def compute_annual_breakdown(self, daily_ic: pd.DataFrame) -> list[dict]:
        """Compute annual IC breakdown with regime labels.

        Args:
            daily_ic: DataFrame with columns [date, IC].

        Returns:
            List of dicts with keys: year, ic_mean, ic_ir, win_rate, regime.
        """
        daily_ic = daily_ic.copy()
        daily_ic["year"] = pd.to_datetime(daily_ic["date"]).dt.year
        result = []
        for year, group in daily_ic.groupby("year"):
            ic = group["IC"]
            if len(ic) < 20:
                continue
            m = float(ic.mean())
            s = float(ic.std())
            result.append({
                "year": int(year),
                "ic_mean": round(m, 4),
                "ic_ir": round(m / s, 4) if s > 0 else 0,
                "win_rate": round(float((ic > 0).mean()), 4),
                "regime": _REGIME_LOOKUP.get(int(year), "sideways"),
            })
        return result

    def compute_monthly_heatmap_data(self, daily_ic: pd.DataFrame) -> list:
        """Compute monthly average IC values for heatmap visualization.

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

    def plot_cumulative_ic(self, daily_ic: pd.DataFrame) -> go.Figure:
        """Plot cumulative IC over time.

        Args:
            daily_ic: DataFrame with columns [date, IC].

        Returns:
            Plotly Figure.
        """
        cum_ic = daily_ic["IC"].cumsum()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=daily_ic["date"], y=cum_ic, mode="lines", name="Cumulative IC"))
        fig.add_hline(y=0, line_dash="dot", line_color="black")
        fig.update_layout(
            title="Cumulative IC",
            template="plotly_white",
            height=350,
            xaxis_title="Date",
            yaxis_title="Cumulative IC",
        )
        return fig

    def plot_monthly_heatmap(self, monthly_data: list) -> go.Figure:
        """Plot monthly IC heatmap.

        Args:
            monthly_data: List of [year, month, ic_mean] triples
                          (as returned by compute_monthly_heatmap_data).

        Returns:
            Plotly Figure.
        """
        years = sorted(set(r[0] for r in monthly_data))
        months = list(range(1, 13))
        z = [
            [next((r[2] for r in monthly_data if r[0] == y and r[1] == m), None) for m in months]
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
            title="Monthly IC Heatmap",
            template="plotly_white",
            height=300,
            xaxis_title="Month",
            yaxis_title="Year",
        )
        return fig
