"""Runner — entry point called by both CLI and Phase 4 report subagent.

Orchestrates: load config → build calendar/view/provider/mask/strategy →
construct factor loader → run engine → write report.

Two factor-loading modes:

- ``signal_recompute=False``: read the cached qfq factor parquet keyed by
  sha256 of the canonical expression in ``vault/factors/{factor_id}.yaml``.
- ``signal_recompute=True`` (default): recompute the factor on hfq data,
  pre-built once over the full window and cached at
  ``cache/factor_values_hfq/{key}.parquet``.

The recompute path is wired but the actual hfq compute call is deferred to
follow-up work (the spec says "out of scope for this design"). For the MVP
this runner falls back to the cached qfq path with a warning if hfq compute
is requested. End-to-end smoke can therefore be exercised against existing
qfq cached factor values.
"""
from __future__ import annotations

import logging
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from research.backtest.calendar import TradeCalendar
from research.backtest.config import BacktestConfig, load_default_config
from research.backtest.data_view import PriceView
from research.backtest.engine import Engine
from research.backtest.executor import Executor
from research.backtest.filters import TradabilityMask
from research.backtest.reporter import Reporter
from research.backtest.strategy import QuintilePortfolio, TopKLongOnly
from research.backtest.tradability import TradabilityProvider
from research.compute.cache import FactorValueCache
from research.storage.paths import StoragePaths
from research.storage.yaml_io import load_yaml

logger = logging.getLogger(__name__)


class CachedFactorLoader:
    """Reads a cached factor parquet built by Phase 2.

    The factor values dataframe has MultiIndex (datetime, instrument), with
    a single column whose name varies but is the only data column.
    """

    def __init__(self, factor_id: str, paths: StoragePaths | None = None):
        paths = paths or StoragePaths()
        meta_path = paths.factors_dir / f"{factor_id}.yaml"
        meta = load_yaml(meta_path)
        expr = meta.get("canonical") or meta.get("expression")
        if expr is None:
            raise ValueError(f"{factor_id}.yaml has no expression / canonical")
        self.factor_id = factor_id
        self.expression = expr
        cache = FactorValueCache(paths.factor_values_cache_dir)
        key = cache.make_key(expr)
        df = cache.get(key)
        if df is None:
            raise FileNotFoundError(
                f"factor cache miss: expression={expr!r} key={key} "
                f"— run Phase 2 first or use --signal-recompute"
            )
        # Coerce to a clean MultiIndex Series keyed by (date, sym)
        if isinstance(df, pd.DataFrame):
            if df.shape[1] != 1:
                # Some caches store multi-col; pick the first non-meta column
                non_meta = [c for c in df.columns if c.lower() not in ("datetime", "instrument")]
                df = df[[non_meta[0]]]
            df = df.iloc[:, 0]
        # Auto-flip sign for negative-IC factors so Top-K picks the predictively
        # best stocks rather than the worst. Reads validation_metrics.ic_mean
        # from the factor yaml; fallback to long_short_mean.
        vm = meta.get("validation_metrics") or {}
        ic = vm.get("ic_mean", vm.get("long_short_mean", 0.0))
        self.sign = -1.0 if ic < 0 else 1.0
        if self.sign < 0:
            df = -df
            logger.info("F%s ic_mean=%.4f<0 → flipping factor sign for Top-K", factor_id, ic)
        self._series: pd.Series = df

    def at(self, dt: date) -> pd.Series:
        ts = pd.Timestamp(dt)
        try:
            return self._series.xs(ts, level=0)
        except KeyError:
            return pd.Series(dtype=float)


