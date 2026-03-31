"""RiskAttributionAnalyzer -- industry IC, size exposure, and style correlation analysis.

Answers Chapter 3: "Is this Alpha or Beta?" by decomposing factor predictive power
across industry groups, market cap quintiles, and style factor correlations.

Data requirements (L1):
    - ref_industry DB table: {symbol: industry_code} static mapping
    - $market_cap, $pb_ratio, $pe_ratio from Qlib (passed in as style_dfs)
"""
from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from core.factor_stats import (
    daily_cross_sectional_ic as _shared_daily_ic,
    pairwise_cross_sectional_corr as _shared_pairwise_corr,
)
from report.charts.theme import COLORS, apply_theme

logger = logging.getLogger(__name__)


class RiskAttributionAnalyzer:
    """Decompose factor risk attribution: industry, size, and style exposures."""

    def compute(
        self,
        factor_df: pd.DataFrame,
        merged: pd.DataFrame,
        style_dfs: dict[str, pd.DataFrame],
        conn_string: str,
        symbols: list[str],
    ) -> dict:
        """Compute risk attribution analysis.

        Args:
            factor_df: Flat factor values [time, symbol, value].
            merged: Factor + price merged [time, symbol, value, future_return].
            style_dfs: Dict of style factor DataFrames, keyed by name
                       (e.g. "market_cap", "pb_ratio", "pe_ratio"),
                       each with columns [time, symbol, value].
            conn_string: psycopg2 connection string for ref_industry lookup.
            symbols: Unique symbols from factor_df.

        Returns:
            dict with:
                industry_ic: [{industry, ic, n_stocks}, ...] sorted by abs(ic) desc
                size_exposure: {factor_size_corr, ic_by_quintile} or None
                style_corr: [{style, corr}, ...]
                has_industry: bool
                has_size: bool
                has_style: bool
        """
        industry_map = self._load_industry_map(conn_string, symbols)
        industry_ic = self._compute_industry_ic(merged, industry_map)
        size_exposure = self._compute_size_exposure(
            factor_df, merged, style_dfs.get("market_cap")
        )
        style_corr = self._compute_style_correlations(factor_df, style_dfs)

        return {
            "industry_ic": industry_ic,
            "size_exposure": size_exposure,
            "style_corr": style_corr,
            "has_industry": len(industry_ic) > 0,
            "has_size": size_exposure is not None,
            "has_style": len(style_corr) > 0,
        }

    def generate_charts(self, result: dict) -> dict[str, go.Figure]:
        """Generate risk attribution charts.

        Returns:
            Dict with 0–3 entries: industry_ic, size_exposure, style_corr.
        """
        charts = {}
        if result["has_industry"]:
            charts["industry_ic"] = self._chart_industry_ic(result["industry_ic"])
        if result["has_size"]:
            charts["size_exposure"] = self._chart_size_exposure(result["size_exposure"])
        if result["has_style"]:
            charts["style_corr"] = self._chart_style_corr(result["style_corr"])
        return charts

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    @staticmethod
    def _load_industry_map(conn_string: str, symbols: list[str]) -> dict[str, str]:
        """Load static symbol→industry_code mapping from ref_industry table."""
        try:
            import psycopg2
            conn = psycopg2.connect(conn_string)
            try:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT symbol, industry_code FROM ref_industry WHERE symbol = ANY(%s)",
                        (symbols,),
                    )
                    return {row[0]: row[1] for row in cur.fetchall()}
            finally:
                conn.close()
        except Exception as exc:
            logger.warning("Failed to load industry map: %s", exc)
            return {}

    # ------------------------------------------------------------------
    # Industry IC decomposition
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_industry_ic(
        merged: pd.DataFrame, industry_map: dict[str, str]
    ) -> list[dict]:
        """Compute mean cross-sectional rank IC per industry.

        Uses _shared_daily_ic (vectorized) on each industry's sub-DataFrame.
        """
        if not industry_map:
            return []

        df = merged.copy()
        df["industry"] = df["symbol"].map(industry_map)
        df = df.dropna(subset=["industry", "value", "future_return"])
        if df.empty:
            return []

        results = []
        for industry, group in df.groupby("industry"):
            n_stocks = group["symbol"].nunique()
            if n_stocks < 3:
                continue
            factor_sub = group[["time", "symbol", "value"]]
            ret_sub = (
                group[["time", "symbol", "future_return"]]
                .rename(columns={"future_return": "value"})
            )
            daily_ic = _shared_daily_ic(factor_sub, ret_sub, min_obs=5)
            if daily_ic.empty:
                continue
            ic_mean = float(daily_ic.mean())
            if not np.isfinite(ic_mean):
                continue
            results.append({
                "industry": str(industry),
                "ic": round(ic_mean, 6),
                "n_stocks": n_stocks,
            })

        return sorted(results, key=lambda x: abs(x["ic"]), reverse=True)

    # ------------------------------------------------------------------
    # Size exposure
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_size_exposure(
        factor_df: pd.DataFrame,
        merged: pd.DataFrame,
        market_cap_df: pd.DataFrame | None,
    ) -> dict | None:
        """Compute factor-size correlation and IC by market cap quintile."""
        if market_cap_df is None or market_cap_df.empty:
            return None

        # Log-transform market cap for correlation
        log_cap_df = market_cap_df.copy()
        log_cap_df["value"] = np.log(log_cap_df["value"].clip(lower=1e-6))
        log_cap_df = log_cap_df.dropna(subset=["value"])

        factor_size_corr = _shared_pairwise_corr(factor_df, log_cap_df, min_obs=30)
        if factor_size_corr is None:
            return None

        # IC by market cap quintile
        ic_by_quintile = _compute_ic_by_quintile(factor_df, merged, log_cap_df)

        return {
            "factor_size_corr": round(factor_size_corr, 4),
            "ic_by_quintile": ic_by_quintile,
        }

    # ------------------------------------------------------------------
    # Style correlations
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_style_correlations(
        factor_df: pd.DataFrame, style_dfs: dict[str, pd.DataFrame]
    ) -> list[dict]:
        """Compute mean cross-sectional Spearman corr with each style factor."""
        results = []
        for style_name, style_df in style_dfs.items():
            if style_df is None or style_df.empty:
                continue
            corr = _shared_pairwise_corr(factor_df, style_df, min_obs=30)
            if corr is not None and np.isfinite(corr):
                results.append({"style": style_name, "corr": round(corr, 4)})
        return results

    # ------------------------------------------------------------------
    # Chart generation
    # ------------------------------------------------------------------

    @staticmethod
    def _chart_industry_ic(industry_ic: list[dict]) -> go.Figure:
        """Horizontal bar chart of IC by industry (top 15 by abs IC)."""
        top = industry_ic[:15]
        industries = [d["industry"] for d in top]
        ics = [d["ic"] for d in top]
        colors = [COLORS["positive"] if v >= 0 else COLORS["negative"] for v in ics]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=ics,
            y=industries,
            orientation="h",
            marker_color=colors,
            name="IC Mean",
        ))
        fig.add_vline(x=0, line_dash="dot", line_color="grey")
        fig.update_layout(
            height=max(300, 30 * len(top)),
            xaxis_title="IC Mean",
            yaxis=dict(autorange="reversed"),
        )
        return apply_theme(fig, title="Industry IC Decomposition")

    @staticmethod
    def _chart_size_exposure(size_exposure: dict) -> go.Figure:
        """Bar chart of IC by market cap quintile."""
        quintiles = size_exposure.get("ic_by_quintile", [])
        if not quintiles:
            fig = go.Figure()
            return apply_theme(fig, title="Size Exposure")

        labels = [q["quintile"] for q in quintiles]
        ics = [q["ic"] for q in quintiles]
        colors = [COLORS["positive"] if v >= 0 else COLORS["negative"] for v in ics]
        corr = size_exposure.get("factor_size_corr", 0.0)

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=labels,
            y=ics,
            marker_color=colors,
            name="IC by Size Quintile",
        ))
        fig.add_hline(y=0, line_dash="dot", line_color="grey")
        fig.update_layout(
            xaxis_title="Market Cap Quintile (Q1=Small, Q5=Large)",
            yaxis_title="IC Mean",
        )
        return apply_theme(
            fig, title=f"Size Exposure (Factor-Size Corr: {corr:+.3f})"
        )

    @staticmethod
    def _chart_style_corr(style_corr: list[dict]) -> go.Figure:
        """Horizontal bar chart of correlations with style factors."""
        styles = [d["style"] for d in style_corr]
        corrs = [d["corr"] for d in style_corr]
        colors = [COLORS["positive"] if v >= 0 else COLORS["negative"] for v in corrs]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=corrs,
            y=styles,
            orientation="h",
            marker_color=colors,
            name="Correlation",
        ))
        fig.add_vline(x=0, line_dash="dot", line_color="grey")
        fig.update_layout(
            height=max(200, 60 * len(styles)),
            xaxis_title="Spearman Correlation",
            yaxis=dict(autorange="reversed"),
        )
        return apply_theme(fig, title="Style Factor Correlations")


