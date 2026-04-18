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
from research.compute.cache import FactorValueCache
from research.storage.paths import StoragePaths

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
            vault_dir: If set, export charts as PNG into ``vault_dir/factors/FXXX/``
                       (colocated with ``F{id}.yaml`` / ``F{id}.md``).
                       Charts dict values become relative paths (for Obsidian embeds).
                       If None, charts are inline HTML (legacy mode).
        """
        t0_total = time.perf_counter()

        if vault_dir:
            self._vault_assets_dir = os.path.join(vault_dir, "factors", f"F{self.factor_id}")
            os.makedirs(self._vault_assets_dir, exist_ok=True)

        # ---- Load metadata + main data (sequential: each depends on previous) ----
        t0 = time.perf_counter()
        meta = self._load_factor_metadata()
        logger.info("[TIMING] load_factor_metadata: %.2fs", time.perf_counter() - t0)

        t0 = time.perf_counter()
        factor_df, price_df = self._load_data_from_cache(meta["expression"])
        logger.info(
            "[TIMING] load_data_from_cache (parquet reads): %.2fs",
            time.perf_counter() - t0,
        )

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

    def _load_data_from_cache(
        self, expression: str
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Load factor values + price from caches — no Qlib, no DB.

        Factor values come from ``FactorValueCache`` (hit by sha256(expr)).
        Prices come from ``storage/cache/market_daily.parquet`` (built by
        ``data_bridge.load_market_data``; the 1-day forward return column
        is inverted to derive close prices only where needed for charts).

        If either cache is cold, we fall through to a one-off Qlib call
        as a safety net — but log a warning so the user can warm the cache
        by running a Phase 2 batch first.
        """
        paths = StoragePaths("storage")
        cache = FactorValueCache(paths.factor_values_cache_dir)
        key = cache.make_key(expression)
        cached = cache.get(key)

        start = pd.Timestamp(self.config.train_start)
        end = pd.Timestamp(self.config.test_end)

        if cached is not None:
            df = cached.reset_index()
            # cached DF has (datetime, instrument) index
            if "datetime" in df.columns:
                df = df.rename(columns={"datetime": "time", "instrument": "symbol"})
            factor_df = df[["time", "symbol", "value"]]
            factor_df = factor_df[
                (factor_df["time"] >= start) & (factor_df["time"] <= end)
            ]
            factor_df = factor_df.dropna(subset=["value"]).reset_index(drop=True)
        else:
            logger.warning(
                "factor cache miss for %s — falling back to Qlib", expression
            )
            factor_df = self._qlib_fallback_factor(expression, start, end)

        price_df = self._load_price_from_cache(paths, start, end)
        if price_df.empty:
            raise ValueError(
                f"No price data in {paths.market_daily_cache} for {start}..{end}"
            )
        symbols = set(factor_df["symbol"].unique().tolist())
        price_df = price_df[price_df["symbol"].isin(symbols)].reset_index(drop=True)

        return factor_df, price_df

    @staticmethod
    def _load_price_from_cache(
        paths: StoragePaths, start: pd.Timestamp, end: pd.Timestamp
    ) -> pd.DataFrame:
        """Derive close prices from the cached market_daily parquet.

        The parquet stores forward returns (returns_1d = close_{t+1}/close_t - 1)
        plus amount/market_cap. We reconstruct a closing-price-like series by
        cumulatively unwinding returns_1d per symbol. For chart purposes
        (rebased curves), any monotone scaling of close is fine.
        """
        if not paths.market_daily_cache.exists():
            return pd.DataFrame(columns=["time", "symbol", "close"])

        raw = pd.read_parquet(paths.market_daily_cache)
        if isinstance(raw.index, pd.MultiIndex):
            raw = raw.reset_index()
        raw = raw.rename(columns={"datetime": "time", "instrument": "symbol"})
        ret_col = next(
            (c for c in ("returns_1d", "$close", "close") if c in raw.columns),
            None,
        )
        if ret_col is None:
            return pd.DataFrame(columns=["time", "symbol", "close"])
        raw["time"] = pd.to_datetime(raw["time"])
        raw = raw[(raw["time"] >= start) & (raw["time"] <= end)].copy()

        if ret_col == "returns_1d":
            # returns_1d is the forward 1-day return. Cumulative-prod gives
            # a close-proxy that's up to a constant multiple of true close.
            raw = raw.sort_values(["symbol", "time"])
            raw["close"] = (
                (1.0 + raw["returns_1d"].fillna(0)).groupby(raw["symbol"]).cumprod()
            )
            return raw[["time", "symbol", "close"]].reset_index(drop=True)

        return raw[["time", "symbol", ret_col]].rename(columns={ret_col: "close"})

    def _qlib_fallback_factor(
        self, expression: str, start: pd.Timestamp, end: pd.Timestamp
    ) -> pd.DataFrame:
        """Last-resort Qlib evaluation when the cache is cold.

        Kept as a safety net so a report can still be generated on a fresh
        checkout. Normal flow: Phase 2 runs first → cache populated →
        reports are pure parquet reads.
        """
        self._ensure_qlib_initialized()
        from qlib.data import D

        instruments = D.instruments("all")
        factor_qlib = D.features(
            instruments=instruments,
            fields=[expression],
            start_time=str(start.date()),
            end_time=str(end.date()),
        )
        if factor_qlib.empty:
            raise ValueError(f"Qlib returned no data for expression={expression!r}")
        df = factor_qlib.iloc[:, [0]].reset_index()
        df.columns = ["symbol", "time", "value"]
        df["time"] = pd.to_datetime(df["time"])
        return df.dropna(subset=["value"])[["time", "symbol", "value"]]

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
        """Load admitted library factors from the expression cache (no DB).

        Uses :func:`research.compute.data_bridge.load_library_signals` which
        hits ``FactorValueCache`` keyed on ``sha256(expression)``. Cache
        misses are computed once across the full date window (Phase 2
        also shares this cache, so the first batch warms it and every
        subsequent report reads from parquet).

        The self factor is filtered out because correlation against self
        is always 1.0 and degrades the top-5 display.
        """
        from research.compute.data_bridge import load_library_signals

        paths = StoragePaths("storage")

        corr_window_start = (
            pd.Timestamp(self.config.test_end) - pd.DateOffset(years=2)
        ).strftime("%Y-%m-%d")

        try:
            raw = load_library_signals(
                paths,
                start=corr_window_start,
                end=str(self.config.test_end),
            )
        except Exception as exc:
            logger.warning("Failed to load library factors from cache: %s", exc)
            return {}

        result: dict[str, pd.DataFrame] = {}
        for fid, mi_df in raw.items():
            if fid == f"F{self.factor_id}" or fid == self.factor_id:
                continue
            flat = mi_df.reset_index()
            flat = flat.rename(
                columns={"datetime": "time", "instrument": "symbol"}
            )
            flat = flat[["time", "symbol", "value"]].dropna(subset=["value"])
            if target_symbols:
                flat = flat[flat["symbol"].isin(set(target_symbols))]
            if not flat.empty:
                result[fid] = flat.reset_index(drop=True)
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
            Path to the report_data.json file (lives in ``vault/factors/F{id}/``
            alongside the generated PNG charts).
        """
        data = self.build(vault_dir=vault_dir)
        json_dir = os.path.join(vault_dir, "factors", f"F{self.factor_id}")
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
