"""ReportDataBuilder — thin orchestrator for factor report generation.

Loads data from DB/YAML, delegates computation to analytics layer,
assembles the final report_data dict, and renders charts to HTML.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from mining.config import MiningConfig
from report.analytics.ic import ICAnalyzer
from report.analytics.groups import GroupReturnsAnalyzer
from report.analytics.decay import DecayAnalyzer
from report.analytics.distribution import DistributionAnalyzer
from report.scorer import CompositeScorer

logger = logging.getLogger(__name__)


class ReportDataBuilder:
    """Orchestrate report data computation for a single factor.

    Usage:
        builder = ReportDataBuilder(factor_id="001", config=MiningConfig())
        data = builder.build()  # returns dict matching report_data.json schema
    """

    def __init__(self, factor_id: str, config: MiningConfig | None = None):
        self.factor_id = factor_id
        self.config = config or MiningConfig()

    def build(self) -> dict:
        """Run full computation pipeline, return report_data dict."""
        factor_meta = self._load_factor_metadata()
        factor_values, price_df = self._load_data_from_db()
        split_date = pd.Timestamp(self.config.test_start)
        name = factor_meta["name"]

        # Split IS / OOS
        fv_is = factor_values[factor_values.index.get_level_values("datetime") < split_date]
        fv_oos = factor_values[factor_values.index.get_level_values("datetime") >= split_date]

        # Flatten for analyzer compatibility
        flat_factor = self._to_flat_df(factor_values)
        flat_is = self._to_flat_df(fv_is) if len(fv_is) > 0 else pd.DataFrame()
        flat_oos = self._to_flat_df(fv_oos) if len(fv_oos) > 0 else pd.DataFrame()

        # --- Analytics ---
        ic = ICAnalyzer(name)
        gr = GroupReturnsAnalyzer(name)
        decay = DecayAnalyzer(name)
        dist = DistributionAnalyzer(name)

        # IC analysis
        try:
            ic_result = ic.compute_ic(flat_factor, price_df, split_date)
        except Exception as exc:
            logger.warning("IC analysis failed, using empty defaults: %s", exc)
            ic_result = {}
        daily_ic = ic_result.get("rolling_ic", pd.DataFrame())

        # IC summary, annual, monthly
        if len(daily_ic) > 0:
            ic_summary_is, ic_summary_oos = ic.compute_ic_summary(daily_ic, split_date)
            annual = ic.compute_annual_breakdown(daily_ic)
            monthly = ic.compute_monthly_heatmap_data(daily_ic)
        else:
            empty = {"ic_mean": 0, "ic_std": 0, "ic_ir": 0, "win_rate": 0, "ic_significant_rate": 0, "n_days": 0}
            ic_summary_is, ic_summary_oos = empty, empty.copy()
            annual, monthly = [], []

        # Distribution stats
        dist_is = dist.compute_stats(fv_is)
        dist_oos = dist.compute_stats(fv_oos) if len(fv_oos) > 100 else None

        # Quintile analysis
        try:
            gr_result = gr.compute_group_returns(flat_factor, price_df, n_groups=5, split_date=split_date)
        except Exception as exc:
            logger.warning("Quintile analysis failed, using empty defaults: %s", exc)
            gr_result = {}

        quintile_stats = gr.compute_quintile_detailed_stats(gr_result)
        monotonicity = gr.compute_monotonicity(gr_result)

        # IS vs OOS quintile
        try:
            gr_is = gr.compute_group_returns(flat_is, price_df, n_groups=5) if len(flat_is) > 100 else {}
        except Exception as exc:
            logger.warning("IS quintile analysis failed: %s", exc)
            gr_is = {}
        try:
            gr_oos = gr.compute_group_returns(flat_oos, price_df, n_groups=5) if len(flat_oos) > 100 else {}
        except Exception as exc:
            logger.warning("OOS quintile analysis failed: %s", exc)
            gr_oos = {}

        # Decay analysis
        decay_result = decay.compute_decay(flat_factor, price_df)
        autocorr = decay.compute_autocorrelation(factor_values)

        # Composite score
        ic_1d = decay_result["ic_by_period"][0]["ic"] if decay_result["ic_by_period"] else 0
        ic_20d_entry = next((d for d in decay_result["ic_by_period"] if d["period"] == 20), None)
        ic_20d = ic_20d_entry["ic"] if ic_20d_entry else ic_1d

        scorer = CompositeScorer()
        scores = scorer.compute(
            ic_mean=ic_result.get("ic_all", 0),
            monotonicity=monotonicity,
            ic_is=ic_result.get("ic_train", ic_result.get("ic_all", 0)),
            ic_oos=ic_result.get("ic_test", ic_result.get("ic_all", 0)),
            ic_1d=ic_1d,
            ic_20d=ic_20d,
            coverage=dist_is.get("coverage", 0.9),
            max_library_corr=self._get_max_library_correlation(),
        )

        # --- Charts ---
        charts_ic = self._generate_ic_charts(ic, ic_result, daily_ic, split_date, monthly)
        charts_quintile = self._generate_quintile_charts(gr, gr_result, gr_is, gr_oos)
        charts_dist = self._generate_dist_charts(dist, fv_is, fv_oos, name)
        charts_decay = self._generate_decay_charts(decay, decay_result, autocorr, name)
        charts_score = self._generate_score_chart(scores, name)

        # --- Assemble ---
        return {
            "factor": factor_meta,
            "preprocessing": {
                "filter_suspend": self.config.filter_suspend,
                "filter_limit": self.config.filter_limit,
                "winsorize_method": self.config.winsorize_method,
                "winsorize_n": self.config.winsorize_n,
                "standardize_method": self.config.standardize_method,
                "neutralize_mode": self.config.neutralize_mode,
            },
            "kpi": {
                "ic_mean_is": ic_summary_is["ic_mean"],
                "ic_mean_oos": ic_summary_oos["ic_mean"],
                "ic_ir": ic_summary_is["ic_ir"],
                "ic_win_rate": ic_summary_is["win_rate"],
                "monotonicity": monotonicity,
                "ls_return": (gr_result.get("mean_returns", pd.Series()).get("Q1", 0)
                              - gr_result.get("mean_returns", pd.Series()).get("Q5", 0)) * 252,
                "composite_grade": scores["composite"]["grade"],
            },
            "distribution": {"stats_is": dist_is, "stats_oos": dist_oos, "charts": charts_dist},
            "ic_analysis": {
                "summary": {"is": ic_summary_is, "oos": ic_summary_oos},
                "annual": annual,
                "monthly_heatmap_data": monthly,
                "charts": charts_ic,
            },
            "quintile": {"stats": quintile_stats["quintiles"], "ls_stats": quintile_stats["ls"], "charts": charts_quintile},
            "decay": {
                "ic_by_period": decay_result["ic_by_period"],
                "autocorrelation": autocorr,
                "half_life_days": decay_result.get("half_life_days"),
                "charts": charts_decay,
            },
            "scores": {**scores, "charts": charts_score},
        }

    # ---- Data Loading (IO boundary) ----

    def _load_factor_metadata(self) -> dict:
        import yaml
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "mining", "library", "factors", f"factor_{self.factor_id}.yaml",
        )
        with open(path) as f:
            meta = yaml.safe_load(f)
        return {
            "id": meta["id"],
            "name": meta["name"],
            "expression": meta["expression"],
            "category": meta.get("category", "other"),
            "batch": meta.get("batch", ""),
            "admitted_at": str(meta.get("admitted_at", "")),
        }

    def _load_data_from_db(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        import psycopg2
        try:
            conn = psycopg2.connect(self.config.system.database.connection_string)
        except psycopg2.Error as exc:
            raise RuntimeError(f"Failed to connect to database: {exc}") from exc
        try:
            fv_sql = "SELECT symbol, trade_date, value FROM mining_factor_values WHERE factor_id = %s ORDER BY trade_date, symbol"
            fv = pd.read_sql(fv_sql, conn, params=[self.factor_id])
            if fv.empty:
                raise ValueError(f"No factor data found in DB for factor_id={self.factor_id!r}")
            fv["trade_date"] = pd.to_datetime(fv["trade_date"])
            fv = fv.set_index(["trade_date", "symbol"]).rename(columns={"value": "factor"})
            fv.index.names = ["datetime", "instrument"]

            symbols = fv.index.get_level_values("instrument").unique().tolist()
            start = fv.index.get_level_values("datetime").min()
            end = fv.index.get_level_values("datetime").max()
            price_sql = "SELECT symbol, time, close FROM price_daily WHERE symbol = ANY(%s) AND time BETWEEN %s AND %s"
            price_df = pd.read_sql(price_sql, conn, params=[symbols, start, end])
            if price_df.empty:
                raise ValueError(
                    f"No price data found in DB for factor_id={self.factor_id!r} "
                    f"(symbols={len(symbols)}, {start} – {end})"
                )
            return fv, price_df
        finally:
            conn.close()

    @staticmethod
    def _to_flat_df(qlib_df: pd.DataFrame) -> pd.DataFrame:
        df = qlib_df.iloc[:, [0]].reset_index()
        df.columns = ["time", "symbol", "value"]
        return df

    def _get_max_library_correlation(self) -> float:
        import yaml
        lib_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "mining", "library", "library.yaml",
        )
        with open(lib_path) as f:
            lib = yaml.safe_load(f)
        factors = lib.get("factors", [])
        if len(factors) <= 1:
            return 0.0
        return 0.0

    # ---- Chart assembly (delegates to analyzers, converts to HTML) ----

    @staticmethod
    def _fig_to_html(fig: go.Figure) -> str:
        return pio.to_html(fig, full_html=False, include_plotlyjs=False)

    def _generate_ic_charts(self, ic: ICAnalyzer, ic_result, daily_ic, split_date, monthly) -> dict:
        charts = {}
        try:
            if "rolling_ic" in ic_result:
                charts["ic_timeseries"] = self._fig_to_html(ic.plot_ic_timeseries(ic_result["rolling_ic"], split_date))
                charts["ic_distribution"] = self._fig_to_html(ic.plot_ic_distribution(ic_result["rolling_ic"]))
            if len(daily_ic) > 0 and "date" in daily_ic.columns:
                charts["rolling_ic"] = self._fig_to_html(ic.plot_rolling_ic_comparison(daily_ic.set_index("date")["IC"]))
                charts["cumulative_ic"] = self._fig_to_html(ic.plot_cumulative_ic(daily_ic))
            if monthly:
                charts["monthly_heatmap"] = self._fig_to_html(ic.plot_monthly_heatmap(monthly))
        except Exception as e:
            logger.warning("IC chart generation error: %s", e)
        return charts

    def _generate_quintile_charts(self, gr: GroupReturnsAnalyzer, gr_result, gr_is, gr_oos) -> dict:
        charts = {}
        try:
            if "mean_returns" in gr_result:
                charts["quintile_bar"] = self._fig_to_html(gr.plot_group_returns_bar(gr_result["mean_returns"]))
            if "cumulative_returns" in gr_result:
                charts["cumulative_returns"] = self._fig_to_html(gr.plot_cumulative_returns(gr_result["cumulative_returns"]))
                if "Q5" in gr_result["cumulative_returns"].columns and "Q1" in gr_result["cumulative_returns"].columns:
                    charts["long_short_curve"] = self._fig_to_html(gr.plot_long_short(gr_result["cumulative_returns"]))
            if "mean_returns" in gr_is and "mean_returns" in gr_oos:
                charts["is_vs_oos_bar"] = self._fig_to_html(gr.plot_is_vs_oos_bar(gr_is, gr_oos))
        except Exception as e:
            logger.warning("Quintile chart generation error: %s", e)
        return charts

    def _generate_dist_charts(self, dist: DistributionAnalyzer, fv_is, fv_oos, name) -> dict:
        charts = {}
        try:
            charts["distribution_overlay"] = self._fig_to_html(dist.plot_distribution(fv_is, fv_oos, name))
            fv_all = pd.concat([fv_is, fv_oos]) if len(fv_oos) > 0 else fv_is
            charts["coverage_timeseries"] = self._fig_to_html(dist.plot_coverage(fv_all))
        except Exception as e:
            logger.warning("Distribution chart error: %s", e)
        return charts

    def _generate_decay_charts(self, decay_analyzer: DecayAnalyzer, decay_result, autocorr, name) -> dict:
        charts = {}
        try:
            if decay_result["ic_by_period"]:
                charts["ic_decay_bar"] = self._fig_to_html(decay_analyzer.plot_ic_decay(decay_result, name))
            if autocorr:
                charts["autocorrelation"] = self._fig_to_html(decay_analyzer.plot_autocorrelation(autocorr, name))
        except Exception as e:
            logger.warning("Decay chart error: %s", e)
        return charts

    @staticmethod
    def _generate_score_chart(scores, name) -> dict:
        charts = {}
        try:
            dims = scores["dimensions"]
            names = [d["name"] for d in dims]
            values = [d["score"] for d in dims]
            fig = go.Figure(data=go.Scatterpolar(
                r=values + [values[0]], theta=names + [names[0]], fill="toself",
            ))
            fig.update_layout(
                title=f"{name} Composite Score", template="plotly_white", height=400,
                polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            )
            charts["radar"] = pio.to_html(fig, full_html=False, include_plotlyjs=False)
        except Exception as e:
            logger.warning("Score chart error: %s", e)
        return charts

    def save(self, output_dir: str) -> str:
        """Build report data and save to JSON."""
        os.makedirs(output_dir, exist_ok=True)
        data = self.build()
        path = os.path.join(output_dir, "report_data.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        logger.info("Report data saved to %s", path)
        return path


def main():
    parser = argparse.ArgumentParser(description="Build factor report data")
    parser.add_argument("--factor-id", required=True)
    parser.add_argument("--output-dir", required=True)
    args = parser.parse_args()

    builder = ReportDataBuilder(args.factor_id)
    builder.save(args.output_dir)


if __name__ == "__main__":
    main()
