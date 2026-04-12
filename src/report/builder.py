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
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from report.config_adapter import MiningConfig
from report.analytics.ic import ICAnalyzer
from report.analytics.profit import ProfitAnalyzer
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
        t0_total = time.perf_counter()

        if vault_dir:
            self._vault_assets_dir = os.path.join(vault_dir, "assets", f"F{self.factor_id}")
            os.makedirs(self._vault_assets_dir, exist_ok=True)

        # ---- Load metadata + main data (sequential: each depends on previous) ----
        t0 = time.perf_counter()
        meta = self._load_factor_metadata()
        logger.info("[TIMING] load_factor_metadata: %.2fs", time.perf_counter() - t0)

        t0 = time.perf_counter()
        factor_df, price_df = self._load_data_from_db(meta["expression"])
        logger.info("[TIMING] load_data_from_db (Qlib eval + DB price): %.2fs", time.perf_counter() - t0)

        split_date = pd.Timestamp(self.config.test_start)
        name = meta.get("name", "")

        # ---- Merge factor + price ----
        t0 = time.perf_counter()
        merged = merge_factor_price(factor_df, price_df)
        logger.info("[TIMING] merge_factor_price: %.2fs", time.perf_counter() - t0)

        # ---- Instantiate analyzers ----
        ic_analyzer = ICAnalyzer(name)
        profit_analyzer = ProfitAnalyzer()
        decay_analyzer = DecayAnalyzer()
        uniq_analyzer = UniquenessAnalyzer()

        # ---- Batch 1: IC + Profit in parallel ----
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=2) as _pool:
            _f_ic = _pool.submit(ic_analyzer.compute, merged, split_date)
            _f_profit = _pool.submit(profit_analyzer.compute, merged, split_date)
            ic_result = _f_ic.result()
            profit_result = _f_profit.result()
        logger.info("[TIMING] batch1 (IC + Profit parallel): %.2fs", time.perf_counter() - t0)

        # ---- Load library factors late — only needed for Uniqueness ----
        t0 = time.perf_counter()
        target_symbols = factor_df["symbol"].unique().tolist()
        library_factors = self._load_library_factors(target_symbols=target_symbols)
        logger.info("[TIMING] load_library_factors (%d factors): %.2fs", len(library_factors), time.perf_counter() - t0)

        # Trim target factor to the same 2-year correlation window for fair comparison
        corr_window_start = pd.Timestamp(self.config.test_end) - pd.DateOffset(years=2)
        factor_df_corr = factor_df[factor_df["time"] >= corr_window_start]

        # ---- Batch 2: Decay + Uniqueness in parallel ----
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=2) as _pool:
            _f_decay = _pool.submit(decay_analyzer.compute, factor_df, price_df, split_date)
            _f_uniq = _pool.submit(uniq_analyzer.compute, factor_df_corr, library_factors)
            decay_result = _f_decay.result()
            uniq_result = _f_uniq.result()
        logger.info("[TIMING] batch2 (Decay + Uniqueness parallel): %.2fs", time.perf_counter() - t0)

        del library_factors

        # ---- Composite Score ----
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

        # ---- Parallel chart generation ----
        t0 = time.perf_counter()
        with ThreadPoolExecutor(max_workers=5) as _pool:
            _f_ic_ch = _pool.submit(ic_analyzer.generate_charts, ic_result)
            _f_profit_ch = _pool.submit(profit_analyzer.generate_charts, profit_result)
            _f_decay_ch = _pool.submit(
                lambda r: decay_analyzer.generate_charts(r, name=name), decay_result
            )
            _f_uniq_ch = _pool.submit(uniq_analyzer.generate_charts, uniq_result)
            _f_score_ch = _pool.submit(scorer.generate_charts, composite)

            ic_charts = _f_ic_ch.result()
            profit_charts = _f_profit_ch.result()
            decay_charts = _f_decay_ch.result()
            uniq_charts = _f_uniq_ch.result()
            score_charts = _f_score_ch.result()
        logger.info("[TIMING] parallel chart generation: %.2fs", time.perf_counter() - t0)

        # ---- Export charts (parallel PNG rendering via Kaleido) ----
        chart_groups = [ic_charts, profit_charts, decay_charts, uniq_charts, score_charts]
        all_fig_items = [
            (chart_name, fig)
            for chart_dict in chart_groups
            for chart_name, fig in chart_dict.items()
        ]

        def _export_one(item):
            chart_name, fig = item
            t0 = time.perf_counter()
            result = self._export_fig(fig, chart_name)
            logger.info("[TIMING]   export_fig %s: %.2fs", chart_name, time.perf_counter() - t0)
            fig.data = []
            return chart_name, result

        all_charts = {}
        t0_export = time.perf_counter()
        with ThreadPoolExecutor(max_workers=4) as _pool:
            for chart_name, path in _pool.map(_export_one, all_fig_items):
                all_charts[chart_name] = path
        logger.info("[TIMING] export all charts (%d PNGs): %.2fs", len(all_fig_items), time.perf_counter() - t0_export)
        for chart_dict in chart_groups:
            chart_dict.clear()

        logger.info("[TIMING] TOTAL build(): %.2fs", time.perf_counter() - t0_total)

        # ---- Assemble report_data ----
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
            from research.compute.operators import register_custom_operators
            register_custom_operators()
        except ImportError:
            pass

    # ---- Data Loading (IO boundary) ----

    def _load_factor_metadata(self) -> dict:
        """Load factor metadata from vault/factors/F{id}.yaml (new architecture).

        Falls back to DB factor_meta if vault file not found.
        """
        import yaml as _yaml

        # Primary: vault/factors/F{id}.yaml (new architecture source of truth)
        vault_yaml = Path("storage/vault/factors") / f"F{self.factor_id}.yaml"
        if not vault_yaml.exists():
            # Try with raw factor_id (might already include F prefix)
            vault_yaml = Path("storage/vault/factors") / f"{self.factor_id}.yaml"

        if vault_yaml.exists():
            with open(vault_yaml) as f:
                meta = _yaml.safe_load(f) or {}
            return {
                "id": meta.get("factor_id", self.factor_id),
                "name": meta.get("name", f"factor_{self.factor_id}"),
                "expression": meta.get("expression", ""),
                "category": meta.get("family_tag", "other"),
                "batch": meta.get("admitted_in_batch", ""),
                "admitted_at": str(meta.get("admitted_at", "")),
            }

        # Fallback: DB factor_meta
        try:
            import psycopg2
            conn = psycopg2.connect(self.config.system.database.connection_string)
            try:
                sql = (
                    "SELECT factor_id, name, expression, category, batch_id, admitted_at "
                    "FROM factor_meta WHERE factor_id = %s"
                )
                with conn.cursor() as cur:
                    cur.execute(sql, (self.factor_id,))
                    row = cur.fetchone()
                if row is not None:
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
        except Exception:
            pass

        raise ValueError(
            f"Factor {self.factor_id!r} not found in vault or factor_meta table"
        )

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

    def _load_style_factors(self, symbols: list[str]) -> dict[str, pd.DataFrame]:
        """Load market_cap, pb_ratio, pe_ratio from Qlib for risk attribution.

        Returns:
            Dict mapping field name to DataFrame[time, symbol, value].
            Empty dict on failure.
        """
        from qlib.data import D
        self._ensure_qlib_initialized()

        fields = ["$market_cap", "$pb_ratio", "$pe_ratio"]
        try:
            raw = D.features(
                instruments=symbols,
                fields=fields,
                start_time=self.config.train_start,
                end_time=self.config.test_end,
            )
        except Exception as exc:
            logger.warning("Failed to load style factors from Qlib: %s", exc)
            return {}

        if raw.empty:
            return {}

        raw = raw.reset_index()
        # Qlib MultiIndex: (instrument, datetime) → columns [symbol, time, ...]
        raw.columns = ["symbol", "time"] + [f.lstrip("$") for f in fields]
        raw["time"] = pd.to_datetime(raw["time"])

        result = {}
        for col in ["market_cap", "pb_ratio", "pe_ratio"]:
            sub = raw[["time", "symbol", col]].rename(columns={col: "value"})
            sub = sub.dropna(subset=["value"])
            if not sub.empty:
                result[col] = sub
        return result

    def _load_library_factors(
        self, target_symbols: list[str] | None = None
    ) -> dict[str, pd.DataFrame]:
        """Load factor values for admitted library members (except self) from DB.

        Reads from factor_values table where admitted values are pre-stored,
        avoiding repeated Qlib expression evaluations.

        Uses a 2-year window and an optional symbol sample to keep the query
        manageable (full-universe × 10-year = ~185M rows is prohibitively slow).

        Args:
            target_symbols: Optional list of symbols from the target factor. When
                provided, only this subset is loaded from DB (correlation estimates
                from a 1000-stock sample are accurate to ±0.02).

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
            # Get admitted factor IDs (excluding self)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT factor_id FROM factor_meta "
                    "WHERE factor_id != %s AND status = 'admitted'",
                    (self.factor_id,),
                )
                factor_ids = [r[0] for r in cur.fetchall()]

            if not factor_ids:
                return {}

            # Use last 2 years only — cross-sectional rank correlations are stable over time.
            corr_window_start = (
                pd.Timestamp(self.config.test_end) - pd.DateOffset(years=2)
            ).strftime("%Y-%m-%d")

            # Sample up to 1000 symbols from the target factor for the query.
            # Spearman cross-sectional correlation estimated on 1000 stocks is
            # accurate to ±0.02 vs full universe — sufficient for the 0.7 threshold.
            _MAX_CORR_SYMBOLS = 200
            if target_symbols and len(target_symbols) > _MAX_CORR_SYMBOLS:
                import numpy as np
                rng = np.random.RandomState(42)
                sample_syms = rng.choice(target_symbols, size=_MAX_CORR_SYMBOLS, replace=False).tolist()
            else:
                sample_syms = target_symbols or []

            # Batch-load all library factor values in one query (date + symbol bounded)
            factor_names = [f"factor_{fid}" for fid in factor_ids]
            placeholders = ",".join(["%s"] * len(factor_names))
            if sample_syms:
                sql = (
                    f"SELECT factor_name, time, symbol, value FROM factor_values "
                    f"WHERE factor_name IN ({placeholders}) "
                    f"AND time BETWEEN %s AND %s "
                    f"AND symbol = ANY(%s)"
                )
                params = factor_names + [corr_window_start, self.config.test_end, sample_syms]
            else:
                sql = (
                    f"SELECT factor_name, time, symbol, value FROM factor_values "
                    f"WHERE factor_name IN ({placeholders}) "
                    f"AND time BETWEEN %s AND %s"
                )
                params = factor_names + [corr_window_start, self.config.test_end]
            all_df = pd.read_sql(sql, conn, params=params)
        except Exception as exc:
            logger.warning("Failed to load library factors from DB: %s", exc)
            return {}
        finally:
            conn.close()

        if all_df.empty:
            return {}

        all_df["time"] = pd.to_datetime(all_df["time"])
        all_df = all_df.dropna(subset=["value"])

        name_to_id = {f"factor_{fid}": fid for fid in factor_ids}
        result = {}
        for fname, grp in all_df.groupby("factor_name"):
            fid = name_to_id.get(fname)
            if fid:
                result[fid] = grp[["time", "symbol", "value"]].reset_index(drop=True)
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

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s - %(message)s")

    config = MiningConfig()
    if args.qlib_dir:
        config.system.qlib_data_dir = args.qlib_dir

    builder = ReportDataBuilder(args.factor_id, config=config)
    try:
        if args.vault:
            path = builder.save_for_vault(args.vault_dir)
        else:
            if not args.output_dir:
                parser.error("--output-dir is required in legacy mode")
            path = builder.save(args.output_dir)
        print(f"Report data: {path}")
    finally:
        # Explicitly shut down Kaleido so its reader thread doesn't block Python exit
        try:
            import plotly.io as _pio
            _pio.kaleido.scope.shutdown_kaleido()
        except Exception:
            pass


if __name__ == "__main__":
    main()
