"""ConditionalAnalyzer -- market regime + volatility conditioning analysis.

Splits IC analysis by market regime (bull/bear/range) and volatility regime
(high/low), plus annual IC with dominant-regime labeling.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import spearmanr

from core.factor_stats import (
    daily_cross_sectional_ic as _shared_daily_ic,
    ic_summary as _shared_ic_summary,
)
from report.charts.theme import apply_theme, COLORS


class ConditionalAnalyzer:
    """Conditional IC analyzer: regime- and volatility-segmented IC."""

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def compute(self, merged_df: pd.DataFrame, price_df: pd.DataFrame) -> dict:
        """Compute conditional IC analysis.

        Args:
            merged_df: From data_prep.merge_factor_price
                       [time, symbol, value, future_return].
            price_df: Raw price data [time, symbol, close] -- needed for
                      regime computation.

        Returns:
            dict with keys:
                regime_ic: {bull: {ic, icir, n_days},
                            bear: {ic, icir, n_days},
                            range: {ic, icir, n_days}}
                vol_regime_ic: {high: {ic, icir, n_days},
                                low: {ic, icir, n_days}}
                annual_ic: [{year, rank_ic, icir, regime}, ...]
                size_ic: None (reserved for L1 data)
                industry_ic: None (reserved for L1 data)
        """
        market_regime = self._compute_market_regimes(price_df)
        vol_regime = self._compute_vol_regimes(price_df)

        # Daily cross-sectional Spearman IC
        daily_ic = self._compute_daily_ic(merged_df)

        # Per market-regime IC
        regime_ic = {}
        for label in ["bull", "bear", "range"]:
            dates_in_regime = market_regime[market_regime == label].index
            ic_sub = daily_ic[daily_ic.index.isin(dates_in_regime)]
            regime_ic[label] = self._summarize_ic(ic_sub)

        # Per volatility-regime IC
        vol_regime_ic = {}
        for label in ["high", "low"]:
            dates_in_regime = vol_regime[vol_regime == label].index
            ic_sub = daily_ic[daily_ic.index.isin(dates_in_regime)]
            vol_regime_ic[label] = self._summarize_ic(ic_sub)

        # Annual IC with dominant regime
        annual_ic = self._compute_annual_ic(daily_ic, market_regime)

        return {
            "regime_ic": regime_ic,
            "vol_regime_ic": vol_regime_ic,
            "annual_ic": annual_ic,
            "size_ic": None,
            "industry_ic": None,
        }

    def generate_charts(self, result: dict) -> dict:
        """Return dict of chart_name -> go.Figure for 2 charts.

        Charts:
            conditional_ic: Grouped bar chart -- IC by market regime + vol regime.
            annual_ic: Annual IC bars with regime color coding.
        """
        charts = {}
        charts["conditional_ic"] = self._chart_conditional_ic(result)
        charts["annual_ic"] = self._chart_annual_ic(result)
        return charts

    # ------------------------------------------------------------------
    # Regime computation
    # ------------------------------------------------------------------

    def _compute_market_regimes(self, price_df: pd.DataFrame, window: int = 60) -> pd.Series:
        """Market breadth indicator: equal-weight universe mean return over
        rolling window.

        Bull: > +10%, Bear: < -10%, Range: otherwise.

        Note: NOT a CSI300 proxy -- captures broad market breadth skewed
        toward small/mid caps.
        """
        daily_market = price_df.groupby("time")["close"].mean().sort_index()
        daily_ret = daily_market.pct_change()
        cum_ret = daily_ret.rolling(window).sum()
        regime = pd.Series("range", index=cum_ret.index)
        regime[cum_ret > 0.10] = "bull"
        regime[cum_ret < -0.10] = "bear"
        return regime  # Series: date -> regime string

    def _compute_vol_regimes(self, price_df: pd.DataFrame, window: int = 20) -> pd.Series:
        """Split dates into high/low volatility by median of realized vol."""
        daily_ret = price_df.groupby("time")["close"].mean().pct_change()
        rvol = daily_ret.rolling(window).std() * np.sqrt(252)
        median_vol = rvol.median()
        regime = pd.Series("low", index=rvol.index)
        regime[rvol > median_vol] = "high"
        return regime

    # ------------------------------------------------------------------
    # IC computation helpers
    # ------------------------------------------------------------------

    def _compute_daily_ic(self, merged_df: pd.DataFrame) -> pd.Series:
        """Compute daily cross-sectional Spearman IC.

        Delegates to core.factor_stats.daily_cross_sectional_ic.

        Returns:
            pd.Series with date index and IC values.
        """
        factor_df = merged_df[["time", "symbol", "value"]].copy()
        returns_df = merged_df[["time", "symbol", "future_return"]].rename(
            columns={"future_return": "value"},
        ).copy()
        return _shared_daily_ic(factor_df, returns_df, method="spearman", min_obs=30)

    @staticmethod
    def _summarize_ic(ic_series: pd.Series) -> dict:
        """Summarize an IC series into {ic, icir, n_days}.

        Delegates core computation to core.factor_stats.ic_summary.
        """
        shared = _shared_ic_summary(ic_series)
        ic_mean = shared["ic_mean"] if not np.isnan(shared["ic_mean"]) else 0.0
        icir = shared["ic_ir"] if not np.isnan(shared.get("ic_ir", np.nan)) else 0.0
        n = len(ic_series.dropna())
        return {
            "ic": round(float(ic_mean), 6),
            "icir": round(float(icir), 4),
            "n_days": n,
        }

    def _compute_annual_ic(
        self, daily_ic: pd.Series, market_regime: pd.Series
    ) -> list:
        """Group daily IC by year, compute stats, label with dominant regime.

        Returns:
            List of dicts with {year, rank_ic, icir, regime}.
        """
        if len(daily_ic) == 0:
            return []

        result = []
        for year, group in daily_ic.groupby(daily_ic.index.year):
            ic = group.dropna()
            if len(ic) < 20:
                continue

            mean_ic = float(ic.mean())
            std_ic = float(ic.std())
            icir = mean_ic / std_ic if std_ic > 0 else 0.0

            # Dominant regime for this year
            year_regime = market_regime[market_regime.index.year == year]
            if len(year_regime) > 0:
                dominant = year_regime.value_counts().idxmax()
            else:
                dominant = "range"

            result.append({
                "year": int(year),
                "rank_ic": round(mean_ic, 4),
                "icir": round(icir, 4),
                "regime": dominant,
            })
        return result

    # ------------------------------------------------------------------
    # Chart generation
    # ------------------------------------------------------------------

    def _chart_conditional_ic(self, result: dict) -> go.Figure:
        """Grouped bar chart: IC by market regime + volatility regime."""
        fig = go.Figure()

        # Market regime bars
        regime_ic = result["regime_ic"]
        market_labels = ["bull", "bear", "range"]
        market_colors = {
            "bull": COLORS["positive"],
            "bear": COLORS["negative"],
            "range": COLORS["neutral"],
        }
        fig.add_trace(go.Bar(
            x=[f"Market: {r.capitalize()}" for r in market_labels],
            y=[regime_ic[r]["ic"] for r in market_labels],
            marker_color=[market_colors[r] for r in market_labels],
            name="Market Regime",
            text=[f"n={regime_ic[r]['n_days']}" for r in market_labels],
            textposition="outside",
        ))

        # Volatility regime bars
        vol_ic = result["vol_regime_ic"]
        vol_labels = ["high", "low"]
        vol_colors = {
            "high": COLORS["secondary"],
            "low": COLORS["primary"],
        }
        fig.add_trace(go.Bar(
            x=[f"Vol: {v.capitalize()}" for v in vol_labels],
            y=[vol_ic[v]["ic"] for v in vol_labels],
            marker_color=[vol_colors[v] for v in vol_labels],
            name="Volatility Regime",
            text=[f"n={vol_ic[v]['n_days']}" for v in vol_labels],
            textposition="outside",
        ))

        fig.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.5)
        fig.update_layout(
            height=400,
            xaxis_title="Regime",
            yaxis_title="Mean IC",
            showlegend=False,
        )
        return apply_theme(fig, "IC by Market & Volatility Regime")

    def _chart_annual_ic(self, result: dict) -> go.Figure:
        """Annual IC bars with regime color coding."""
        annual = result["annual_ic"]
        if not annual:
            fig = go.Figure()
            fig.update_layout(height=400)
            return apply_theme(fig, "Annual IC by Regime")

        regime_colors = {
            "bull": COLORS["positive"],
            "bear": COLORS["negative"],
            "range": COLORS["neutral"],
        }

        years = [str(a["year"]) for a in annual]
        ics = [a["rank_ic"] for a in annual]
        colors = [regime_colors.get(a["regime"], COLORS["neutral"]) for a in annual]
        regimes = [a["regime"].capitalize() for a in annual]

        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=years,
            y=ics,
            marker_color=colors,
            text=regimes,
            textposition="outside",
            name="Annual IC",
        ))

        fig.add_hline(y=0, line_dash="dot", line_color="black", opacity=0.5)
        fig.update_layout(
            height=400,
            xaxis_title="Year",
            yaxis_title="Mean Rank IC",
        )
        return apply_theme(fig, "Annual IC by Regime")
