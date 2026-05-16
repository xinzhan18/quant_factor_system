#!/usr/bin/env python3
"""Refresh backtest figures for one factor from existing parquets.

Usage:
    PYTHONPATH=src python3 scripts/refresh_backtest_figs.py F029
    PYTHONPATH=src python3 scripts/refresh_backtest_figs.py F029 --periods holdout
    PYTHONPATH=src python3 scripts/refresh_backtest_figs.py F029 --out-dir /tmp/test

The script reads ``equity_curve.parquet`` / ``trades.parquet`` /
``positions.parquet`` / ``metrics.yaml`` and rebuilds a
``BacktestResult`` shell, then calls ``Reporter.write`` to regenerate
all figures **without** re-running the engine. This is the "read parquet
→ redraw" path so we can iterate on chart code without spending 10-15
minutes per period.

Existing parquets are preserved (write is idempotent — Reporter
overwrites them with the same dataframes).
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
import yaml

# Add src/ to path if running from repo root without PYTHONPATH
_REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO / "src"))

from research.backtest.engine import BacktestResult  # noqa: E402
from research.backtest.reporter import Reporter  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("refresh_backtest_figs")


def _load_metrics(period_dir: Path) -> dict:
    p = period_dir / "metrics.yaml"
    if not p.exists():
        return {}
    with open(p) as f:
        loaded = yaml.safe_load(f) or {}
    return loaded


def refresh_period(period_dir: Path, market_parquet: Path | None) -> dict:
    """Refresh figures for one period dir; return summary dict."""
    eq_path = period_dir / "equity_curve.parquet"
    if not eq_path.exists():
        log.warning("%s: equity_curve.parquet missing — skip", period_dir)
        return {"period": period_dir.name, "status": "missing_equity"}
    equity = pd.read_parquet(eq_path)
    trades = (
        pd.read_parquet(period_dir / "trades.parquet")
        if (period_dir / "trades.parquet").exists()
        else pd.DataFrame()
    )
    positions = (
        pd.read_parquet(period_dir / "positions.parquet")
        if (period_dir / "positions.parquet").exists()
        else pd.DataFrame()
    )
    meta = _load_metrics(period_dir)
    result = BacktestResult(
        equity_curve=equity,
        trades=trades,
        positions=positions,
        metrics=meta.get("metrics", {}),
        config_snapshot=meta.get("config_snapshot", {}),
        runtime_meta=meta.get("runtime_meta", {}),
    )
    reporter = Reporter(market_parquet=market_parquet)
    reporter.write(result, period_dir)

    # Count figs
    figs = sorted((period_dir / "figs").glob("*.png"))
    # Reload metrics to capture benchmark block written by Reporter
    refreshed = _load_metrics(period_dir)
    bench = (refreshed.get("metrics") or {}).get("benchmark") or {}
    return {
        "period": period_dir.name,
        "status": "ok",
        "n_figs": len(figs),
        "figs": [f.name for f in figs],
        "benchmark_kind": bench.get("kind"),
        "benchmark_available": bench.get("available", False),
        "info_ratio": bench.get("info_ratio"),
        "alpha": bench.get("alpha"),
        "beta": bench.get("beta"),
        "sector_data_missing": (refreshed.get("metrics") or {}).get(
            "sector_data_missing", False
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("factor_id", help="e.g. F029")
    ap.add_argument(
        "--periods",
        nargs="+",
        default=None,
        help="Subset of periods to refresh (default: all under backtest/)",
    )
    ap.add_argument(
        "--storage-root",
        default="storage",
        help="Path to storage root (default: storage)",
    )
    ap.add_argument(
        "--market-parquet",
        default=None,
        help="Override market_daily parquet path for benchmark/ADV plots",
    )
    args = ap.parse_args()

    fid = args.factor_id
    backtest_dir = Path(args.storage_root) / "vault" / "factors" / fid / "backtest"
    if not backtest_dir.exists():
        log.error("backtest dir not found: %s", backtest_dir)
        return 1

    periods_avail = sorted([p.name for p in backtest_dir.iterdir() if p.is_dir()])
    periods = args.periods or periods_avail
    log.info("%s: refreshing periods %s", fid, periods)

    market_path = Path(args.market_parquet) if args.market_parquet else None

    results = []
    for pname in periods:
        period_dir = backtest_dir / pname
        if not period_dir.is_dir():
            log.warning("%s missing period dir: %s", fid, pname)
            continue
        summary = refresh_period(period_dir, market_path)
        log.info("  %s: %s", pname, summary)
        results.append(summary)

    # Print final compact summary
    print()
    print(f"=== refresh summary for {fid} ===")
    for r in results:
        print(
            f"  {r['period']:<10} status={r['status']} "
            f"figs={r.get('n_figs', 0)} "
            f"bench_kind={r.get('benchmark_kind')} "
            f"bench_avail={r.get('benchmark_available')} "
            f"IR={r.get('info_ratio')} alpha={r.get('alpha')} beta={r.get('beta')} "
            f"sector_missing={r.get('sector_data_missing')}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