def run_backtest(
    factor_id: str,
    cli_overrides: dict | None = None,
    storage_paths: StoragePaths | None = None,
) -> None:
    cfg = load_default_config(factor_id, cli_overrides)
    paths = storage_paths or StoragePaths()

    if cfg.signal_recompute:
        logger.warning(
            "signal_recompute=True requested but hfq recompute pipeline is not "
            "wired in this MVP; falling back to cached qfq factor values. "
            "Document any divergence in metrics.yaml.assumptions."
        )

    cal = TradeCalendar.from_db()
    view_path = (
        paths.cache_dir / "market_daily_hfq.parquet"
        if cfg.matching.price_adjust == "hfq"
        else paths.market_daily_cache
    )
    if not view_path.exists():
        # Friendly fallback: if hfq is requested but missing, try qfq with a
        # warning. The user can flip back to hfq once
        # `scripts/sync_hfq_parquet.py` has run.
        if cfg.matching.price_adjust == "hfq" and paths.market_daily_cache.exists():
            logger.warning(
                "hfq parquet missing (%s); falling back to qfq market_daily.parquet "
                "for this run. Sync hfq via `python3 scripts/sync_hfq_parquet.py`.",
                view_path,
            )
            view_path = paths.market_daily_cache
        else:
            raise FileNotFoundError(
                f"price view parquet missing: {view_path}. For hfq run "
                f"`python3 scripts/sync_hfq_parquet.py` first."
            )
    view = PriceView.from_parquet(view_path)
    # allow_missing_tables=True: tradability tables (instrument_st_status /
    # instrument_lifecycle) may not yet exist; fall back to empty data and
    # rely on the filter config to disable irrelevant blockers.
    provider = TradabilityProvider.from_db(view, allow_missing_tables=True)
    mask = TradabilityMask(view, provider, cfg.filters, cal,
                            match_price=cfg.matching.match_price)

    main = TopKLongOnly(
        holdings_n=cfg.portfolio.holdings_n,
        max_single_weight=cfg.portfolio.max_single_weight,
    )
    quint = QuintilePortfolio()
    factor_loader = CachedFactorLoader(factor_id, paths)
    engine = Engine(cfg, cal, view, mask, main, quint, factor_loader,
                     Executor(match_price=cfg.matching.match_price))

    base_out = paths.factors_dir / factor_id / "backtest"
    period_table = {
        "train": cfg.periods.train,
        "val": cfg.periods.val,
        "holdout": cfg.periods.holdout,
    }
    period_results: dict[str, dict] = {}
    for period_name in cfg.periods.run:
        start, end = period_table[period_name]
        result = engine.run(start, end)
        out_dir = base_out / period_name
        Reporter().write(result, out_dir)
        full = result.metrics.get("full", {})
        tov = result.metrics.get("turnover", {})
        period_results[period_name] = dict(
            equity_curve=result.equity_curve,
            metrics=result.metrics,
            start=start, end=end,
        )
        print(
            f"[{factor_id}] {period_name}: "
            f"Sharpe={full.get('sharpe', 0):.2f} "
            f"AnnRet={full.get('ann_return', 0):.2%} "
            f"MaxDD={full.get('max_dd', 0):.2%} "
            f"n_days={full.get('n_days', 0)} "
            f"AvgTradesPerRebal={tov.get('avg_trades_per_rebalance', 0):.1f} "
            f"AnnTurnoverX={tov.get('ann_turnover_x', 0):.2f}"
        )

    if len(period_results) >= 2:
        _write_combined_chart(period_results, base_out / "combined.png")
        print(f"[{factor_id}] combined chart: {base_out}/combined.png")


def _write_combined_chart(period_results: dict, out_path) -> None:
    """One continuous compound equity chart spanning train → val → holdout.

    Each period continues compounding from the prior period's end (no
    per-period reset), so the curve reads as "what would my account look
    like if I held this strategy from day 1". Background shading marks the
    three regions; vertical dotted lines mark the period boundaries.
    Top-K is the solid main line; Q1 / Q5 are faint dashed for context.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import pandas as pd

    fig, ax = plt.subplots(figsize=(14, 5))
    period_order = ["train", "val", "holdout"]
    region_colors = {"train": "#dddddd", "val": "#cfe3f5", "holdout": "#f6cccc"}
    line_colors = {"train": "#444", "val": "#1f77b4", "holdout": "#d62728"}

    carry: dict[str, float] = {"topk": 1.0, "q1": 1.0, "q5": 1.0}
    boundaries: list = []
    region_spans: list = []

    for pname in period_order:
        if pname not in period_results:
            continue
        ec = period_results[pname]["equity_curve"]
        if ec.empty:
            continue
        idx = ec.index
        if not isinstance(idx, pd.DatetimeIndex):
            idx = pd.to_datetime(idx)

        # Compound continuously: scale this period to start at last period's end
        topk = ec["total_equity"] / ec["total_equity"].iloc[0] * carry["topk"]
        ax.plot(idx, topk, color=line_colors[pname], lw=2, label=f"{pname} Top-K")
        carry["topk"] = float(topk.iloc[-1])

        for q, ls, key in [("q1_equity", ":", "q1"), ("q5_equity", "--", "q5")]:
            if q in ec.columns:
                series = ec[q] / ec[q].iloc[0] * carry[key]
                ax.plot(idx, series, color=line_colors[pname], lw=1, alpha=0.5,
                        linestyle=ls,
                        label=f"{pname} {key.upper()}")
                carry[key] = float(series.iloc[-1])

        region_spans.append((pname, idx[0], idx[-1]))
        boundaries.append(idx[-1])

    # Background shading + inside-top region labels (won't collide with title)
    for pname, x0, x1 in region_spans:
        ax.axvspan(x0, x1, color=region_colors[pname], alpha=0.35, zorder=0)
        ax.text((x0 + (x1 - x0) / 2), 0.96,
                pname.upper(), transform=ax.get_xaxis_transform(),
                ha="center", va="top",
                color=line_colors[pname], fontweight="bold", fontsize=10)

    for b in boundaries[:-1]:
        ax.axvline(b, color="black", linestyle="--", alpha=0.4, lw=1)

    ax.axhline(1.0, color="grey", linestyle=":", alpha=0.5)
    ax.set_title("Equity — continuous compound (train → val → holdout)")
    ax.set_ylabel("Cumulative return × initial")
    ax.legend(loc="best", fontsize=8, ncol=3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=110)
    plt.close(fig)
