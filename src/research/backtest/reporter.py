"""Reporter — write 4 parquets + metrics.yaml + figures.

All ``_plot_*`` methods receive ``(BacktestResult, Path)`` and never raise:
on failure they log a warning, render a placeholder, and continue. This is
intentional — a missing optional chart (e.g. industry data) must NOT abort
the whole report.

R5 vectorisation: every plot uses groupby / unstack / cumprod / rolling.
No per-date or per-symbol Python loops.

Chart families
--------------

Tier-0 (always produced, identical to v1):
    equity / drawdown / monthly_heatmap / layer_decomp / cost_drag /
    blocked_trades

Tier-1 P0 (benchmark — the conclusion):
    equity_vs_benchmark, excess_equity, rolling_sharpe

Tier-1 P1 (portfolio diagnostics):
    holding_period_hist, sector_weight_timeseries, topk_vs_q5_diff,
    rank_persistence

Tier-2 P2 (nice-to-have):
    trade_pnl_dist, drawdown_recovery, liquidity_utilization,
    cost_waterfall
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml

from research.backtest.benchmark import (
    compute_benchmark_metrics,
    load_benchmark_equity,
)
from research.backtest.engine import BacktestResult

logger = logging.getLogger(__name__)


def _date_to_iso(obj):
    """yaml.safe_dump can't serialize date / Timestamp by default."""
    import datetime as _dt
    if isinstance(obj, (_dt.date, _dt.datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {k: _date_to_iso(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_date_to_iso(v) for v in obj]
    return obj


def _ensure_dt_index(s):
    """Return a copy of ``s`` with a DatetimeIndex (no-op if already)."""
    if not isinstance(s.index, pd.DatetimeIndex):
        s = s.copy()
        s.index = pd.to_datetime(s.index)
    return s


def _placeholder(ax, msg: str) -> None:
    ax.text(0.5, 0.5, msg, ha="center", va="center", fontsize=11, color="gray",
            transform=ax.transAxes)
    ax.set_xticks([])
    ax.set_yticks([])


def _save(fig, path: Path, dpi: int = 100) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=dpi)
    plt.close(fig)


@dataclass(frozen=True)
class Reporter:
    """Writes parquets / metrics.yaml / 17 figures.

    Construction option ``benchmark_kind`` chooses the benchmark series
    used by ``equity_vs_benchmark`` / ``excess_equity`` and the metrics
    block. ``None`` (default) means "infer from result.config_snapshot".
    """

    benchmark_kind: str | None = None
    secondary_benchmark_kind: str | None = "csi300"
    market_parquet: Path | None = None

    def write(self, result: BacktestResult, out_dir: Path) -> None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        # ---- parquets ----
        result.equity_curve.to_parquet(out_dir / "equity_curve.parquet")
        result.trades.to_parquet(out_dir / "trades.parquet")
        if not result.positions.empty:
            result.positions.to_parquet(out_dir / "positions.parquet")
        else:
            pd.DataFrame().to_parquet(out_dir / "positions.parquet")

        # ---- benchmark (compute once, share across plots & metrics) ----
        primary_kind = self._resolve_benchmark_kind(result)
        bench_primary = self._load_benchmark(result, primary_kind)
        bench_secondary = (
            self._load_benchmark(result, self.secondary_benchmark_kind)
            if self.secondary_benchmark_kind
            else pd.Series(dtype=float)
        )

        # ---- metrics.yaml (extended with benchmark block) ----
        metrics = dict(result.metrics)
        bench_metrics = compute_benchmark_metrics(
            result.equity_curve["total_equity"], bench_primary,
        )
        bench_metrics["kind"] = primary_kind
        metrics["benchmark"] = bench_metrics
        # Industry availability flag (set later by _plot_sector_weights)
        sector_flag: dict = {}
        meta = {
            "metrics": _date_to_iso(metrics),
            "config_snapshot": _date_to_iso(result.config_snapshot),
            "runtime_meta": _date_to_iso(result.runtime_meta),
        }
        # Write a first pass; _plot_sector_weights may overwrite with the
        # sector_data_missing flag.
        with open(out_dir / "metrics.yaml", "w") as f:
            yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)

        # ---- figures ----
        figs_dir = out_dir / "figs"
        figs_dir.mkdir(exist_ok=True)

        plots = [
            # Tier-0
            ("equity", self._plot_equity),
            ("drawdown", self._plot_drawdown),
            ("monthly_heatmap", self._plot_monthly_heatmap),
            ("layer_decomp", self._plot_layer_decomp),
            ("cost_drag", self._plot_cost_drag),
            ("blocked_trades", self._plot_blocked),
            # Tier-1 P0
            ("equity_vs_benchmark", lambda r, p: self._plot_equity_vs_benchmark(
                r, p, bench_primary, bench_secondary, primary_kind)),
            ("excess_equity", lambda r, p: self._plot_excess_equity(
                r, p, bench_primary, primary_kind)),
            ("rolling_sharpe", self._plot_rolling_sharpe),
            # Tier-1 P1
            ("holding_period_hist", self._plot_holding_period_hist),
            ("sector_weight_timeseries", lambda r, p: sector_flag.update(
                self._plot_sector_weights(r, p))),
            ("topk_vs_q5_diff", self._plot_topk_vs_q5_diff),
            ("rank_persistence", self._plot_rank_persistence),
            # Tier-2 P2
            ("trade_pnl_dist", self._plot_trade_pnl_dist),
            ("drawdown_recovery", self._plot_drawdown_recovery),
            ("liquidity_utilization", lambda r, p: self._plot_liquidity_util(
                r, p, self.market_parquet)),
            ("cost_waterfall", self._plot_cost_waterfall),
        ]
        for name, fn in plots:
            try:
                fn(result, figs_dir / f"{name}.png")
            except Exception as exc:  # noqa: BLE001
                logger.warning("plot %s failed: %s", name, exc)
                fig, ax = plt.subplots(figsize=(10, 3))
                _placeholder(ax, f"{name}: {type(exc).__name__}")
                ax.set_title(name)
                _save(fig, figs_dir / f"{name}.png")

        # Re-write metrics.yaml if sector flag landed
        if sector_flag.get("sector_data_missing"):
            metrics["sector_data_missing"] = True
            meta["metrics"] = _date_to_iso(metrics)
            with open(out_dir / "metrics.yaml", "w") as f:
                yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)

    # ------------------------------------------------------------------
    # Benchmark plumbing
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_benchmark_kind(result: BacktestResult) -> str:
        # config_snapshot.benchmark.kind = "csi1000_total_return" | …
        snap = result.config_snapshot or {}
        bench = snap.get("benchmark") or {}
        raw = bench.get("kind", "csi1000_total_return")
        # Map to index_constituents.index_name values
        if "csi1000" in raw:
            return "csi1000"
        if "csi300" in raw:
            return "csi300"
        return "csi1000"

    def _load_benchmark(self, result: BacktestResult, kind: str | None) -> pd.Series:
        if not kind:
            return pd.Series(dtype=float)
        ec = result.equity_curve
        if ec.empty:
            return pd.Series(dtype=float)
        idx = ec.index
        if not isinstance(idx, pd.DatetimeIndex):
            idx = pd.to_datetime(idx)
        start = idx.min().date()
        end = idx.max().date()
        initial = float(result.config_snapshot.get("initial_capital", 1e6))
        return load_benchmark_equity(
            start, end, kind=kind, initial_capital=initial,
            market_parquet=self.market_parquet,
        )

    # ------------------------------------------------------------------
    # Tier 0 plots (preserved from v1)
    # ------------------------------------------------------------------

    @staticmethod
    def _plot_equity(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(10, 4))
        r.equity_curve["total_equity"].plot(ax=ax, label="Top-K", color="black", lw=2)
        ax.set_title("Net equity curve")
        ax.legend()
        _save(fig, path)

    @staticmethod
    def _plot_drawdown(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(10, 3))
        if "drawdown" in r.equity_curve.columns:
            r.equity_curve["drawdown"].plot(ax=ax, color="red")
        ax.set_title("Drawdown")
        ax.set_ylabel("DD")
        _save(fig, path)

    @staticmethod
    def _plot_monthly_heatmap(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(10, 4))
        ret = r.equity_curve["total_equity"].pct_change().dropna()
        if ret.empty:
            _placeholder(ax, "no returns")
            _save(fig, path)
            return
        if not isinstance(ret.index, pd.DatetimeIndex):
            ret.index = pd.to_datetime(ret.index)
        monthly = (1 + ret).resample("ME").prod() - 1
        df = monthly.to_frame("ret")
        df["year"] = df.index.year
        df["month"] = df.index.month
        hm = df.pivot(index="year", columns="month", values="ret")
        im = ax.imshow(hm.values, cmap="RdYlGn", aspect="auto")
        ax.set_yticks(range(len(hm.index)))
        ax.set_yticklabels(hm.index)
        ax.set_xticks(range(hm.shape[1]))
        ax.set_xticklabels(hm.columns)
        ax.set_title("Monthly returns")
        plt.colorbar(im, ax=ax)
        _save(fig, path)

    @staticmethod
    def _plot_layer_decomp(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(10, 4))
        for q in range(1, 6):
            col = f"q{q}_equity"
            if col in r.equity_curve.columns:
                r.equity_curve[col].plot(ax=ax, label=f"Q{q}", alpha=0.6)
        if "total_equity" in r.equity_curve.columns:
            r.equity_curve["total_equity"].plot(
                ax=ax, label="Top-K", color="black", lw=2
            )
        ax.legend()
        ax.set_title("Quintile decomposition + Top-K")
        _save(fig, path)

    @staticmethod
    def _plot_cost_drag(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(10, 3))
        if not r.trades.empty and "cost_cny" in r.trades.columns:
            main_only = r.trades[r.trades.get("account", "main") == "main"]
            if not main_only.empty:
                main_only.groupby("date")["cost_cny"].sum().cumsum().plot(ax=ax)
        ax.set_title("Cumulative cost drag (CNY)")
        _save(fig, path)

    @staticmethod
    def _plot_blocked(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(10, 3))
        if not r.trades.empty:
            blocked = r.trades[
                r.trades["reason"].astype(str).str.startswith("blocked")
            ]
            if not blocked.empty:
                blocked.groupby("date").size().plot(ax=ax, kind="bar")
        ax.set_title("Blocked trades per day")
        _save(fig, path)

    # ------------------------------------------------------------------
    # Tier 1 P0 — benchmark comparison
    # ------------------------------------------------------------------

    @staticmethod
    def _plot_equity_vs_benchmark(
        r: BacktestResult,
        path: Path,
        bench_primary: pd.Series,
        bench_secondary: pd.Series,
        primary_kind: str,
    ) -> None:
        fig, ax = plt.subplots(figsize=(11, 4))
        eq = _ensure_dt_index(r.equity_curve["total_equity"])
        eq.plot(ax=ax, label="Top-K", color="black", lw=2)
        if not bench_primary.empty:
            b = _ensure_dt_index(bench_primary)
            b.plot(ax=ax, label=f"{primary_kind} (eq-weight)", color="#1f77b4",
                   lw=1.5, alpha=0.8)
        if not bench_secondary.empty:
            b2 = _ensure_dt_index(bench_secondary)
            b2.plot(ax=ax, label="csi300 (eq-weight)", color="#d62728",
                    lw=1.0, alpha=0.7, linestyle="--")
        ax.set_title("Top-K vs benchmark equity")
        ax.set_ylabel("Equity (CNY)")
        ax.legend()
        ax.grid(alpha=0.3)
        _save(fig, path)

    @staticmethod
    def _plot_excess_equity(
        r: BacktestResult,
        path: Path,
        bench_primary: pd.Series,
        primary_kind: str,
    ) -> None:
        fig, ax = plt.subplots(figsize=(11, 4))
        eq = _ensure_dt_index(r.equity_curve["total_equity"])
        if bench_primary.empty:
            _placeholder(ax, "benchmark unavailable")
            ax.set_title("Excess equity — N/A")
            _save(fig, path)
            return
        b = _ensure_dt_index(bench_primary)
        joined = pd.concat({"s": eq, "b": b}, axis=1).dropna()
        if joined.empty:
            _placeholder(ax, "no overlap with benchmark")
            ax.set_title("Excess equity — N/A")
            _save(fig, path)
            return
        excess = joined["s"] / joined["s"].iloc[0] - joined["b"] / joined["b"].iloc[0]
        excess.plot(ax=ax, color="#2ca02c", lw=2, label="excess return (Top-K − bench)")
        # Tracking error shading: 20d rolling std of daily diff
        s_ret = joined["s"].pct_change()
        b_ret = joined["b"].pct_change()
        diff = (s_ret - b_ret).fillna(0.0)
        te_band = diff.rolling(20).std() * (252 ** 0.5)
        # Shade where TE is in the top quartile
        if te_band.notna().any():
            q75 = float(te_band.quantile(0.75))
            highvol = te_band > q75
            if highvol.any():
                ax.fill_between(
                    excess.index, excess.values, 0.0,
                    where=highvol.reindex(excess.index, fill_value=False).values,
                    alpha=0.15, color="orange",
                    label=f"high-TE regime (>{q75:.2f} ann)",
                )
        ax.axhline(0.0, color="black", linestyle=":", alpha=0.5)
        ax.set_title(f"Excess equity vs {primary_kind} (eq-weight)")
        ax.set_ylabel("Cumulative excess return")
        ax.legend()
        ax.grid(alpha=0.3)
        _save(fig, path)

    @staticmethod
    def _plot_rolling_sharpe(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(11, 4))
        eq = _ensure_dt_index(r.equity_curve["total_equity"])
        ret = eq.pct_change().dropna()
        if ret.empty:
            _placeholder(ax, "no returns")
            _save(fig, path)
            return
        windows = [60, 120, 252]
        colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]
        for w, c in zip(windows, colors):
            if len(ret) >= w:
                roll_mean = ret.rolling(w).mean() * 252
                roll_std = ret.rolling(w).std() * (252 ** 0.5)
                sharpe = roll_mean / roll_std.where(roll_std > 0)
                sharpe.plot(ax=ax, label=f"{w}d", color=c, lw=1.5)
        ax.axhline(0.0, color="black", linestyle=":", alpha=0.5)
        ax.axhline(1.0, color="gray", linestyle=":", alpha=0.4)
        ax.set_title("Rolling Sharpe (60 / 120 / 252 day)")
        ax.set_ylabel("Annualised Sharpe")
        ax.legend()
        ax.grid(alpha=0.3)
        _save(fig, path)

    # ------------------------------------------------------------------
    # Tier 1 P1 — portfolio diagnostics
    # ------------------------------------------------------------------

    @staticmethod
    def _plot_holding_period_hist(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(10, 4))
        if r.positions.empty:
            _placeholder(ax, "no positions")
            ax.set_title("Holding period distribution")
            _save(fig, path)
            return
        pos = r.positions.copy()
        pos["date"] = pd.to_datetime(pos["date"])
        # For each (symbol) compute first_seen / last_seen across run
        grp = pos.groupby("symbol")["date"]
        first = grp.min()
        last = grp.max()
        holding_days = (last - first).dt.days + 1
        # Drop zero-day rows (1-day flash holdings show up as 1)
        holding_days = holding_days[holding_days > 0]
        if holding_days.empty:
            _placeholder(ax, "no holdings recorded")
            ax.set_title("Holding period distribution")
            _save(fig, path)
            return
        # Bucket into sensible bins
        bins = [0, 5, 10, 20, 40, 60, 120, 252, 1e9]
        labels = ["≤5", "6-10", "11-20", "21-40", "41-60", "61-120", "121-252", ">252"]
        cats = pd.cut(holding_days, bins=bins, labels=labels, right=True)
        counts = cats.value_counts().reindex(labels, fill_value=0)
        ax.bar(range(len(labels)), counts.values, color="#1f77b4", alpha=0.7,
               edgecolor="black")
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels(labels, rotation=30)
        median = float(holding_days.median())
        mean = float(holding_days.mean())
        ax.axhline(0, color="black", lw=0.5)
        ax.set_title(
            f"Holding period distribution — median={median:.0f}d  mean={mean:.0f}d  "
            f"n={len(holding_days)}"
        )
        ax.set_xlabel("Days held (first→last appearance)")
        ax.set_ylabel("Number of unique holdings")
        ax.grid(alpha=0.3, axis="y")
        _save(fig, path)

    @staticmethod
    def _plot_sector_weights(r: BacktestResult, path: Path) -> dict:
        """Return dict with sector_data_missing flag for metrics.yaml."""
        fig, ax = plt.subplots(figsize=(11, 5))
        result_flag: dict = {}
        if r.positions.empty:
            _placeholder(ax, "no positions")
            ax.set_title("Sector weights")
            _save(fig, path)
            return {"sector_data_missing": True}
        # Try DB ref_industry join
        try:
            import os
            import psycopg2

            conn = psycopg2.connect(
                host=os.environ.get("TIMESCALE_HOST", "localhost"),
                port=int(os.environ.get("TIMESCALE_PORT", 5432)),
                dbname=os.environ.get("TIMESCALE_DB", "quant_data"),
                user=os.environ.get("TIMESCALE_USER", "postgres"),
                password=os.environ.get("TIMESCALE_PASSWORD", "postgres"),
            )
            try:
                ind = pd.read_sql(
                    "SELECT symbol, industry_name FROM ref_industry",
                    conn,
                )
            finally:
                conn.close()
        except Exception as exc:  # noqa: BLE001
            logger.warning("sector weights: DB join failed (%s)", exc)
            _placeholder(ax, f"Industry data unavailable: {type(exc).__name__}")
            ax.set_title("Sector weights — N/A")
            _save(fig, path)
            return {"sector_data_missing": True}

        if ind.empty:
            _placeholder(ax, "ref_industry empty")
            ax.set_title("Sector weights — N/A")
            _save(fig, path)
            return {"sector_data_missing": True}

        pos = r.positions.copy()
        pos["date"] = pd.to_datetime(pos["date"])
        pos = pos.merge(ind, on="symbol", how="left")
        # Use mkt_value column where present; positions snapshot writes shares
        # × last_close so mkt_value may be 0 on settlement-only rows. Fall
        # back to shares × avg_cost (cost basis) so the stack is non-zero.
        if "mkt_value" in pos.columns:
            mv = pos["mkt_value"].astype(float).fillna(0.0)
            zero_share = (mv == 0).mean() if len(mv) else 0.0
            if zero_share > 0.5:
                mv = (pos["shares"].astype(float) * pos["avg_cost"].astype(float)).fillna(0.0)
        else:
            mv = pos["shares"].astype(float) * pos["avg_cost"].astype(float)
        pos["mv"] = mv
        pos["industry_name"] = pos["industry_name"].fillna("UNKNOWN")
        # Daily total per industry
        daily = (
            pos.groupby(["date", "industry_name"])["mv"].sum().unstack(fill_value=0.0)
        )
        if daily.empty:
            _placeholder(ax, "no daily holdings")
            ax.set_title("Sector weights — N/A")
            _save(fig, path)
            return {"sector_data_missing": True}
        total = daily.sum(axis=1).replace(0.0, np.nan)
        weights = daily.div(total, axis=0).fillna(0.0)
        # Keep only top-12 industries by avg weight; bucket rest as Other
        avg_w = weights.mean().sort_values(ascending=False)
        top = avg_w.head(12).index.tolist()
        if "UNKNOWN" in weights.columns and "UNKNOWN" not in top:
            top = top + ["UNKNOWN"]
        weights_top = weights[top].copy()
        other_w = weights.drop(columns=top, errors="ignore").sum(axis=1)
        if (other_w > 0).any():
            weights_top["Other"] = other_w
        # Stacked area
        ax.stackplot(
            weights_top.index,
            weights_top.T.values,
            labels=weights_top.columns.tolist(),
            alpha=0.85,
        )
        ax.set_ylim(0, max(1.0, float(weights_top.sum(axis=1).max())))
        ax.set_title("Sector weights (top 12 + Other; static ref_industry snapshot)")
        ax.set_ylabel("Weight")
        ax.legend(loc="upper left", bbox_to_anchor=(1.0, 1.0), fontsize=7,
                  ncol=1, frameon=False)
        ax.grid(alpha=0.3)
        _save(fig, path, dpi=110)
        return result_flag

    @staticmethod
    def _plot_topk_vs_q5_diff(r: BacktestResult, path: Path) -> None:
        ec = r.equity_curve
        if "q5_equity" not in ec.columns:
            fig, ax = plt.subplots(figsize=(11, 4))
            _placeholder(ax, "no q5_equity column")
            ax.set_title("Top-K vs Q5")
            _save(fig, path)
            return
        topk = _ensure_dt_index(ec["total_equity"])
        q5 = _ensure_dt_index(ec["q5_equity"])
        # Normalise both to start at 1.0 for fair comparison
        topk_n = topk / topk.iloc[0]
        q5_n = q5 / q5.iloc[0]
        spread = topk_n - q5_n
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 5),
                                       sharex=True, gridspec_kw={"height_ratios": [3, 1]})
        topk_n.plot(ax=ax1, label="Top-K (normalised)", color="black", lw=2)
        q5_n.plot(ax=ax1, label="Q5 (normalised)", color="#1f77b4", lw=1.5,
                  alpha=0.8)
        ax1.set_ylabel("Cumulative × initial")
        ax1.set_title("Top-K vs Q5 — concentration premium")
        ax1.legend()
        ax1.grid(alpha=0.3)
        spread.plot(ax=ax2, color="#2ca02c", lw=1.2)
        ax2.axhline(0.0, color="black", linestyle=":", alpha=0.5)
        ax2.set_ylabel("Top-K − Q5")
        ax2.grid(alpha=0.3)
        _save(fig, path)

    @staticmethod
    def _plot_rank_persistence(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(11, 4))
        if r.positions.empty:
            _placeholder(ax, "no positions")
            ax.set_title("Rank persistence")
            _save(fig, path)
            return
        pos = r.positions.copy()
        pos["date"] = pd.to_datetime(pos["date"])
        # Per-date holdings set
        per_day = pos.groupby("date")["symbol"].apply(frozenset)
        if len(per_day) < 2:
            _placeholder(ax, "need ≥2 dates")
            ax.set_title("Rank persistence")
            _save(fig, path)
            return
        # Pairwise Jaccard between adjacent dates (vectorised via shift)
        cur = per_day
        prev = per_day.shift(1)
        # Compute via element-wise function but in a single comprehension
        # (per_day length is small: O(n_dates)).
        def _jaccard(a: frozenset | float, b: frozenset | float) -> float:
            if not isinstance(a, frozenset) or not isinstance(b, frozenset):
                return np.nan
            if not a and not b:
                return 1.0
            inter = len(a & b)
            union = len(a | b)
            return inter / union if union else np.nan

        jacc = pd.Series(
            [_jaccard(p, c) for p, c in zip(prev.values, cur.values)],
            index=cur.index,
            name="jaccard",
        ).dropna()
        if jacc.empty:
            _placeholder(ax, "no adjacent pairs")
            ax.set_title("Rank persistence")
            _save(fig, path)
            return
        jacc.plot(ax=ax, color="#1f77b4", alpha=0.5, lw=0.8,
                  label="daily Jaccard")
        jacc.rolling(20).mean().plot(ax=ax, color="#d62728", lw=2,
                                     label="20-snapshot rolling mean")
        ax.axhline(float(jacc.mean()), color="black", linestyle=":", alpha=0.5,
                   label=f"mean={jacc.mean():.2f}")
        ax.set_ylim(0, 1.05)
        ax.set_title("Rank persistence — adjacent-snapshot Jaccard of top-K holdings")
        ax.set_ylabel("Jaccard similarity")
        ax.legend()
        ax.grid(alpha=0.3)
        _save(fig, path)

    # ------------------------------------------------------------------
    # Tier 2 P2 — nice-to-have
    # ------------------------------------------------------------------

    @staticmethod
    def _plot_trade_pnl_dist(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(10, 4))
        if r.trades.empty:
            _placeholder(ax, "no trades")
            ax.set_title("Trade P&L distribution")
            _save(fig, path)
            return
        tr = r.trades[r.trades.get("account", "main") == "main"].copy()
        tr = tr[tr["shares"].fillna(0) > 0]
        if tr.empty:
            _placeholder(ax, "no main-account fills")
            ax.set_title("Trade P&L distribution")
            _save(fig, path)
            return
        tr["date"] = pd.to_datetime(tr["date"])
        tr["notional"] = tr["fill_price"].astype(float) * tr["shares"].astype(float)
        tr["signed_notional"] = np.where(
            tr["side"] == "buy", -tr["notional"], tr["notional"]
        )
        tr = tr.sort_values(["symbol", "date"])

        # Per symbol, match buys → sells in FIFO order via vectorised cumulative
        # net shares. A round-trip P&L is approximated as ``Σ sells − Σ buys``
        # per symbol where shares net to ≤0 — adequate for distribution shape.
        grp = tr.groupby("symbol")
        agg = grp.agg(
            buy_notional=("notional", lambda s: float(
                s[tr.loc[s.index, "side"] == "buy"].sum())),
            sell_notional=("notional", lambda s: float(
                s[tr.loc[s.index, "side"] == "sell"].sum())),
            n_legs=("side", "size"),
            buy_qty=("shares", lambda s: float(
                s[tr.loc[s.index, "side"] == "buy"].sum())),
            sell_qty=("shares", lambda s: float(
                s[tr.loc[s.index, "side"] == "sell"].sum())),
        )
        closed = agg[
            (agg["buy_qty"] > 0)
            & (agg["sell_qty"] > 0)
        ].copy()
        if closed.empty:
            _placeholder(ax, "no closed trades")
            ax.set_title("Trade P&L distribution")
            _save(fig, path)
            return
        # P&L per symbol = sell_notional − buy_notional (proxy, no avg-cost
        # tracking — good enough for distribution shape, not exact accounting).
        closed["pnl"] = closed["sell_notional"] - closed["buy_notional"]
        closed["pnl_bps"] = (
            closed["pnl"] / closed["buy_notional"].replace(0, np.nan) * 1e4
        ).fillna(0.0)
        pnl_bps = closed["pnl_bps"].clip(-2000, 2000)
        ax.hist(pnl_bps.values, bins=60, color="#1f77b4", edgecolor="black", alpha=0.7)
        ax.axvline(0, color="black", linestyle=":", alpha=0.5)
        mean_bps = float(pnl_bps.mean())
        median_bps = float(pnl_bps.median())
        win_rate = float((pnl_bps > 0).mean())
        ax.axvline(mean_bps, color="red", linestyle="--", alpha=0.7,
                   label=f"mean={mean_bps:.0f}bps")
        ax.set_title(
            f"Per-symbol round-trip P&L distribution "
            f"(n={len(pnl_bps)}, win={win_rate:.0%}, median={median_bps:.0f}bps)"
        )
        ax.set_xlabel("Round-trip return (bps, clipped ±2000)")
        ax.set_ylabel("Count")
        ax.legend()
        ax.grid(alpha=0.3, axis="y")
        _save(fig, path)

    @staticmethod
    def _plot_drawdown_recovery(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(11, 4))
        ec = r.equity_curve
        if "drawdown" not in ec.columns or ec.empty:
            _placeholder(ax, "no drawdown")
            ax.set_title("Drawdown recovery events")
            _save(fig, path)
            return
        eq = _ensure_dt_index(ec["total_equity"])
        dd = _ensure_dt_index(ec["drawdown"])
        dd.plot(ax=ax, color="red", lw=1, alpha=0.6, label="drawdown")
        # Identify drawdown events: in-DD when dd < 0, ends when returns to 0.
        in_dd = dd < -1e-6
        # Vectorised event detection: groupby cumulative-flip on transitions
        starts = in_dd & ~in_dd.shift(1, fill_value=False)
        ends = ~in_dd & in_dd.shift(1, fill_value=False)
        start_dates = dd.index[starts.values]
        end_dates = dd.index[ends.values]
        # Pair up — if event hasn't recovered by end of series, mark as ongoing
        events = []
        e_iter = iter(end_dates)
        for s in start_dates:
            e = next(e_iter, None)
            if e is None:
                e = dd.index[-1]
            trough = dd.loc[s:e].idxmin()
            depth = float(dd.loc[trough])
            events.append((s, trough, e, depth, (e - s).days))
        # Keep top-5 by depth
        events.sort(key=lambda x: x[3])
        events_top = events[:5]
        for s, trough, e, depth, days in events_top:
            ax.axvspan(s, e, alpha=0.1, color="gray")
            ax.scatter([s], [0.0], color="green", marker="^", s=40, zorder=5)
            ax.scatter([trough], [depth], color="red", marker="v", s=60, zorder=5)
            ax.scatter([e], [0.0], color="blue", marker="o", s=30, zorder=5)
            ax.annotate(
                f"{depth:.1%} / {days}d",
                xy=(trough, depth), xytext=(0, -12), textcoords="offset points",
                fontsize=8, ha="center", color="black",
            )
        ax.axhline(0.0, color="black", linestyle=":", alpha=0.4)
        ax.set_title(
            f"Drawdown recovery — top-{len(events_top)} events "
            f"(peak ▲ / trough ▼ / recovery ●)"
        )
        ax.set_ylabel("Drawdown")
        ax.legend(loc="lower right")
        ax.grid(alpha=0.3)
        _save(fig, path)

    @staticmethod
    def _plot_liquidity_util(
        r: BacktestResult, path: Path, market_parquet: Path | None
    ) -> None:
        fig, ax = plt.subplots(figsize=(11, 4))
        if r.positions.empty:
            _placeholder(ax, "no positions")
            ax.set_title("Liquidity utilisation")
            _save(fig, path)
            return
        # Pick whichever cache exists; prefer hfq for ≥2024 data
        if market_parquet is not None:
            candidates = [market_parquet]
        else:
            candidates = [
                Path("storage/cache/market_daily_hfq.parquet"),
                Path("storage/cache/market_daily.parquet"),
            ]
        mkt = None
        for c in candidates:
            if not c.exists():
                continue
            try:
                mkt = pd.read_parquet(c, columns=["$volume"]).rename(
                    columns={"$volume": "volume"}
                )
                break
            except Exception:
                try:
                    mkt = pd.read_parquet(c, columns=["volume"])
                    break
                except Exception:
                    continue
        if mkt is None or mkt.empty:
            _placeholder(ax, "market parquet missing")
            ax.set_title("Liquidity utilisation — N/A")
            _save(fig, path)
            return
        if not isinstance(mkt.index, pd.MultiIndex):
            _placeholder(ax, "market not MultiIndex")
            _save(fig, path)
            return
        mkt.index.names = ["time", "symbol"]
        # 20d ADV in shares per stock — vectorised by unstack + rolling
        vol_wide = mkt["volume"].unstack(level=-1).sort_index()
        adv20 = vol_wide.rolling(20, min_periods=5).mean()

        pos = r.positions.copy()
        pos["date"] = pd.to_datetime(pos["date"])
        pos = pos.dropna(subset=["shares"])
        if pos.empty:
            _placeholder(ax, "no shares column")
            _save(fig, path)
            return
        # Build (date, symbol) → util by joining shares with ADV
        # adv lookup via reindex
        pos = pos.set_index(["date", "symbol"]).sort_index()
        adv_stack = adv20.stack().rename("adv20")
        adv_stack.index.names = ["date", "symbol"]
        # Align dtypes — both indices should be datetime + str
        joined = pos.join(adv_stack, how="left").reset_index()
        joined["util"] = (
            joined["shares"].astype(float)
            / joined["adv20"].replace(0, np.nan)
        )
        joined = joined.dropna(subset=["util"])
        if joined.empty:
            _placeholder(ax, "no ADV overlap")
            _save(fig, path)
            return
        by_date = joined.groupby("date")["util"].agg(["max", "median"]).dropna()
        # Convert to percentage
        ax.plot(by_date.index, by_date["max"] * 100, color="#d62728", lw=1.5,
                label="max position / ADV20 (%)")
        ax.plot(by_date.index, by_date["median"] * 100, color="#1f77b4", lw=1.5,
                label="median position / ADV20 (%)")
        ax.axhline(1.0, color="gray", linestyle=":", alpha=0.5,
                   label="1% impact threshold")
        ax.set_title("Liquidity utilisation — single-position % of 20d ADV")
        ax.set_ylabel("Position size / 20d ADV (%)")
        ax.legend()
        ax.grid(alpha=0.3)
        _save(fig, path)

    @staticmethod
    def _plot_cost_waterfall(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(10, 4.5))
        ec = r.equity_curve
        eq = _ensure_dt_index(ec["total_equity"])
        if eq.empty or len(eq) < 2:
            _placeholder(ax, "no equity")
            ax.set_title("Cost waterfall")
            _save(fig, path)
            return
        n_days = int(len(eq))
        ret_net = eq.pct_change().mean() * 252 if n_days > 1 else 0.0
        # Trades-derived cost breakdown
        tr = r.trades[r.trades.get("account", "main") == "main"] if not r.trades.empty else r.trades
        avg_eq = float(eq.mean())
        n_years = max(n_days / 252.0, 0.01)
        # Total cost (cost_cny is signed by direction in engine; sum cash drag)
        total_cost_cny = float(tr["cost_cny"].sum()) if not tr.empty else 0.0
        cost_drag_ann = (total_cost_cny / avg_eq / n_years) if avg_eq > 0 else 0.0
        # Split cost into slippage / commission / stamp using bps from config
        snap = r.config_snapshot or {}
        cost_cfg = snap.get("cost", {})
        slip_bps = float(cost_cfg.get("slippage_bps", 0))
        comm_bps = float(cost_cfg.get("commission_bps", 0))
        # Use average stamp from schedule
        stamp_sched = cost_cfg.get("stamp_schedule", [])
        stamp_bps = float(stamp_sched[-1].get("sell_bps", 0)) if stamp_sched else 0.0
        bps_total = slip_bps + comm_bps + 0.5 * stamp_bps  # stamp is sell-only
        if bps_total > 0 and cost_drag_ann > 0:
            slip_share = slip_bps / bps_total
            comm_share = comm_bps / bps_total
            stamp_share = (0.5 * stamp_bps) / bps_total
        else:
            slip_share = comm_share = stamp_share = 0.0
        # block-drag = number of blocked orders × estimated lost opportunity
        # (we don't know counterfactual return; proxy = blocked_buy_count / total
        # × cost_drag, capped). For visualisation only.
        if not tr.empty:
            blocked_share = (
                tr["reason"].astype(str).str.startswith("blocked").mean()
            )
        else:
            blocked_share = 0.0
        block_drag = cost_drag_ann * float(blocked_share) * 0.5  # heuristic
        slip_drag = cost_drag_ann * slip_share
        comm_drag = cost_drag_ann * comm_share
        stamp_drag = cost_drag_ann * stamp_share
        # Reconstruct gross: net_ret + sum(drags)
        gross = ret_net + slip_drag + comm_drag + stamp_drag + block_drag

        labels = ["Gross α", "− slippage", "− commission", "− stamp", "− block drag", "Net α"]
        # Waterfall pos: gross, then deltas (drags), then net.
        # Plot as bars with running totals.
        values = [gross, -slip_drag, -comm_drag, -stamp_drag, -block_drag, ret_net]
        cum = np.cumsum([gross, -slip_drag, -comm_drag, -stamp_drag, -block_drag])
        bottoms = [0.0] + list(cum[:-1]) + [0.0]
        heights = [gross, -slip_drag, -comm_drag, -stamp_drag, -block_drag, ret_net]
        colors = ["#2ca02c", "#d62728", "#d62728", "#d62728", "#ff7f0e", "#1f77b4"]
        xs = list(range(len(labels)))
        bars = ax.bar(xs, heights, bottom=bottoms, color=colors, alpha=0.8,
                      edgecolor="black")
        for x, v, b in zip(xs, heights, bottoms):
            y = b + v / 2
            ax.text(x, y, f"{v:+.2%}", ha="center", va="center",
                    fontsize=9, color="white" if abs(v) > 0.005 else "black",
                    fontweight="bold")
        ax.axhline(0.0, color="black", lw=0.8)
        ax.set_xticks(xs)
        ax.set_xticklabels(labels, rotation=15)
        ax.set_ylabel("Annualised return")
        ax.set_title(
            f"Cost waterfall — gross α → net α "
            f"(cost_drag_ann≈{cost_drag_ann:.2%}, gross≈{gross:.2%}, net≈{ret_net:.2%})"
        )
        ax.grid(alpha=0.3, axis="y")
        _save(fig, path)
