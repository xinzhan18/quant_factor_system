"""ReportDataBuilder — compute all metrics and charts for factor reports."""
from __future__ import annotations

import argparse
import json
import logging
import os
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
from scipy import stats as sp_stats

from mining.config import MiningConfig
from mining.report.scorer import CompositeScorer

logger = logging.getLogger(__name__)

# Market regime lookup (CSI 300 annual returns)
_REGIME_LOOKUP = {
    2015: "bear", 2016: "sideways", 2017: "bull", 2018: "bear", 2019: "bull",
    2020: "bull", 2021: "sideways", 2022: "bear", 2023: "bear", 2024: "sideways",
    2025: "sideways",
}


class ReportDataBuilder:
    """Compute all metrics and Plotly charts for a factor report.

    Usage:
        builder = ReportDataBuilder(factor_id="001", config=MiningConfig())
        data = builder.build()  # returns dict matching report_data.json schema
    """

    def __init__(self, factor_id: str, config: MiningConfig | None = None):
        self.factor_id = factor_id
        self.config = config or MiningConfig()
        self._conn = None

    def build(self) -> dict:
        """Run full computation pipeline, return report_data dict."""
        factor_meta = self._load_factor_metadata()
        factor_values, price_df = self._load_data_from_db()
        split_date = pd.Timestamp(self.config.test_start)

        # Split IS / OOS
        fv_is = factor_values[factor_values.index.get_level_values("datetime") < split_date]
        fv_oos = factor_values[factor_values.index.get_level_values("datetime") >= split_date]

        # Flatten for ic_analyzer / group_returns compatibility
        flat_factor = self._to_flat_df(factor_values)
        flat_is = self._to_flat_df(fv_is) if len(fv_is) > 0 else pd.DataFrame()
        flat_oos = self._to_flat_df(fv_oos) if len(fv_oos) > 0 else pd.DataFrame()

        # IC analysis (reuse ic_analyzer)
        from visualization.ic_analyzer import ICAnalyzer
        ic = ICAnalyzer(factor_meta["name"])
        try:
            ic_result = ic.compute_ic(flat_factor, price_df, split_date)
        except Exception as exc:
            logger.warning("IC analysis failed, using empty defaults: %s", exc)
            ic_result = {}
        daily_ic = ic_result.get("rolling_ic", pd.DataFrame())

        # Distribution stats
        dist_is = self._compute_distribution_stats(fv_is)
        dist_oos = self._compute_distribution_stats(fv_oos) if len(fv_oos) > 100 else None

        # Annual + monthly breakdown
        annual = self._compute_annual_breakdown(daily_ic) if len(daily_ic) > 0 else []
        monthly = self._compute_monthly_heatmap_data(daily_ic) if len(daily_ic) > 0 else []

        # Quintile analysis (reuse group_returns)
        from visualization.group_returns import GroupReturnsAnalyzer
        gr = GroupReturnsAnalyzer(factor_meta["name"])
        try:
            gr_result = gr.compute_group_returns(flat_factor, price_df, n_groups=5, split_date=split_date)
        except Exception as exc:
            logger.warning("Quintile analysis failed, using empty defaults: %s", exc)
            gr_result = {}

        # Quintile detailed stats
        quintile_stats = self._compute_quintile_detailed_stats(gr_result)

        # IS vs OOS quintile
        try:
            gr_is = gr.compute_group_returns(flat_is, price_df, n_groups=5) if len(flat_is) > 100 else {}
        except Exception as exc:
            logger.warning("IS quintile analysis failed, using empty defaults: %s", exc)
            gr_is = {}
        try:
            gr_oos = gr.compute_group_returns(flat_oos, price_df, n_groups=5) if len(flat_oos) > 100 else {}
        except Exception as exc:
            logger.warning("OOS quintile analysis failed, using empty defaults: %s", exc)
            gr_oos = {}

        # Decay analysis
        decay = self._compute_decay(flat_factor, price_df)

        # Factor autocorrelation
        autocorr = self._compute_autocorrelation(factor_values)

        # Composite score
        ic_1d = decay["ic_by_period"][0]["ic"] if decay["ic_by_period"] else 0
        ic_20d_entry = next((d for d in decay["ic_by_period"] if d["period"] == 20), None)
        ic_20d = ic_20d_entry["ic"] if ic_20d_entry else ic_1d
        max_lib_corr = self._get_max_library_correlation()

        scorer = CompositeScorer()
        scores = scorer.compute(
            ic_mean=ic_result.get("ic_all", 0),
            monotonicity=gr_result.get("monotonicity", 0) if "monotonicity" in gr_result else self._compute_monotonicity(gr_result),
            ic_is=ic_result.get("ic_train", ic_result.get("ic_all", 0)),
            ic_oos=ic_result.get("ic_test", ic_result.get("ic_all", 0)),
            ic_1d=ic_1d,
            ic_20d=ic_20d,
            coverage=dist_is.get("coverage", 0.9),
            max_library_corr=max_lib_corr,
        )

        # Generate all charts
        charts_ic = self._generate_ic_charts(ic, ic_result, daily_ic, split_date, annual, monthly)
        charts_quintile = self._generate_quintile_charts(gr, gr_result, gr_is, gr_oos)
        charts_dist = self._generate_distribution_charts(fv_is, fv_oos, factor_meta["name"])
        charts_decay = self._generate_decay_charts(decay, autocorr, factor_meta["name"])
        charts_score = self._generate_score_charts(scores, factor_meta["name"])

        # IC summary stats
        if len(daily_ic) > 0:
            ic_summary_is, ic_summary_oos = self._compute_ic_summary(daily_ic, split_date)
        else:
            empty = {"ic_mean": 0, "ic_std": 0, "ic_ir": 0, "win_rate": 0, "ic_significant_rate": 0, "n_days": 0}
            ic_summary_is, ic_summary_oos = empty, empty.copy()

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
                "monotonicity": self._compute_monotonicity(gr_result),
                "ls_return": (gr_result.get("mean_returns", pd.Series()).get("Q1", 0) - gr_result.get("mean_returns", pd.Series()).get("Q5", 0)),
                "composite_grade": scores["composite"]["grade"],
            },
            "distribution": {
                "stats_is": dist_is,
                "stats_oos": dist_oos,
                "charts": charts_dist,
            },
            "ic_analysis": {
                "summary": {"is": ic_summary_is, "oos": ic_summary_oos},
                "annual": annual,
                "monthly_heatmap_data": monthly,
                "charts": charts_ic,
            },
            "quintile": {
                "stats": quintile_stats["quintiles"],
                "ls_stats": quintile_stats["ls"],
                "charts": charts_quintile,
            },
            "decay": {
                "ic_by_period": decay["ic_by_period"],
                "autocorrelation": autocorr,
                "half_life_days": decay.get("half_life_days", None),
                "charts": charts_decay,
            },
            "scores": {**scores, "charts": charts_score},
        }

    # ---- Data Loading ----

    def _load_factor_metadata(self) -> dict:
        """Load factor YAML from library."""
        import yaml
        path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "library", "factors", f"factor_{self.factor_id}.yaml",
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
        """Load factor values and price data from DB."""
        import psycopg2
        try:
            conn = psycopg2.connect(self.config.system.database.connection_string)
        except psycopg2.Error as exc:
            raise RuntimeError(
                f"Failed to connect to database: {exc}"
            ) from exc
        try:
            # Factor values
            fv_sql = "SELECT symbol, trade_date, value FROM mining_factor_values WHERE factor_id = %s ORDER BY trade_date, symbol"
            fv = pd.read_sql(fv_sql, conn, params=[self.factor_id])
            if fv.empty:
                raise ValueError(
                    f"No factor data found in DB for factor_id={self.factor_id!r}"
                )
            fv["trade_date"] = pd.to_datetime(fv["trade_date"])
            fv = fv.set_index(["trade_date", "symbol"]).rename(columns={"value": "factor"})
            fv.index.names = ["datetime", "instrument"]

            # Price data
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

    # ---- Distribution ----

    def _compute_distribution_stats(self, factor_values: pd.DataFrame) -> dict:
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

    # ---- IC Analysis ----

    def _compute_ic_summary(self, daily_ic: pd.DataFrame, split_date) -> tuple[dict, dict]:
        """Compute IC summary stats for IS and OOS from daily IC DataFrame."""
        def _summarize(ic_series):
            if len(ic_series) < 5:
                return {"ic_mean": 0, "ic_std": 0, "ic_ir": 0, "win_rate": 0, "ic_significant_rate": 0, "n_days": 0}
            m = float(ic_series.mean())
            s = float(ic_series.std())
            return {
                "ic_mean": round(m, 6),
                "ic_std": round(s, 6),
                "ic_ir": round(m / s, 4) if s > 0 else 0,
                "win_rate": round(float((ic_series > 0).mean()), 4),
                "ic_significant_rate": round(float((ic_series.abs() > 0.02).mean()), 4),
                "n_days": len(ic_series),
            }

        if "period" in daily_ic.columns:
            is_ic = daily_ic[daily_ic["period"] == "train"]["IC"]
            oos_ic = daily_ic[daily_ic["period"] == "test"]["IC"]
        else:
            is_ic = daily_ic[daily_ic["date"] < split_date]["IC"]
            oos_ic = daily_ic[daily_ic["date"] >= split_date]["IC"]

        return _summarize(is_ic), _summarize(oos_ic)

    def _compute_annual_breakdown(self, daily_ic: pd.DataFrame) -> list[dict]:
        daily_ic = daily_ic.copy()
        daily_ic["year"] = pd.to_datetime(daily_ic["date"]).dt.year
        result = []
        for year, group in daily_ic.groupby("year"):
            ic = group["IC"]
            if len(ic) < 20:
                continue
            m = float(ic.mean())
            s = float(ic.std())
            result.append({
                "year": int(year),
                "ic_mean": round(m, 4),
                "ic_ir": round(m / s, 4) if s > 0 else 0,
                "win_rate": round(float((ic > 0).mean()), 4),
                "regime": _REGIME_LOOKUP.get(int(year), "sideways"),
            })
        return result

    def _compute_monthly_heatmap_data(self, daily_ic: pd.DataFrame) -> list:
        daily_ic = daily_ic.copy()
        daily_ic["date"] = pd.to_datetime(daily_ic["date"])
        daily_ic["year"] = daily_ic["date"].dt.year
        daily_ic["month"] = daily_ic["date"].dt.month
        grouped = daily_ic.groupby(["year", "month"])["IC"].mean()
        return [[int(y), int(m), round(float(v), 4)] for (y, m), v in grouped.items()]

    # ---- Quintile ----

    def _compute_quintile_detailed_stats(self, gr_result: dict) -> dict:
        """Compute detailed per-quintile stats: ann_return, ann_vol, sharpe, max_dd, calmar, win_days."""
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

    def _compute_monotonicity(self, gr_result: dict) -> float:
        if "mean_returns" not in gr_result:
            return 0
        mr = gr_result["mean_returns"]
        if len(mr) < 3:
            return 0
        ranks = list(range(1, len(mr) + 1))
        corr, _ = sp_stats.spearmanr(ranks, mr.values)
        return round(float(corr), 4)

    # ---- Decay ----

    def _compute_decay(self, flat_factor: pd.DataFrame, price_df: pd.DataFrame) -> dict:
        merged = pd.merge(flat_factor, price_df, on=["time", "symbol"], how="inner")
        merged = merged.sort_values(["symbol", "time"])
        periods = [1, 5, 10, 20, 60]
        results = []
        base_ic = None
        for period in periods:
            merged[f"ret_{period}"] = merged.groupby("symbol")["close"].pct_change(period).shift(-period)
            valid = merged.dropna(subset=["value", f"ret_{period}"])
            if len(valid) < 100:
                continue
            daily_ic = valid.groupby("time").apply(
                lambda x: x["value"].corr(x[f"ret_{period}"], method="spearman") if len(x) > 3 else np.nan
            ).dropna()
            ic = float(daily_ic.mean())
            if base_ic is None:
                base_ic = ic
            ratio = abs(ic / base_ic) if base_ic != 0 else 0
            results.append({"period": period, "ic": round(ic, 6), "ratio": round(ratio, 4)})
        # Estimate half-life
        half_life = None
        for r in results:
            if r["ratio"] <= 0.5:
                half_life = r["period"]
                break
        return {"ic_by_period": results, "half_life_days": half_life}

    def _compute_autocorrelation(self, factor_values: pd.DataFrame) -> list:
        """Compute factor value autocorrelation at lags 1-20."""
        result = []
        unique_dates = factor_values.index.get_level_values("datetime").unique()
        for lag in [1, 2, 3, 5, 10, 15, 20]:
            corrs = []
            for date in unique_dates[lag:]:
                try:
                    date_loc = unique_dates.get_loc(date)
                    if date_loc < lag:
                        continue
                    current = factor_values.xs(date, level="datetime").iloc[:, 0]
                    prev_date = unique_dates[date_loc - lag]
                    prev = factor_values.xs(prev_date, level="datetime").iloc[:, 0]
                    common = current.index.intersection(prev.index)
                    if len(common) > 10:
                        corrs.append(current[common].corr(prev[common], method="spearman"))
                except (KeyError, IndexError):
                    continue
                if len(corrs) >= 50:
                    break
            if corrs:
                result.append({"lag": lag, "corr": round(float(np.mean(corrs)), 4)})
        return result

    def _get_max_library_correlation(self) -> float:
        """Get max correlation with other library factors. Returns 0 if only factor."""
        import yaml
        lib_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "library", "library.yaml")
        with open(lib_path) as f:
            lib = yaml.safe_load(f)
        factors = lib.get("factors", [])
        if len(factors) <= 1:
            return 0.0
        # TODO: Full computation requires loading all factor values from DB.
        return 0.0

    # ---- Chart Generation (all return HTML div strings) ----

    def _fig_to_html(self, fig: go.Figure) -> str:
        return pio.to_html(fig, full_html=False, include_plotlyjs=False)

    def _generate_ic_charts(self, ic_analyzer, ic_result, daily_ic, split_date, annual, monthly) -> dict:
        charts = {}
        try:
            if "rolling_ic" in ic_result:
                fig = ic_analyzer.plot_ic_timeseries(ic_result["rolling_ic"], split_date)
                charts["ic_timeseries"] = self._fig_to_html(fig)
                fig = ic_analyzer.plot_ic_distribution(ic_result["rolling_ic"])
                charts["ic_distribution"] = self._fig_to_html(fig)
            if len(daily_ic) > 0 and "date" in daily_ic.columns:
                fig = ic_analyzer.plot_rolling_ic_comparison(daily_ic.set_index("date")["IC"])
                charts["rolling_ic"] = self._fig_to_html(fig)
            # Cumulative IC (NEW)
            if len(daily_ic) > 0:
                cum_ic = daily_ic["IC"].cumsum()
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=daily_ic["date"], y=cum_ic, mode="lines", name="Cumulative IC"))
                fig.add_hline(y=0, line_dash="dot", line_color="black")
                fig.update_layout(title="Cumulative IC", template="plotly_white", height=350,
                                  xaxis_title="Date", yaxis_title="Cumulative IC")
                charts["cumulative_ic"] = self._fig_to_html(fig)
            # Monthly heatmap (NEW)
            if monthly:
                years = sorted(set(r[0] for r in monthly))
                months = list(range(1, 13))
                z = [[next((r[2] for r in monthly if r[0] == y and r[1] == m), None) for m in months] for y in years]
                fig = go.Figure(data=go.Heatmap(
                    z=z, x=[str(m) for m in months], y=[str(y) for y in years],
                    colorscale="RdBu_r", zmid=0,
                ))
                fig.update_layout(title="Monthly IC Heatmap", template="plotly_white", height=300,
                                  xaxis_title="Month", yaxis_title="Year")
                charts["monthly_heatmap"] = self._fig_to_html(fig)
        except Exception as e:
            logger.warning("IC chart generation error: %s", e)
        return charts

    def _generate_quintile_charts(self, gr_analyzer, gr_result, gr_is, gr_oos) -> dict:
        charts = {}
        try:
            if "mean_returns" in gr_result:
                fig = gr_analyzer.plot_group_returns_bar(gr_result["mean_returns"])
                charts["quintile_bar"] = self._fig_to_html(fig)
            if "cumulative_returns" in gr_result:
                fig = gr_analyzer.plot_cumulative_returns(gr_result["cumulative_returns"])
                charts["cumulative_returns"] = self._fig_to_html(fig)
                if "Q5" in gr_result["cumulative_returns"].columns and "Q1" in gr_result["cumulative_returns"].columns:
                    fig = gr_analyzer.plot_long_short(gr_result["cumulative_returns"])
                    charts["long_short_curve"] = self._fig_to_html(fig)
            # IS vs OOS bar (NEW)
            if "mean_returns" in gr_is and "mean_returns" in gr_oos:
                fig = go.Figure()
                fig.add_trace(go.Bar(x=gr_is["mean_returns"].index, y=gr_is["mean_returns"].values * 100, name="In-Sample"))
                fig.add_trace(go.Bar(x=gr_oos["mean_returns"].index, y=gr_oos["mean_returns"].values * 100, name="Out-of-Sample"))
                fig.update_layout(title="IS vs OOS Quintile Returns", barmode="group", template="plotly_white", height=350)
                charts["is_vs_oos_bar"] = self._fig_to_html(fig)
        except Exception as e:
            logger.warning("Quintile chart generation error: %s", e)
        return charts

    def _generate_distribution_charts(self, fv_is, fv_oos, name) -> dict:
        charts = {}
        try:
            fig = go.Figure()
            fig.add_trace(go.Histogram(x=fv_is.iloc[:, 0].dropna(), name="In-Sample", opacity=0.6, histnorm="probability density"))
            if len(fv_oos) > 0:
                fig.add_trace(go.Histogram(x=fv_oos.iloc[:, 0].dropna(), name="Out-of-Sample", opacity=0.6, histnorm="probability density"))
            fig.update_layout(title=f"{name} Factor Distribution IS vs OOS", template="plotly_white", height=350, barmode="overlay")
            charts["distribution_overlay"] = self._fig_to_html(fig)

            # Coverage time series
            fv_all = pd.concat([fv_is, fv_oos]) if len(fv_oos) > 0 else fv_is
            coverage = fv_all.groupby(level="datetime").apply(lambda x: x.iloc[:, 0].notna().mean())
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=coverage.index, y=coverage.values, mode="lines", name="Coverage"))
            fig.update_layout(title="Factor Coverage Rate", template="plotly_white", height=300)
            charts["coverage_timeseries"] = self._fig_to_html(fig)
        except Exception as e:
            logger.warning("Distribution chart error: %s", e)
        return charts

    def _generate_decay_charts(self, decay, autocorr, name) -> dict:
        charts = {}
        try:
            if decay["ic_by_period"]:
                periods = [str(d["period"]) + "d" for d in decay["ic_by_period"]]
                ics = [d["ic"] for d in decay["ic_by_period"]]
                fig = go.Figure(data=go.Bar(x=periods, y=ics))
                fig.add_hline(y=0, line_dash="dot")
                fig.update_layout(title=f"{name} IC Decay", template="plotly_white", height=350)
                charts["ic_decay_bar"] = self._fig_to_html(fig)
            if autocorr:
                lags = [a["lag"] for a in autocorr]
                corrs = [a["corr"] for a in autocorr]
                fig = go.Figure(data=go.Scatter(x=lags, y=corrs, mode="lines+markers"))
                fig.update_layout(title=f"{name} Factor Autocorrelation", template="plotly_white", height=350,
                                  xaxis_title="Lag (days)", yaxis_title="Spearman Correlation")
                charts["autocorrelation"] = self._fig_to_html(fig)
        except Exception as e:
            logger.warning("Decay chart error: %s", e)
        return charts

    def _generate_score_charts(self, scores, name) -> dict:
        charts = {}
        try:
            dims = scores["dimensions"]
            names = [d["name"] for d in dims]
            values = [d["score"] for d in dims]
            fig = go.Figure(data=go.Scatterpolar(r=values + [values[0]], theta=names + [names[0]], fill="toself"))
            fig.update_layout(title=f"{name} Composite Score", template="plotly_white", height=400,
                              polar=dict(radialaxis=dict(visible=True, range=[0, 100])))
            charts["radar"] = self._fig_to_html(fig)
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
