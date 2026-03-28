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

        Args:
            df_a: Factor A with columns [time, symbol, value].
            df_b: Factor B with columns [time, symbol, value].

        Returns:
            Mean daily cross-sectional Spearman correlation, or None if insufficient data.
        """
        merged = df_a.merge(df_b, on=["time", "symbol"], suffixes=("_a", "_b"))
        if len(merged) < 100:
            return None
        daily_corrs = []
        for _, group in merged.groupby("time"):
            if len(group) >= 30:
                corr, _ = spearmanr(group["value_a"], group["value_b"])
                daily_corrs.append(corr)
        return float(np.mean(daily_corrs)) if daily_corrs else None

    def _compute_incremental_ic(
        self,
        target_df: pd.DataFrame,
        library_factors: dict[str, pd.DataFrame],
        merged_df: pd.DataFrame,
    ) -> tuple[float | None, float | None]:
        """Compute IC of residuals after removing library factor exposures.

        For each date, regress target factor values on all library factor values
        (cross-sectional OLS via np.linalg.lstsq), then compute Spearman correlation
        of residuals vs future_return.

        Args:
            target_df: Target factor [time, symbol, value].
            library_factors: Library factor DataFrames.
            merged_df: DataFrame with [time, symbol, future_return].

        Returns:
            Tuple of (incremental_ic_mean, incremental_icir), or (None, None).
        """
        target = target_df.rename(columns={"value": "target"})
        daily_residual_ics = []

        for date, group in merged_df.groupby("time"):
            date_target = target[target["time"] == date][["symbol", "target"]]
            lib_vals = date_target[["symbol"]].copy()

            for fid, fdf in library_factors.items():
                fdate = fdf[fdf["time"] == date][["symbol", "value"]].rename(
                    columns={"value": fid}
                )
                lib_vals = lib_vals.merge(fdate, on="symbol", how="inner")

            if len(lib_vals) < 30:
                continue

            lib_cols = [c for c in lib_vals.columns if c != "symbol"]
            if not lib_cols:
                continue

            date_merged = date_target.merge(lib_vals, on="symbol")
            date_merged = date_merged.merge(
                group[["symbol", "future_return"]].drop_duplicates(), on="symbol"
            )

            if len(date_merged) < 30:
                continue

            X = date_merged[lib_cols].values
            y = date_merged["target"].values

            try:
                coeffs, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
                residual = y - X @ coeffs
                corr, _ = spearmanr(residual, date_merged["future_return"].values)
                daily_residual_ics.append(corr)
            except (np.linalg.LinAlgError, ValueError):
                continue

        if not daily_residual_ics:
            return None, None

        ics = np.array(daily_residual_ics)
        ic_mean = float(np.mean(ics))
        ic_std = float(np.std(ics))
        icir = float(ic_mean / ic_std) if ic_std > 0 else 0.0
        return ic_mean, icir

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
