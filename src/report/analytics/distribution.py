"""DistributionAnalyzer -- factor value distribution statistics and plots.

Extracted from mining/report/builder.py.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from scipy import stats as sp_stats


class DistributionAnalyzer:
    """Analyze factor value distributions: stats, histogram overlay, coverage."""

    def __init__(self, factor_name: str = None):
        self.factor_name = factor_name

    def compute_stats(self, factor_values: pd.DataFrame) -> dict:
        """Compute distribution statistics for factor values.

        Args:
            factor_values: Multi-indexed DataFrame (datetime, instrument) with
                           factor values in the first column.

        Returns:
            Dict with mean, std, skewness, kurtosis, coverage, nan_ratio.
        """
        vals = factor_values.iloc[:, 0]
        total = len(vals)
        non_nan = vals.dropna()
        if len(non_nan) < 10:
            return {"mean": 0, "std": 0, "skewness": 0, "kurtosis": 0, "coverage": 0, "nan_ratio": 1.0}
        return {
            "mean": round(float(non_nan.mean()), 6),
            "std": round(float(non_nan.std()), 6),
            "skewness": round(float(sp_stats.skew(non_nan)), 4),
            "kurtosis": round(float(sp_stats.kurtosis(non_nan)), 4),
            "coverage": round(len(non_nan) / total, 4) if total > 0 else 0,
            "nan_ratio": round(1 - len(non_nan) / total, 4) if total > 0 else 1.0,
        }

    def plot_distribution(
        self,
        fv_is: pd.DataFrame,
        fv_oos: pd.DataFrame,
        name: str = None,
    ) -> go.Figure:
        """Plot IS vs OOS factor distribution overlay histogram.

        Args:
            fv_is: In-sample factor values (multi-indexed DataFrame).
            fv_oos: Out-of-sample factor values (multi-indexed DataFrame).
            name: Factor name for chart title.

        Returns:
            Plotly Figure.
        """
        if name is None:
            name = self.factor_name or ""

        _MAX_HIST_PTS = 20_000
        is_vals = fv_is.iloc[:, 0].dropna()
        if len(is_vals) > _MAX_HIST_PTS:
            is_vals = is_vals.sample(_MAX_HIST_PTS, random_state=42)

        fig = go.Figure()
        fig.add_trace(go.Histogram(
            x=is_vals, name="In-Sample", opacity=0.6, histnorm="probability density",
        ))

        if len(fv_oos) > 0:
            oos_vals = fv_oos.iloc[:, 0].dropna()
            if len(oos_vals) > _MAX_HIST_PTS:
                oos_vals = oos_vals.sample(_MAX_HIST_PTS, random_state=42)
            fig.add_trace(go.Histogram(
                x=oos_vals, name="Out-of-Sample", opacity=0.6, histnorm="probability density",
            ))

        fig.update_layout(
            title=f"{name} Factor Distribution IS vs OOS".strip(),
            template="plotly_white",
            height=350,
            barmode="overlay",
        )
        return fig

    def plot_coverage(self, factor_values: pd.DataFrame) -> go.Figure:
        """Plot factor coverage rate over time.

        Args:
            factor_values: Multi-indexed DataFrame (datetime, instrument) with
                           factor values in the first column.

        Returns:
            Plotly Figure.
        """
        coverage = factor_values.groupby(level="datetime").apply(
            lambda x: x.iloc[:, 0].notna().mean()
        )
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=coverage.index, y=coverage.values, mode="lines", name="Coverage",
        ))
        fig.update_layout(
            title="Factor Coverage Rate",
            template="plotly_white",
            height=300,
        )
        return fig
