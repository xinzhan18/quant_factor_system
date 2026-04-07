"""DecayAnalyzer -- IC decay, distribution, and rebalancing analysis.

Unified analyzer that computes:
  - IC decay across multiple holding periods (including 2-day)
  - Signal half-life and optimal rebalancing recommendation
  - Distribution statistics (absorbed from DistributionAnalyzer)
  - Charts: ic_decay, distribution, coverage
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from concurrent.futures import ThreadPoolExecutor
from core.factor_stats import (
    distribution_stats as _shared_distribution_stats,
)
from report.charts.theme import COLORS, apply_theme


class DecayAnalyzer:
    """Analyze factor signal persistence: IC decay and distribution."""

    DEFAULT_PERIODS = [1, 2, 5, 10, 20, 60]

    def compute(
        self,
        factor_df: pd.DataFrame,
        price_df: pd.DataFrame,
        split_date=None,
        periods: list | None = None,
    ) -> dict:
        """Compute decay, autocorrelation, and distribution in one call.

        Args:
            factor_df: Flat factor values [time, symbol, value]
            price_df: Price data [time, symbol, close]
            split_date: IS/OOS cutoff for distribution stats (optional)
            periods: IC holding periods (default: [1, 2, 5, 10, 20, 60])

        Returns:
            dict with:
                ic_by_period: [{days, ic, ratio}, ...]
                half_life_days: int | None
                optimal_rebalance_days: int
                autocorrelation: [{lag, corr}, ...]
                distribution: {stats_is, stats_oos} or {stats_all}
        """
        if periods is None:
            periods = list(self.DEFAULT_PERIODS)

        ic_by_period = self._compute_ic_decay(factor_df, price_df, periods)
        half_life = self._compute_half_life(ic_by_period)
        optimal_rebalance = self._compute_optimal_rebalance(
            ic_by_period, half_life, periods
        )
        distribution = self._compute_distribution(factor_df, split_date)

        return {
            "ic_by_period": ic_by_period,
            "half_life_days": half_life,
            "optimal_rebalance_days": optimal_rebalance,
            "distribution": distribution,
        }

    # ------------------------------------------------------------------
    # IC Decay
    # ------------------------------------------------------------------

    def _compute_ic_decay(
        self,
        factor_df: pd.DataFrame,
        price_df: pd.DataFrame,
        periods: list[int],
    ) -> list[dict]:
        """Compute IC at each holding period and ratio vs 1-day IC.

        Vectorized: pivots to (date × stock) matrices once, computes cross-sectional
        rank IC for all periods using numpy matrix ops (no Python loop over dates).
        """
        merged = pd.merge(
            factor_df, price_df, on=["time", "symbol"], how="inner"
        )
        merged = merged.sort_values(["symbol", "time"]).reset_index(drop=True)

        # Compute all forward return columns upfront
        for period in periods:
            merged[f"_ret_{period}"] = (
                merged.groupby("symbol")["close"]
                .pct_change(period)
                .shift(-period)
            )

        # Pivot factor to wide (date × stock) and rank cross-sectionally — shared across periods
        factor_wide = merged.pivot(index="time", columns="symbol", values="value")
        factor_ranks = factor_wide.rank(axis=1, na_option="keep")

        def _ic_for_period(period: int):
            """Compute mean IC for one holding period. Reads merged/factor_ranks (no writes)."""
            col = f"_ret_{period}"
            ret_wide = merged.pivot(index="time", columns="symbol", values=col)
            common_cols = factor_ranks.columns.intersection(ret_wide.columns)
            f = factor_ranks[common_cols]
            r = ret_wide[common_cols].rank(axis=1, na_option="keep")

            valid_mask = f.notna() & r.notna()
            good_days = valid_mask.sum(axis=1).pipe(lambda s: s[s >= 30]).index
            if len(good_days) < 10:
                return period, None

            f, r = f.loc[good_days], r.loc[good_days]
            vm = valid_mask.loc[good_days].values
            fv = np.where(vm, f.values, np.nan)
            rv = np.where(vm, r.values, np.nan)
            n_day = vm.sum(axis=1).astype(float)

            mean_f = np.nanmean(fv, axis=1, keepdims=True)
            mean_r = np.nanmean(rv, axis=1, keepdims=True)
            fc = np.where(vm, fv - mean_f, 0.0)
            rc = np.where(vm, rv - mean_r, 0.0)

            var_f = (fc ** 2).sum(axis=1) / n_day
            var_r = (rc ** 2).sum(axis=1) / n_day
            cov = (fc * rc).sum(axis=1) / n_day
            denom = np.sqrt(var_f * var_r)
            daily_ic = np.where(denom > 0, cov / denom, np.nan)
            daily_ic = daily_ic[~np.isnan(daily_ic)]

            if len(daily_ic) == 0:
                return period, None
            return period, float(daily_ic.mean())

        # Run all periods in parallel (pure reads on shared DataFrames — thread-safe)
        with ThreadPoolExecutor(max_workers=len(periods)) as executor:
            period_ics = dict(executor.map(_ic_for_period, periods))

        # Build results in original order; compute ratio after all ICs are known
        base_ic = next((period_ics[p] for p in periods if period_ics.get(p) is not None), None)
        results = []
        for period in periods:
            ic = period_ics.get(period)
            if ic is None:
                continue
            ratio = abs(ic / base_ic) if base_ic and base_ic != 0 else 0.0
            results.append({"days": period, "ic": round(ic, 6), "ratio": round(ratio, 4)})

        return results

    # ------------------------------------------------------------------
    # Half-life & Optimal Rebalance
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_half_life(ic_by_period: list[dict]) -> int | None:
        """First period where ratio <= 0.5, or None.

        Note: This uses ratio-based half-life (report-specific), distinct from
        the interpolation-based estimate_half_life in core.factor_stats which
        is used by mining/metrics.py.
        """
        for entry in ic_by_period:
            if entry["ratio"] <= 0.5:
                return entry["days"]
        return None

    @staticmethod
    def _compute_optimal_rebalance(
        ic_by_period: list[dict],
        half_life: int | None,
        periods: list[int],
    ) -> int:
        """First period where ratio < 0.7; fallback to half_life or max period."""
        for entry in ic_by_period:
            if entry["ratio"] < 0.7:
                return entry["days"]
        if half_life is not None:
            return half_life
        return max(periods) if periods else 1

    # ------------------------------------------------------------------
    # Distribution (absorbed from DistributionAnalyzer)
    # ------------------------------------------------------------------

    def _compute_distribution(
        self, factor_df: pd.DataFrame, split_date=None
    ) -> dict:
        """Compute distribution stats, optionally split by IS/OOS."""
        if split_date is not None:
            split_date = pd.Timestamp(split_date)
            is_df = factor_df[factor_df["time"] < split_date]
            oos_df = factor_df[factor_df["time"] >= split_date]
            return {
                "stats_is": self._dist_stats(is_df),
                "stats_oos": self._dist_stats(oos_df),
            }
        return {"stats_all": self._dist_stats(factor_df)}

    @staticmethod
    def _dist_stats(df: pd.DataFrame) -> dict:
        """Compute mean, std, skew, kurtosis, coverage, nan_ratio.

        Delegates to core.factor_stats.distribution_stats.
        """
        return _shared_distribution_stats(df)

    # ------------------------------------------------------------------
    # Chart Generation
    # ------------------------------------------------------------------

    def generate_charts(
        self, result: dict, name: str = ""
    ) -> dict[str, go.Figure]:
        """Generate all decay-related charts from compute() output.

        Args:
            result: Dict returned by compute().
            name: Factor name for chart titles.

        Returns:
            Dict mapping chart name to Plotly Figure:
                ic_decay, autocorrelation, distribution, coverage.
        """
        charts = {}
        charts["ic_decay"] = self._chart_ic_decay(result["ic_by_period"], name)
        charts["distribution"] = self._chart_distribution(result["distribution"], name)
        charts["coverage"] = self._chart_coverage(result.get("_factor_df"), name)
        return charts

    def _chart_ic_decay(
        self, ic_by_period: list[dict], name: str
    ) -> go.Figure:
        """Bar chart of IC by holding period with decay curve overlay."""
        days = [str(d["days"]) + "d" for d in ic_by_period]
        ics = [d["ic"] for d in ic_by_period]
        ratios = [d["ratio"] for d in ic_by_period]

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=days,
                y=ics,
                name="IC",
                marker_color=COLORS["primary"],
                opacity=0.7,
            )
        )
        fig.add_trace(
            go.Scatter(
                x=days,
                y=ratios,
                name="Decay ratio",
                yaxis="y2",
                mode="lines+markers",
                line=dict(color=COLORS["secondary"]),
            )
        )
        fig.add_hline(y=0, line_dash="dot", line_color="grey")

        fig.update_layout(
            yaxis=dict(title="IC"),
            yaxis2=dict(
                title="Ratio",
                overlaying="y",
                side="right",
                range=[0, 1.2],
            ),
        )
        return apply_theme(fig, title=f"{name} IC Decay".strip())

    def _chart_distribution(
        self, distribution: dict, name: str
    ) -> go.Figure:
        """IS vs OOS factor value histogram overlay."""
        fig = go.Figure()
        _MAX_HIST_PTS = 20_000

        if "stats_is" in distribution and "stats_oos" in distribution:
            # When we have IS/OOS stats, show both distributions
            # We use the stats to generate a synthetic normal overlay
            for label, key, color in [
                ("In-Sample", "stats_is", COLORS["is_period"]),
                ("Out-of-Sample", "stats_oos", COLORS["oos_period"]),
            ]:
                st = distribution[key]
                if st["std"] > 0:
                    rng = np.random.RandomState(42)
                    samples = rng.normal(st["mean"], st["std"], _MAX_HIST_PTS)
                    fig.add_trace(
                        go.Histogram(
                            x=samples,
                            name=label,
                            opacity=0.6,
                            histnorm="probability density",
                            marker_color=color,
                        )
                    )
        elif "stats_all" in distribution:
            st = distribution["stats_all"]
            if st["std"] > 0:
                rng = np.random.RandomState(42)
                samples = rng.normal(st["mean"], st["std"], _MAX_HIST_PTS)
                fig.add_trace(
                    go.Histogram(
                        x=samples,
                        name="All",
                        opacity=0.6,
                        histnorm="probability density",
                        marker_color=COLORS["primary"],
                    )
                )

        fig.update_layout(barmode="overlay")
        return apply_theme(
            fig, title=f"{name} Factor Distribution".strip()
        )

    def _chart_coverage(
        self, factor_df: pd.DataFrame | None, name: str
    ) -> go.Figure:
        """Daily coverage % time series."""
        fig = go.Figure()

        if factor_df is not None and len(factor_df) > 0:
            daily = factor_df.groupby("time")["value"].apply(
                lambda x: x.notna().mean()
            )
            fig.add_trace(
                go.Scatter(
                    x=daily.index,
                    y=daily.values * 100,
                    mode="lines",
                    name="Coverage %",
                    line=dict(color=COLORS["primary"]),
                )
            )
            fig.update_layout(yaxis_title="Coverage %")

        return apply_theme(fig, title=f"{name} Factor Coverage".strip())
