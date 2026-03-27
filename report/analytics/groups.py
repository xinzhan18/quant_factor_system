"""GroupReturnsAnalyzer -- quintile/group returns computation and visualization.

Merged from:
  - visualization/group_returns.py (core class, minus plot_returns_decay)
  - mining/report/builder.py (quintile detailed stats, monotonicity, IS vs OOS bar)
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats as sp_stats
from typing import Dict, List
from datetime import datetime


class GroupReturnsAnalyzer:
    """Group returns analyzer: compute and visualize factor-sorted portfolio returns."""

    def __init__(self, factor_name: str = None):
        self.factor_name = factor_name
        self.results: Dict = {}

    # ------------------------------------------------------------------
    # Source A: visualization/group_returns.py
    # ------------------------------------------------------------------

    def compute_group_returns(
        self,
        factor_df: pd.DataFrame,
        price_df: pd.DataFrame,
        n_groups: int = 5,
        split_date: datetime = None,
    ) -> Dict:
        """Compute group returns from factor-sorted portfolios.

        Args:
            factor_df: Factor data (time, symbol, value).
            price_df: Price data (time, symbol, close).
            n_groups: Number of quantile groups.
            split_date: Train/test split date.

        Returns:
            Dict with group_returns_pivot, cumulative_returns, mean_returns,
            std_returns, sharpe, n_groups, samples.
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

        labels = [f"Q{i+1}" for i in range(n_groups)]
        merged["group"] = pd.qcut(merged["value"], q=n_groups, labels=labels)

        group_returns = merged.groupby(["time", "group"])["future_return"].mean().reset_index()
        group_returns_pivot = group_returns.pivot(
            index="time",
            columns="group",
            values="future_return",
        )

        cumulative_returns = (1 + group_returns_pivot).cumprod() - 1

        mean_returns = group_returns_pivot.mean() * 252
        std_returns = group_returns_pivot.std() * np.sqrt(252)
        sharpe = mean_returns / std_returns

        result = {
            "group_returns_pivot": group_returns_pivot,
            "cumulative_returns": cumulative_returns,
            "mean_returns": mean_returns,
            "std_returns": std_returns,
            "sharpe": sharpe,
            "n_groups": n_groups,
            "samples": len(merged),
        }

        if split_date:
            for period in ["train", "test"]:
                period_data = merged[merged["period"] == period]
                if len(period_data) > 100:
                    period_gr = period_data.groupby(["time", "group"])["future_return"].mean()
                    period_pivot = period_gr.unstack(level="group")
                    result[f"mean_returns_{period}"] = period_pivot.mean() * 252
                    result[f"cumulative_returns_{period}"] = (1 + period_pivot).cumprod() - 1

        return result

    def plot_group_returns_bar(
        self,
        mean_returns: pd.Series,
        title: str = None,
        show_values: bool = True,
    ) -> go.Figure:
        """Plot annualized group returns bar chart.

        Args:
            mean_returns: Annualized returns by group.
            title: Chart title.
            show_values: Whether to annotate bars with values.

        Returns:
            Plotly Figure.
        """
        if title is None:
            title = f"{self.factor_name} Group Annualized Returns" if self.factor_name else "Group Annualized Returns"

        color_values = mean_returns.values * 100

        fig = px.bar(
            x=mean_returns.index,
            y=mean_returns.values * 100,
            title=title,
            labels={"x": "Group", "y": "Annualized Return (%)"},
            color=color_values,
            color_continuous_scale="RdYlGn",
        )

        fig.add_hline(y=0, line_dash="dot", line_color="black")

        if show_values:
            for idx, val in mean_returns.items():
                fig.add_annotation(
                    x=idx,
                    y=val * 100,
                    text=f"{val*100:.2f}%",
                    showarrow=False,
                    yshift=10,
                )

        fig.update_layout(
            template="plotly_white",
            height=400,
            coloraxis_colorbar=dict(title="Return (%)"),
        )

        return fig

    def plot_cumulative_returns(
        self,
        cumulative_returns: pd.DataFrame,
        title: str = None,
        show_groups: bool = True,
        highlight_q: str = None,
    ) -> go.Figure:
        """Plot cumulative returns curves.

        Args:
            cumulative_returns: Cumulative returns DataFrame by group.
            title: Chart title.
            show_groups: Whether to show all groups.
            highlight_q: Group to highlight (e.g. 'Q5').

        Returns:
            Plotly Figure.
        """
        if title is None:
            title = f"{self.factor_name} Cumulative Returns" if self.factor_name else "Cumulative Returns"

        if show_groups:
            fig = px.line(
                cumulative_returns,
                title=title,
                labels={"value": "Cumulative Return", "time": "Date", "group": "Group"},
            )

            if highlight_q and highlight_q in cumulative_returns.columns:
                fig.add_trace(
                    go.Scatter(
                        x=cumulative_returns.index,
                        y=cumulative_returns[highlight_q],
                        mode="lines",
                        name=f"{highlight_q} (highlighted)",
                        line=dict(width=4, color="red"),
                    )
                )
        else:
            if "Q5" in cumulative_returns.columns and "Q1" in cumulative_returns.columns:
                long_short = cumulative_returns["Q5"] - cumulative_returns["Q1"]
                fig = px.line(
                    long_short,
                    title=title,
                    labels={"value": "Cumulative Return", "index": "Date"},
                )
            else:
                fig = px.line(cumulative_returns, title=title)

        fig.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.5)

        fig.update_layout(
            template="plotly_white",
            height=400,
            xaxis_title="Date",
            yaxis_title="Cumulative Return",
        )

        return fig

    def plot_long_short(
        self,
        cumulative_returns: pd.DataFrame,
        title: str = None,
    ) -> go.Figure:
        """Plot long-short (Q5 - Q1) cumulative return curve.

        Args:
            cumulative_returns: Cumulative returns DataFrame with Q1 and Q5 columns.
            title: Chart title.

        Returns:
            Plotly Figure.
        """
        if "Q5" not in cumulative_returns.columns or "Q1" not in cumulative_returns.columns:
            raise ValueError("Need both Q1 and Q5 columns")

        if title is None:
            title = f"{self.factor_name} Long-Short (Q5-Q1)" if self.factor_name else "Long-Short (Q5-Q1)"

        long_short = cumulative_returns["Q5"] - cumulative_returns["Q1"]

        fig = px.line(
            long_short,
            title=title,
            labels={"value": "Cumulative Return", "index": "Date"},
        )

        fig.add_hline(y=0, line_dash="dot", line_color="black")

        fig.add_trace(
            go.Scatter(
                x=long_short.index,
                y=long_short,
                fill="tozeroy",
                fillcolor="rgba(0, 255, 0, 0.1)" if long_short.iloc[-1] > 0 else "rgba(255, 0, 0, 0.1)",
                line=dict(color="rgba(0,0,0,0)"),
                showlegend=False,
            )
        )

        fig.update_layout(
            template="plotly_white",
            height=400,
            xaxis_title="Date",
            yaxis_title="Cumulative Return",
        )

        return fig

    def compute_group_statistics(
        self,
        mean_returns: pd.Series,
        std_returns: pd.Series,
        sharpe: pd.Series,
        cumulative_returns: pd.DataFrame,
    ) -> pd.DataFrame:
        """Compute group statistics table.

        Args:
            mean_returns: Annualized returns by group.
            std_returns: Annualized volatility by group.
            sharpe: Sharpe ratio by group.
            cumulative_returns: Cumulative returns DataFrame.

        Returns:
            Statistics DataFrame.
        """
        stats = pd.DataFrame({
            "Group": mean_returns.index,
            "Ann. Return (%)": (mean_returns * 100).round(2),
            "Ann. Vol (%)": (std_returns * 100).round(2),
            "Sharpe": sharpe.round(2),
        })

        max_drawdown = []
        for col in cumulative_returns.columns:
            dd = (cumulative_returns[col] - cumulative_returns[col].cummax()).min()
            max_drawdown.append(dd * 100)

        stats["Max DD (%)"] = [round(dd, 2) for dd in max_drawdown]

        return stats

    # ------------------------------------------------------------------
    # Source B: mining/report/builder.py
    # ------------------------------------------------------------------

    def compute_quintile_detailed_stats(self, gr_result: dict) -> dict:
        """Compute detailed per-quintile stats.

        Args:
            gr_result: Result dict from compute_group_returns.

        Returns:
            Dict with 'quintiles' (list of per-group stat dicts) and
            'ls' (long-short stat dict).
        """
        if "error" in gr_result or "group_returns_pivot" not in gr_result:
            return {"quintiles": [], "ls": {}}

        pivot = gr_result["group_returns_pivot"]
        cum = gr_result["cumulative_returns"]
        quintiles = []
        for q in pivot.columns:
            r = pivot[q]
            ann_ret = float(r.mean() * 252)
            ann_vol = float(r.std() * np.sqrt(252))
            sharpe = ann_ret / ann_vol if ann_vol > 0 else 0
            cum_q = cum[q]
            peak = cum_q.cummax()
            dd = (cum_q - peak).min()
            calmar = ann_ret / abs(dd) if dd != 0 else 0
            win_days = float((r > 0).mean())
            quintiles.append({
                "quintile": str(q),
                "ann_return": round(ann_ret, 6),
                "ann_vol": round(ann_vol, 6),
                "sharpe": round(sharpe, 4),
                "max_dd": round(float(dd), 6),
                "calmar": round(calmar, 4),
                "win_days": round(win_days, 4),
            })

        # LS stats (Q1 - Q5)
        if "Q1" in pivot.columns and "Q5" in pivot.columns:
            ls = pivot["Q1"] - pivot["Q5"]
            ls_cum = (1 + ls).cumprod() - 1
            ann_ret = float(ls.mean() * 252)
            ann_vol = float(ls.std() * np.sqrt(252))
            peak = ls_cum.cummax()
            dd = (ls_cum - peak).min()
            ls_stats = {
                "ann_return": round(ann_ret, 6),
                "ann_vol": round(ann_vol, 6),
                "sharpe": round(ann_ret / ann_vol if ann_vol > 0 else 0, 4),
                "max_dd": round(float(dd), 6),
                "calmar": round(ann_ret / abs(dd) if dd != 0 else 0, 4),
                "win_days": round(float((ls > 0).mean()), 4),
            }
        else:
            ls_stats = {}

        return {"quintiles": quintiles, "ls": ls_stats}

    def compute_monotonicity(self, gr_result: dict) -> float:
        """Compute monotonicity (Spearman rank correlation of group returns).

        Args:
            gr_result: Result dict from compute_group_returns.

        Returns:
            Spearman correlation between group rank and mean return.
        """
        if "mean_returns" not in gr_result:
            return 0
        mr = gr_result["mean_returns"]
        if len(mr) < 3:
            return 0
        ranks = list(range(1, len(mr) + 1))
        corr, _ = sp_stats.spearmanr(ranks, mr.values)
        return round(float(corr), 4)

    def plot_is_vs_oos_bar(self, gr_is: dict, gr_oos: dict) -> go.Figure:
        """Plot in-sample vs out-of-sample quintile returns bar chart.

        Args:
            gr_is: In-sample group returns result dict.
            gr_oos: Out-of-sample group returns result dict.

        Returns:
            Plotly Figure.
        """
        fig = go.Figure()
        if "mean_returns" in gr_is:
            fig.add_trace(go.Bar(
                x=gr_is["mean_returns"].index,
                y=gr_is["mean_returns"].values * 100,
                name="In-Sample",
            ))
        if "mean_returns" in gr_oos:
            fig.add_trace(go.Bar(
                x=gr_oos["mean_returns"].index,
                y=gr_oos["mean_returns"].values * 100,
                name="Out-of-Sample",
            ))
        fig.update_layout(
            title="IS vs OOS Quintile Returns",
            barmode="group",
            template="plotly_white",
            height=350,
        )
        return fig
