"""ProfitAnalyzer -- quintile profitability analysis with extended metrics.

Replaces and upgrades GroupReturnsAnalyzer with Sortino, Calmar, Page's trend
test, annual decomposition, and IS vs OOS comparison.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import spearmanr, page_trend_test

from core.metrics import (
    annualize_return,
    annualize_volatility,
    sharpe_ratio,
    sortino_ratio,
    calmar_ratio,
    max_drawdown,
    max_drawdown_duration,
)
from report.charts.theme import apply_theme, COLORS

GROUPS = ["Q1", "Q2", "Q3", "Q4", "Q5"]


class ProfitAnalyzer:
    """Quintile profitability analyzer with extended risk metrics."""

    # ------------------------------------------------------------------
    # Core compute
    # ------------------------------------------------------------------

    def compute(self, merged_df: pd.DataFrame, split_date) -> dict:
        """Compute profitability analysis on pre-merged data.

        Args:
            merged_df: Output of data_prep.merge_factor_price
                       [time, symbol, value, future_return]
            split_date: IS/OOS cutoff date

        Returns:
            dict with keys: stats, ls_stats, monotonicity,
            page_test_pvalue, annual_group_returns,
            long_contribution, short_contribution, is_vs_oos
        """
        split_date = pd.Timestamp(split_date)

        # -- 1. Group assignment per date --
        pivot = self._build_group_pivot(merged_df)

        # -- 2. Per-group stats --
        stats = self._compute_group_stats(pivot)

        # -- 3. Monotonicity --
        mean_rets = [pivot[q].mean() for q in GROUPS]
        mono_corr, _ = spearmanr(range(1, 6), mean_rets)
        monotonicity = round(float(mono_corr), 4) if not np.isnan(mono_corr) else 0.0

        # -- 4. L/S portfolio (auto-detect direction) --
        if monotonicity >= 0:
            ls_daily = pivot["Q5"] - pivot["Q1"]
        else:
            ls_daily = pivot["Q1"] - pivot["Q5"]
        ls_stats = self._series_stats(ls_daily, label="L/S")

        # -- 5. Page's trend test --
        page_pvalue = self._page_trend_test(pivot, monotonicity)

        # -- 6. Annual decomposition --
        annual_group_returns = self._annual_decomposition(pivot)

        # -- 7. L/S contribution --
        long_contribution, short_contribution = self._ls_contribution(
            pivot, monotonicity
        )

        # -- 8. IS vs OOS --
        is_vs_oos = self._is_vs_oos(merged_df, split_date)

        # -- Assemble extras for charts --
        return {
            "stats": stats,
            "ls_stats": ls_stats,
            "monotonicity": monotonicity,
            "page_test_pvalue": page_pvalue,
            "annual_group_returns": annual_group_returns,
            "long_contribution": long_contribution,
            "short_contribution": short_contribution,
            "is_vs_oos": is_vs_oos,
            # Internal data for chart generation
            "_pivot": pivot,
            "_ls_daily": ls_daily,
        }

    # ------------------------------------------------------------------
    # Charts
    # ------------------------------------------------------------------

    def generate_charts(self, result: dict) -> dict:
        """Return dict of chart_name -> go.Figure for 5 charts."""
        pivot = result["_pivot"]
        ls_daily = result["_ls_daily"]

        charts = {}
        charts["quintile_bar"] = self._chart_quintile_bar(result["stats"])
        charts["cumulative_returns"] = self._chart_cumulative_returns(pivot, ls_daily)
        charts["long_short"] = self._chart_long_short(ls_daily)
        charts["is_vs_oos_bar"] = self._chart_is_vs_oos_bar(result["is_vs_oos"])
        charts["annual_group_returns"] = self._chart_annual_heatmap(
            result["annual_group_returns"]
        )
        return charts

    # ------------------------------------------------------------------
    # Internal: data wrangling
    # ------------------------------------------------------------------

    @staticmethod
    def _build_group_pivot(merged_df: pd.DataFrame) -> pd.DataFrame:
        """Assign quintile groups per date and return a daily group-return pivot."""
        df = merged_df.copy()
        df = df.dropna(subset=["value", "future_return"])

        # Assign groups per date
        def _qcut_safe(sub):
            try:
                return pd.qcut(sub, 5, labels=GROUPS)
            except ValueError:
                # Not enough unique values for 5 bins
                return pd.Series(np.nan, index=sub.index)

        df["group"] = df.groupby("time")["value"].transform(_qcut_safe)
        df = df.dropna(subset=["group"])

        # Equal-weight mean return per date+group
        group_ret = (
            df.groupby(["time", "group"], observed=False)["future_return"]
            .mean()
            .reset_index()
        )
        pivot = group_ret.pivot(index="time", columns="group", values="future_return")
        pivot = pivot.sort_index()

        # Ensure all group columns present
        for q in GROUPS:
            if q not in pivot.columns:
                pivot[q] = np.nan
        pivot = pivot[GROUPS]
        return pivot

    @staticmethod
    def _series_stats(daily_returns: pd.Series, label: str = "") -> dict:
        """Compute full stat dict from a daily return series."""
        ann_ret = annualize_return(daily_returns)
        ann_vol = annualize_volatility(daily_returns)
        cum = (1 + daily_returns).cumprod()
        dd = max_drawdown(cum)
        dd_dur = max_drawdown_duration(cum)
        sr = sharpe_ratio(daily_returns)
        so = sortino_ratio(daily_returns)
        cal = calmar_ratio(ann_ret, dd)

        def _safe(v):
            return round(float(v), 6) if np.isfinite(v) else 0.0

        return {
            "group": label,
            "ann_return": _safe(ann_ret),
            "ann_vol": _safe(ann_vol),
            "sharpe": _safe(sr),
            "sortino": _safe(so),
            "calmar": _safe(cal),
            "max_dd": _safe(dd),
            "max_dd_duration": int(dd_dur),
        }

    def _compute_group_stats(self, pivot: pd.DataFrame) -> list[dict]:
        """Compute stats for each of the 5 quintile groups."""
        stats = []
        for q in GROUPS:
            s = self._series_stats(pivot[q].dropna(), label=q)
            stats.append(s)
        return stats

    # ------------------------------------------------------------------
    # Internal: metrics
    # ------------------------------------------------------------------

    @staticmethod
    def _page_trend_test(pivot: pd.DataFrame, monotonicity: float) -> float:
        """Run Page's trend test on daily group returns matrix."""
        # page_trend_test expects (replications x treatments) matrix
        # treatments = 5 groups, replications = dates
        data = pivot[GROUPS].dropna()
        if len(data) < 5:
            return 1.0

        matrix = data.values  # shape (n_dates, 5)

        # predicted_ranks should match the monotonicity direction
        if monotonicity >= 0:
            predicted_ranks = [1, 2, 3, 4, 5]
        else:
            predicted_ranks = [5, 4, 3, 2, 1]

        try:
            result = page_trend_test(matrix, predicted_ranks=predicted_ranks)
            return float(result.pvalue)
        except Exception:
            return 1.0

    @staticmethod
    def _annual_decomposition(pivot: pd.DataFrame) -> list[dict]:
        """Group daily returns by year, compute annualized return per group."""
        pivot = pivot.copy()
        pivot["year"] = pivot.index.year
        rows = []
        for year, grp in pivot.groupby("year"):
            row = {"year": int(year)}
            for q in GROUPS:
                row[q] = round(float(annualize_return(grp[q].dropna())), 6)
            rows.append(row)
        return rows

    @staticmethod
    def _ls_contribution(
        pivot: pd.DataFrame, monotonicity: float
    ) -> tuple[float, float]:
        """Compute long/short contribution to L/S return."""
        if monotonicity >= 0:
            long_q, short_q = "Q5", "Q1"
        else:
            long_q, short_q = "Q1", "Q5"

        long_ret = abs(annualize_return(pivot[long_q].dropna()))
        short_ret = abs(annualize_return(pivot[short_q].dropna()))
        total = long_ret + short_ret
        if total == 0:
            return 0.5, 0.5
        return round(long_ret / total, 4), round(short_ret / total, 4)

    def _is_vs_oos(self, merged_df: pd.DataFrame, split_date) -> dict:
        """Compute stats for IS and OOS periods separately."""
        is_df = merged_df[merged_df["time"] < split_date]
        oos_df = merged_df[merged_df["time"] >= split_date]

        result = {}
        for label, sub_df in [("is", is_df), ("oos", oos_df)]:
            if len(sub_df) < 50:
                result[label] = {"stats": [], "monotonicity": 0.0}
                continue
            pivot = self._build_group_pivot(sub_df)
            stats = self._compute_group_stats(pivot)
            mean_rets = [pivot[q].mean() for q in GROUPS]
            corr, _ = spearmanr(range(1, 6), mean_rets)
            mono = round(float(corr), 4) if not np.isnan(corr) else 0.0
            result[label] = {"stats": stats, "monotonicity": mono}
        return result

    # ------------------------------------------------------------------
    # Internal: charts
    # ------------------------------------------------------------------

    @staticmethod
    def _chart_quintile_bar(stats: list[dict]) -> go.Figure:
        """Annualized returns by quintile bar chart."""
        groups = [s["group"] for s in stats]
        returns_pct = [s["ann_return"] * 100 for s in stats]
        colors = COLORS["quintile"]

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=groups,
                y=returns_pct,
                marker_color=colors,
                text=[f"{r:.2f}%" for r in returns_pct],
                textposition="outside",
            )
        )
        fig.add_hline(y=0, line_dash="dot", line_color="grey")
        apply_theme(fig, title="Quintile Annualized Returns")
        fig.update_layout(
            yaxis_title="Annualized Return (%)",
            xaxis_title="Quintile",
            height=400,
        )
        return fig

    @staticmethod
    def _chart_cumulative_returns(
        pivot: pd.DataFrame, ls_daily: pd.Series
    ) -> go.Figure:
        """Cumulative return curves for Q1-Q5 + L/S."""
        fig = go.Figure()
        colors = COLORS["quintile"]
        for i, q in enumerate(GROUPS):
            cum = (1 + pivot[q]).cumprod() - 1
            fig.add_trace(
                go.Scatter(
                    x=cum.index,
                    y=cum.values,
                    mode="lines",
                    name=q,
                    line=dict(color=colors[i]),
                )
            )
        # L/S
        ls_cum = (1 + ls_daily).cumprod() - 1
        fig.add_trace(
            go.Scatter(
                x=ls_cum.index,
                y=ls_cum.values,
                mode="lines",
                name="L/S",
                line=dict(color=COLORS["long_short"], dash="dash", width=2),
            )
        )
        fig.add_hline(y=0, line_dash="dot", line_color="grey", opacity=0.5)
        apply_theme(fig, title="Cumulative Returns by Quintile")
        fig.update_layout(
            yaxis_title="Cumulative Return",
            xaxis_title="Date",
            height=400,
        )
        return fig

    @staticmethod
    def _chart_long_short(ls_daily: pd.Series) -> go.Figure:
        """L/S cumulative return with drawdown shading."""
        ls_cum = (1 + ls_daily).cumprod() - 1
        running_max = ls_cum.cummax()
        dd = ls_cum - running_max

        fig = go.Figure()
        # Drawdown fill area
        fig.add_trace(
            go.Scatter(
                x=dd.index,
                y=dd.values,
                fill="tozeroy",
                fillcolor="rgba(239,85,59,0.15)",
                line=dict(color="rgba(239,85,59,0.4)", width=1),
                name="Drawdown",
                yaxis="y2",
            )
        )
        # Cumulative return line
        fig.add_trace(
            go.Scatter(
                x=ls_cum.index,
                y=ls_cum.values,
                mode="lines",
                name="L/S Cumulative",
                line=dict(color=COLORS["long_short"], width=2),
            )
        )
        fig.add_hline(y=0, line_dash="dot", line_color="grey", opacity=0.5)
        apply_theme(fig, title="Long-Short Portfolio")
        fig.update_layout(
            yaxis_title="Cumulative Return",
            yaxis2=dict(
                title="Drawdown",
                overlaying="y",
                side="right",
                showgrid=False,
                range=[dd.min() * 3 if dd.min() < 0 else -0.1, 0],
            ),
            xaxis_title="Date",
            height=400,
        )
        return fig

    @staticmethod
    def _chart_is_vs_oos_bar(is_vs_oos: dict) -> go.Figure:
        """IS vs OOS grouped bar comparison."""
        fig = go.Figure()

        for label, color in [
            ("is", COLORS["is_period"]),
            ("oos", COLORS["oos_period"]),
        ]:
            period_data = is_vs_oos.get(label, {})
            stats = period_data.get("stats", [])
            if stats:
                groups = [s["group"] for s in stats]
                rets = [s["ann_return"] * 100 for s in stats]
                display = "In-Sample" if label == "is" else "Out-of-Sample"
                fig.add_trace(
                    go.Bar(x=groups, y=rets, name=display, marker_color=color)
                )

        fig.update_layout(barmode="group")
        fig.add_hline(y=0, line_dash="dot", line_color="grey", opacity=0.5)
        apply_theme(fig, title="IS vs OOS Quintile Returns")
        fig.update_layout(
            yaxis_title="Annualized Return (%)",
            xaxis_title="Quintile",
            height=400,
        )
        return fig

    @staticmethod
    def _chart_annual_heatmap(annual_group_returns: list[dict]) -> go.Figure:
        """Year x Quintile heatmap of annualized returns."""
        if not annual_group_returns:
            fig = go.Figure()
            apply_theme(fig, title="Annual Group Returns")
            return fig

        df = pd.DataFrame(annual_group_returns)
        years = df["year"].astype(str).tolist()
        z = df[GROUPS].values * 100  # to percent

        fig = go.Figure(
            data=go.Heatmap(
                z=z,
                x=GROUPS,
                y=years,
                colorscale="RdYlGn",
                text=[[f"{v:.1f}%" for v in row] for row in z],
                texttemplate="%{text}",
                colorbar=dict(title="Ann. Ret (%)"),
            )
        )
        apply_theme(fig, title="Annual Group Returns")
        fig.update_layout(
            xaxis_title="Quintile",
            yaxis_title="Year",
            height=max(300, 60 * len(years)),
        )
        return fig
