"""UniquenessAnalyzer -- factor independence analysis with correlation matrix and incremental IC.

Computes cross-sectional Spearman rank correlations between a target factor and
all factors in the library, identifies the most correlated factors, and optionally
computes incremental IC (IC of residuals after removing library exposures via
cross-sectional OLS).
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import spearmanr

from core.factor_stats import (
    incremental_ic as _shared_incremental_ic,
    pairwise_cross_sectional_corr as _shared_pairwise_corr,
)
from report.charts.theme import apply_theme, COLORS


class UniquenessAnalyzer:
    """Analyze factor uniqueness relative to an existing factor library."""

    def compute(
        self,
        target_df: pd.DataFrame,
        library_factors: dict[str, pd.DataFrame],
        merged_df: pd.DataFrame | None = None,
    ) -> dict:
        """Compute uniqueness metrics.

        Args:
            target_df: Factor values with columns [time, symbol, value].
            library_factors: Mapping of factor_id to DataFrame [time, symbol, value].
            merged_df: If provided (with future_return column), compute incremental IC.

        Returns:
            dict with:
                max_corr: float (highest absolute avg cross-sectional rank correlation)
                max_corr_factor: str (factor ID of highest correlated)
                top5_correlated: [{factor, corr}, ...] sorted descending by abs corr
                incremental_ic: float | None
                incremental_icir: float | None
        """
        # Compute pairwise correlations with all library factors
        corr_results = {}
        for fid, fdf in library_factors.items():
            c = self._cross_sectional_corr(target_df, fdf)
            if c is not None:
                corr_results[fid] = c

        if corr_results:
            # Sort by absolute correlation descending
            sorted_corrs = sorted(
                corr_results.items(), key=lambda x: abs(x[1]), reverse=True
            )
            max_corr_factor, max_corr = sorted_corrs[0]
            max_corr = abs(max_corr)
            top5 = [
                {"factor": fid, "corr": abs(c)} for fid, c in sorted_corrs[:5]
            ]
        else:
            max_corr = 0.0
            max_corr_factor = ""
            top5 = []

        # Incremental IC
        incremental_ic = None
        incremental_icir = None
        if merged_df is not None and library_factors:
            incremental_ic, incremental_icir = self._compute_incremental_ic(
                target_df, library_factors, merged_df
            )

        return {
            "max_corr": max_corr,
            "max_corr_factor": max_corr_factor,
            "top5_correlated": top5,
            "incremental_ic": incremental_ic,
            "incremental_icir": incremental_icir,
            "all_correlations": corr_results,
        }

    def generate_charts(self, result: dict) -> dict:
        """Return dict with 'correlation_bar' -> go.Figure."""
        charts = {}
        charts["correlation_bar"] = self._chart_correlation_bar(result)
        return charts

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _cross_sectional_corr(self, df_a: pd.DataFrame, df_b: pd.DataFrame) -> float | None:
        """Average cross-sectional Spearman rank correlation between two factor DFs.

        Delegates to core.factor_stats.pairwise_cross_sectional_corr.
        """
        return _shared_pairwise_corr(df_a, df_b, min_obs=30)

    def _compute_incremental_ic(
        self,
        target_df: pd.DataFrame,
        library_factors: dict[str, pd.DataFrame],
        merged_df: pd.DataFrame,
    ) -> tuple[float | None, float | None]:
        """Compute IC of residuals after removing library factor exposures.

        Delegates to core.factor_stats.incremental_ic.
        """
        returns_df = merged_df[["time", "symbol", "future_return"]].rename(
            columns={"future_return": "value"},
        ).drop_duplicates()
        return _shared_incremental_ic(
            target_df, returns_df, library_factors, min_obs=30,
        )

    # ------------------------------------------------------------------
    # Chart generation
    # ------------------------------------------------------------------

    def _chart_correlation_bar(self, result: dict) -> go.Figure:
        """Horizontal bar chart of correlations with all library factors, sorted descending.

        Args:
            result: Output of self.compute().

        Returns:
            go.Figure with horizontal bar chart.
        """
        all_corrs = result.get("all_correlations", {})

        if not all_corrs:
            fig = go.Figure()
            fig.update_layout(height=300)
            return apply_theme(fig, "Factor Correlations")

        # Sort by absolute correlation descending
        sorted_items = sorted(all_corrs.items(), key=lambda x: abs(x[1]), reverse=True)
        factors = [item[0] for item in sorted_items]
        corrs = [abs(item[1]) for item in sorted_items]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=corrs,
            y=factors,
            orientation="h",
            marker_color=COLORS["primary"],
            name="Abs Correlation",
        ))

        fig.update_layout(
            height=max(300, 40 * len(factors)),
            xaxis_title="Absolute Correlation",
            yaxis_title="Factor",
            yaxis=dict(autorange="reversed"),
        )

        return apply_theme(fig, "Factor Correlations")
