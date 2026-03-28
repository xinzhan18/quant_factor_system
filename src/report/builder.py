"""ReportDataBuilder -- thin orchestrator for factor report generation.

Loads data from DB/YAML, delegates computation to the 6-analyzer pipeline,
assembles the final report_data dict, and exports charts as PNG (vault mode)
or HTML fragments (legacy mode).

New schema (v2):
    factor, predictive_power, profitability, risk_attribution,
    conditional, decay_tradability, uniqueness, composite
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
from report.analytics.profit import ProfitAnalyzer
from report.analytics.conditional import ConditionalAnalyzer
from report.analytics.decay import DecayAnalyzer
from report.analytics.uniqueness import UniquenessAnalyzer
from report.scorer import CompositeScorer
from report.data_prep import merge_factor_price
from report.charts.theme import PNG_WIDTH, PNG_HEIGHT, PNG_SCALE

logger = logging.getLogger(__name__)


class ReportDataBuilder:
    """Orchestrate report data computation for a single factor.

    Usage:
        builder = ReportDataBuilder(factor_id="001", config=MiningConfig())
        data = builder.build()  # returns dict matching new report_data schema
    """

    def __init__(self, factor_id: str, config: MiningConfig | None = None):
        self.factor_id = factor_id
        self.config = config or MiningConfig()
        self._vault_assets_dir: str | None = None

    def build(self, vault_dir: str | None = None) -> dict:
        """Run full 6-analyzer computation pipeline, return report_data dict.

        Args:
            vault_dir: If set, export charts as PNG into vault_dir/assets/FXXX/.
                       Charts dict values become relative paths (for Obsidian embeds).
                       If None, charts are inline HTML (legacy mode).
        """
        if vault_dir:
            self._vault_assets_dir = os.path.join(vault_dir, "assets", f"F{self.factor_id}")
            os.makedirs(self._vault_assets_dir, exist_ok=True)

        # ---- Load data ----
        meta = self._load_factor_metadata()
        factor_df, price_df = self._load_data_from_db(meta["expression"])
        library_factors = self._load_library_factors()

        split_date = pd.Timestamp(self.config.test_start)
        name = meta.get("name", "")

        # ---- Merge factor + price ----
        merged = merge_factor_price(factor_df, price_df)

        # ---- Ch1: Predictive Power (ICAnalyzer) ----
        ic_analyzer = ICAnalyzer(name)
        ic_result = ic_analyzer.compute(merged, split_date)
        ic_charts = ic_analyzer.generate_charts(ic_result)

        # ---- Ch2: Profitability (ProfitAnalyzer) ----
        profit_analyzer = ProfitAnalyzer()
        profit_result = profit_analyzer.compute(merged, split_date)
        profit_charts = profit_analyzer.generate_charts(profit_result)

        # ---- Ch3: Risk Attribution (null at L0 -- requires industry/market cap) ----
        risk_result = None

        # ---- Ch4: Conditional (ConditionalAnalyzer) ----
        cond_analyzer = ConditionalAnalyzer()
        cond_result = cond_analyzer.compute(merged, price_df)
        cond_charts = cond_analyzer.generate_charts(cond_result)

        # ---- Ch5: Decay & Tradability (DecayAnalyzer) ----
        decay_analyzer = DecayAnalyzer()
        decay_result = decay_analyzer.compute(factor_df, price_df, split_date)
        decay_charts = decay_analyzer.generate_charts(decay_result, name=name)

        # ---- Ch6: Uniqueness (UniquenessAnalyzer) ----
        uniq_analyzer = UniquenessAnalyzer()
        uniq_result = uniq_analyzer.compute(factor_df, library_factors, merged)
        uniq_charts = uniq_analyzer.generate_charts(uniq_result)

        # ---- Merge regime labels into IC annual entries ----
        regime_map = {
            a["year"]: a["regime"]
            for a in cond_result.get("annual_ic", [])
            if "regime" in a
        }
        for entry in ic_result.get("annual", []):
            entry["regime"] = regime_map.get(entry["year"], "unknown")

        # ---- Ch7: Composite Score ----
        scorer = CompositeScorer()
        ic_1d = self._get_ic_at_period(decay_result, 1)
        ic_20d = self._get_ic_at_period(decay_result, 20)

        composite = scorer.compute(
            rank_ic_oos=ic_result["summary"]["oos"]["rank_ic_mean"],
            icir_oos=ic_result["summary"]["oos"]["icir"],
            ls_sharpe=profit_result["ls_stats"].get("sharpe"),
            monotonicity=profit_result["monotonicity"],
            ic_is=ic_result["summary"]["is"]["rank_ic_mean"],
            ic_oos=ic_result["summary"]["oos"]["rank_ic_mean"],
            max_corr=uniq_result["max_corr"] if uniq_result["max_corr"] > 0 else None,
            ic_1d=ic_1d,
            ic_20d=ic_20d,
        )
        score_charts = scorer.generate_charts(composite)

        # ---- Export charts ----
        all_charts = {}
        chart_groups = [
            ic_charts, profit_charts, cond_charts,
            decay_charts, uniq_charts, score_charts,
        ]
        for chart_dict in chart_groups:
            for chart_name, fig in chart_dict.items():
                all_charts[chart_name] = self._export_fig(fig, chart_name)

        # ---- Assemble report_data (new schema) ----
        return {
            "factor": {**meta, "data_level": "L0"},
            "predictive_power": {
                **self._strip_internal(ic_result),
                "charts": {k: all_charts[k] for k in ic_charts},
            },
            "profitability": {
                **self._strip_internal(profit_result),
                "charts": {k: all_charts[k] for k in profit_charts},
            },
            "risk_attribution": risk_result,
            "conditional": {
                **self._strip_internal(cond_result),
                "charts": {k: all_charts[k] for k in cond_charts},
            },
            "decay_tradability": {
                **self._strip_internal(decay_result),
                "charts": {k: all_charts[k] for k in decay_charts},
            },
            "uniqueness": {
                **self._strip_internal(uniq_result),
                "charts": {k: all_charts[k] for k in uniq_charts},
            },
            "composite": {
                **composite,
                "charts": {k: all_charts[k] for k in score_charts},
            },
        }

    # ---- Helpers ----

    @staticmethod
    def _get_ic_at_period(decay_result: dict, period: int):
        """Extract IC value for a given holding period from decay result."""
        for entry in decay_result.get("ic_by_period", []):
            if entry["days"] == period:
                return entry["ic"]
        return None

    @staticmethod
    def _strip_internal(result: dict) -> dict:
        """Remove keys starting with '_' (internal data not for serialization)."""
        return {k: v for k, v in result.items() if not k.startswith("_")}

    # ---- Qlib Initialization ----

    def _ensure_qlib_initialized(self):
        """Initialize Qlib and register custom operators if not already done."""
        import qlib
        if not getattr(qlib, "_is_initialized", False):
            qlib.init(provider_uri=os.path.expanduser(self.config.qlib_data_dir))
        from qlib.config import C
        C.kernels = 1
        try:
            from mining.operators import register_custom_operators
            register_custom_operators()
        except ImportError:
            pass

    # ---- Data Loading (IO boundary) ----

    def _load_factor_metadata(self) -> dict:
        """Load factor metadata from factor_meta DB table."""
        import psycopg2
        try:
            conn = psycopg2.connect(self.config.system.database.connection_string)
        except psycopg2.Error as exc:
            raise RuntimeError(f"Failed to connect to database: {exc}") from exc
        try:
            sql = (
                "SELECT factor_id, name, expression, category, batch_id, admitted_at "
                "FROM factor_meta WHERE factor_id = %s"
            )
            with conn.cursor() as cur:
                cur.execute(sql, (self.factor_id,))
                row = cur.fetchone()
            if row is None:
                raise ValueError(
                    f"Factor {self.factor_id!r} not found in factor_meta table"
                )
            return {
                "id": row[0],
                "name": row[1],
                "expression": row[2],
                "category": row[3] or "other",
                "batch": row[4] or "",
                "admitted_at": str(row[5] or ""),
            }
        finally:
            conn.close()

    def _load_data_from_db(self, expression: str) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Compute factor values via Qlib and load price data from DB.

        Args:
            expression: Qlib expression string for the factor.

        Returns:
            Tuple of (factor_df[time, symbol, value], price_df[time, symbol, close]).
        """
        self._ensure_qlib_initialized()
        from qlib.data import D

        instruments = D.instruments("all")
        start = self.config.train_start
        end = self.config.test_end

        factor_qlib = D.features(
            instruments=instruments,
            fields=[expression],
            start_time=start,
            end_time=end,
        )
        if factor_qlib.empty:
            raise ValueError(f"Qlib returned no data for expression={expression!r}")

        # Flatten MultiIndex (instrument, datetime) -> [time, symbol, value]
        factor_df = factor_qlib.iloc[:, [0]].reset_index()
        factor_df.columns = ["symbol", "time", "value"]
        factor_df = factor_df[["time", "symbol", "value"]]
        factor_df["time"] = pd.to_datetime(factor_df["time"])
        factor_df = factor_df.dropna(subset=["value"])

        # Load price data from market_daily
        import psycopg2
        try:
            conn = psycopg2.connect(self.config.system.database.connection_string)
        except psycopg2.Error as exc:
            raise RuntimeError(f"Failed to connect to database: {exc}") from exc
        try:
            symbols = factor_df["symbol"].unique().tolist()
            price_sql = (
                "SELECT symbol, time, close FROM market_daily "
                "WHERE symbol = ANY(%s) AND time BETWEEN %s AND %s"
            )
            price_df = pd.read_sql(price_sql, conn, params=[symbols, start, end])
            if price_df.empty:
                raise ValueError(
                    f"No price data for {len(symbols)} symbols in {start}..{end}"
                )
            price_df["time"] = pd.to_datetime(price_df["time"])
            return factor_df, price_df
        finally:
            conn.close()

    def _load_library_factors(self) -> dict[str, pd.DataFrame]:
        """Load factor values for admitted library members (except self) via Qlib.

        Returns:
            Dict mapping factor_id -> DataFrame[time, symbol, value].
        """
        import psycopg2
        try:
            conn = psycopg2.connect(self.config.system.database.connection_string)
        except psycopg2.Error as exc:
            logger.warning("Failed to connect to DB for library factors: %s", exc)
            return {}
        try:
            sql = (
                "SELECT factor_id, expression FROM factor_meta "
                "WHERE factor_id != %s AND status = 'admitted'"
            )
            with conn.cursor() as cur:
                cur.execute(sql, (self.factor_id,))
                rows = cur.fetchall()
        except Exception as exc:
            logger.warning("Failed to query library factors: %s", exc)
            return {}
        finally:
            conn.close()

        if not rows:
            return {}

        self._ensure_qlib_initialized()
        from qlib.data import D

        instruments = D.instruments("all")
        start = self.config.train_start
        end = self.config.test_end
        result = {}
        for fid, expr in rows:
            try:
                qlib_df = D.features(
                    instruments=instruments,
                    fields=[expr],
                    start_time=start,
                    end_time=end,
                )
                if not qlib_df.empty:
                    df = qlib_df.iloc[:, [0]].reset_index()
                    df.columns = ["symbol", "time", "value"]
                    df = df[["time", "symbol", "value"]]
                    df["time"] = pd.to_datetime(df["time"])
                    df = df.dropna(subset=["value"])
                    result[fid] = df
            except Exception as exc:
                logger.warning("Failed to compute library factor %s: %s", fid, exc)
        return result

    # ---- Chart output (PNG for vault, HTML for legacy) ----

    def _export_fig(
        self, fig: go.Figure, chart_name: str, height: int | None = None
    ) -> str:
        """Export a Plotly figure as PNG (vault mode) or HTML fragment (legacy).

        Returns:
            Vault mode: relative path like "F001/ic_timeseries.png"
            Legacy mode: HTML string
        """
        if height:
            fig.update_layout(height=height)

        if self._vault_assets_dir:
            png_path = os.path.join(self._vault_assets_dir, f"{chart_name}.png")
            fig.write_image(
                png_path,
                width=PNG_WIDTH,
                height=height or PNG_HEIGHT,
                scale=PNG_SCALE,
            )
            return f"F{self.factor_id}/{chart_name}.png"
        else:
            return pio.to_html(fig, full_html=False, include_plotlyjs=False)

    # ---- Save methods ----

    def save(self, output_dir: str) -> str:
        """Build report data and save to JSON (legacy mode)."""
        os.makedirs(output_dir, exist_ok=True)
        data = self.build()
        path = os.path.join(output_dir, "report_data.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        logger.info("Report data saved to %s", path)
        return path

    def save_for_vault(self, vault_dir: str = "storage/vault") -> str:
        """Build report data with PNG charts and save JSON for skill consumption.

        Args:
            vault_dir: Path to the Obsidian vault root.

        Returns:
            Path to the report_data.json file.
        """
        data = self.build(vault_dir=vault_dir)
        json_dir = os.path.join(vault_dir, "assets", f"F{self.factor_id}")
        os.makedirs(json_dir, exist_ok=True)
        json_path = os.path.join(json_dir, "report_data.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        logger.info("Vault report data saved to %s (PNGs in same dir)", json_path)
        return json_path


def main():
    parser = argparse.ArgumentParser(description="Build factor report data")
    parser.add_argument("--factor-id", required=True)
    parser.add_argument("--qlib-dir", default=None, help="Qlib data directory")
    parser.add_argument("--output-dir", default=None, help="Legacy HTML mode output dir")
    parser.add_argument("--vault", action="store_true", help="Vault mode: export PNGs + JSON")
    parser.add_argument("--vault-dir", default="storage/vault", help="Vault root directory")
    args = parser.parse_args()

    config = MiningConfig()
    if args.qlib_dir:
        config.system.qlib_data_dir = args.qlib_dir

    builder = ReportDataBuilder(args.factor_id, config=config)
    if args.vault:
        path = builder.save_for_vault(args.vault_dir)
    else:
        if not args.output_dir:
            parser.error("--output-dir is required in legacy mode")
        path = builder.save(args.output_dir)
    print(f"Report data: {path}")


if __name__ == "__main__":
    main()
