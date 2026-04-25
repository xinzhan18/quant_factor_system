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
        raise FileNotFoundError(
            f"price view parquet missing: {view_path}. For hfq run "
            f"`python3 scripts/resync_qlib.py --adjust hfq` first."
        )
    view = PriceView.from_parquet(view_path)
    provider = TradabilityProvider.from_db(view)
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
    for period_name in cfg.periods.run:
        start, end = period_table[period_name]
        result = engine.run(start, end)
        out_dir = base_out / period_name
        Reporter().write(result, out_dir)
        full = result.metrics.get("full", {})
        print(
            f"[{factor_id}] {period_name}: "
            f"Sharpe={full.get('sharpe', 0):.2f} "
            f"AnnRet={full.get('ann_return', 0):.2%} "
            f"MaxDD={full.get('max_dd', 0):.2%} "
            f"n_days={full.get('n_days', 0)}"
        )
