"""DecayAnalyzer -- IC decay, autocorrelation, distribution, and rebalancing analysis.

Unified analyzer that computes:
  - IC decay across multiple holding periods (including 2-day)
  - Signal half-life and optimal rebalancing recommendation
  - Factor autocorrelation at various lags
  - Distribution statistics (absorbed from DistributionAnalyzer)
  - Charts: ic_decay, autocorrelation, distribution, coverage
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy.stats import spearmanr, skew, kurtosis

from report.charts.theme import COLORS, apply_theme


class DecayAnalyzer:
    """Analyze factor signal persistence: IC decay, autocorrelation, distribution."""

    DEFAULT_PERIODS = [1, 2, 5, 10, 20, 60]
    AUTOCORR_LAGS = [1, 2, 3, 5, 10, 15, 20]
    MAX_AUTOCORR_DATES = 50

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
        autocorrelation = self._compute_autocorrelation(factor_df)
        distribution = self._compute_distribution(factor_df, split_date)

        return {
            "ic_by_period": ic_by_period,
            "half_life_days": half_life,
            "optimal_rebalance_days": optimal_rebalance,
            "autocorrelation": autocorrelation,
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
        """Compute IC at each holding period and ratio vs 1-day IC."""
        merged = pd.merge(
            factor_df, price_df, on=["time", "symbol"], how="inner"
        )
        merged = merged.sort_values(["symbol", "time"]).reset_index(drop=True)

        results = []
        base_ic = None

        for period in periods:
            fwd_ret = (
                merged.groupby("symbol")["close"]
                .pct_change(period)
                .shift(-period)
            )
            merged[f"_ret_{period}"] = fwd_ret

            valid = merged.dropna(subset=["value", f"_ret_{period}"])
            if len(valid) < 100:
                continue

            col = f"_ret_{period}"
            daily_ic = (
                valid.groupby("time")[["value", col]]
                .apply(
                    lambda g: _spearman_corr(g["value"], g.iloc[:, 1])
                    if len(g) > 3
                    else np.nan
                )
                .dropna()
            )
            if len(daily_ic) == 0:
                continue

            ic = float(daily_ic.mean())
            if base_ic is None:
                base_ic = ic
            ratio = abs(ic / base_ic) if base_ic != 0 else 0.0
            results.append({
                "days": period,
                "ic": round(ic, 6),
                "ratio": round(ratio, 4),
            })

        return results

    # ------------------------------------------------------------------
    # Half-life & Optimal Rebalance
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_half_life(ic_by_period: list[dict]) -> int | None:
        """First period where ratio <= 0.5, or None."""
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
    # Autocorrelation
    # ------------------------------------------------------------------

    def _compute_autocorrelation(self, factor_df: pd.DataFrame) -> list[dict]:
        """Cross-sectional Spearman correlation between factor at t and t-lag."""
        # Use sorted list of Timestamps for consistent type matching
        unique_dates = sorted(factor_df["time"].unique())
        # Build a date-indexed dict for fast lookup (keys are Timestamps)
        date_groups = {
            pd.Timestamp(d): g
            for d, g in factor_df.groupby("time")
        }

        result = []
        for lag in self.AUTOCORR_LAGS:
            if lag >= len(unique_dates):
                continue

            eligible_indices = list(range(lag, len(unique_dates)))
            # Sample up to MAX_AUTOCORR_DATES
            if len(eligible_indices) > self.MAX_AUTOCORR_DATES:
                rng = np.random.RandomState(42)
                eligible_indices = list(
                    rng.choice(
                        eligible_indices,
                        self.MAX_AUTOCORR_DATES,
                        replace=False,
                    )
                )

            corrs = []
            for idx in eligible_indices:
                date = pd.Timestamp(unique_dates[idx])
                prev_date = pd.Timestamp(unique_dates[idx - lag])

                curr_group = date_groups.get(date)
                prev_group = date_groups.get(prev_date)
                if curr_group is None or prev_group is None:
                    continue

                curr = curr_group.set_index("symbol")["value"]
                prev = prev_group.set_index("symbol")["value"]
                common = curr.index.intersection(prev.index)
                if len(common) > 10:
                    c = _spearman_corr(curr[common], prev[common])
                    if not np.isnan(c):
                        corrs.append(c)

            if corrs:
                result.append({
                    "lag": lag,
                    "corr": round(float(np.mean(corrs)), 4),
                })

        return result

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
        """Compute mean, std, skew, kurtosis, coverage, nan_ratio."""
        vals = df["value"]
        total = len(vals)
        non_nan = vals.dropna()

        if len(non_nan) < 10:
            return {
                "mean": 0.0,
                "std": 0.0,
                "skew": 0.0,
                "kurtosis": 0.0,
                "coverage": 0.0,
                "nan_ratio": 1.0,
            }

        nan_ratio = 1 - len(non_nan) / total if total > 0 else 1.0
        return {
            "mean": round(float(non_nan.mean()), 6),
            "std": round(float(non_nan.std()), 6),
            "skew": round(float(skew(non_nan)), 4),
            "kurtosis": round(float(kurtosis(non_nan)), 4),
            "coverage": round(1 - nan_ratio, 4),
            "nan_ratio": round(nan_ratio, 4),
        }

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
        charts["autocorrelation"] = self._chart_autocorrelation(
            result["autocorrelation"], name
        )
        charts["distribution"] = self._chart_distribution(
            result["distribution"], name
        )
        charts["coverage"] = self._chart_coverage(
            result.get("_factor_df"), name
        )
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

    def _chart_autocorrelation(
        self, autocorr: list[dict], name: str
    ) -> go.Figure:
        """Lag vs autocorrelation line chart."""
        lags = [a["lag"] for a in autocorr]
        corrs = [a["corr"] for a in autocorr]

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=lags,
                y=corrs,
                mode="lines+markers",
                name="Autocorrelation",
                line=dict(color=COLORS["primary"]),
            )
        )
        fig.update_layout(
            xaxis_title="Lag (days)",
            yaxis_title="Spearman Correlation",
        )
        return apply_theme(fig, title=f"{name} Factor Autocorrelation".strip())

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


# ------------------------------------------------------------------
# Helper
# ------------------------------------------------------------------


def _spearman_corr(a: pd.Series, b: pd.Series) -> float:
    """Compute Spearman correlation, returning NaN on failure."""
    try:
        mask = a.notna() & b.notna()
        if mask.sum() < 4:
            return np.nan
        corr, _ = spearmanr(a[mask], b[mask])
        return corr
    except Exception:
        return np.nan