# ------------------------------------------------------------------
# Helper (module-level, not part of class)
# ------------------------------------------------------------------


def _compute_ic_by_quintile(
    factor_df: pd.DataFrame,
    merged: pd.DataFrame,
    log_cap_df: pd.DataFrame,
    n_quintiles: int = 5,
) -> list[dict]:
    """Compute factor IC within each market cap quintile.

    Per trading date, assigns stocks to size quintiles based on log_mktcap,
    then computes cross-sectional IC within each quintile across all dates.
    """
    # Build combined panel: factor value + future_return + log_mktcap
    panel = merged[["time", "symbol", "value", "future_return"]].copy()
    panel = panel.merge(
        log_cap_df[["time", "symbol", "value"]].rename(columns={"value": "log_cap"}),
        on=["time", "symbol"],
        how="inner",
    )
    panel = panel.dropna(subset=["value", "future_return", "log_cap"])
    if panel.empty:
        return []

    # Per date, assign size quintile
    def assign_quintile(grp):
        grp = grp.copy()
        try:
            grp["quintile"] = pd.qcut(
                grp["log_cap"], q=n_quintiles,
                labels=[f"Q{i+1}" for i in range(n_quintiles)],
                duplicates="drop",
            )
        except ValueError:
            grp["quintile"] = None
        return grp

    panel = panel.groupby("time", group_keys=False).apply(assign_quintile)
    panel = panel.dropna(subset=["quintile"])
    if panel.empty:
        return []

    results = []
    quintile_labels = [f"Q{i+1}" for i in range(n_quintiles)]
    for q_label in quintile_labels:
        sub = panel[panel["quintile"] == q_label]
        if sub["symbol"].nunique() < 3:
            results.append({"quintile": q_label, "ic": 0.0})
            continue
        factor_sub = sub[["time", "symbol", "value"]]
        ret_sub = sub[["time", "symbol", "future_return"]].rename(
            columns={"future_return": "value"}
        )
        daily_ic = _shared_daily_ic(factor_sub, ret_sub, min_obs=5)
        ic_mean = float(daily_ic.mean()) if not daily_ic.empty else 0.0
        results.append({
            "quintile": q_label,
            "ic": round(ic_mean, 6) if np.isfinite(ic_mean) else 0.0,
        })

    return results
