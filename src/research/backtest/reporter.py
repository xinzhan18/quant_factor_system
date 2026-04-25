"""Reporter — write 4 parquets + metrics.yaml + figures."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import yaml

from research.backtest.engine import BacktestResult


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


@dataclass(frozen=True)
class Reporter:
    def write(self, result: BacktestResult, out_dir: Path) -> None:
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        result.equity_curve.to_parquet(out_dir / "equity_curve.parquet")
        result.trades.to_parquet(out_dir / "trades.parquet")
        if not result.positions.empty:
            result.positions.to_parquet(out_dir / "positions.parquet")
        else:
            pd.DataFrame().to_parquet(out_dir / "positions.parquet")

        meta = {
            "metrics": _date_to_iso(result.metrics),
            "config_snapshot": _date_to_iso(result.config_snapshot),
            "runtime_meta": _date_to_iso(result.runtime_meta),
        }
        with open(out_dir / "metrics.yaml", "w") as f:
            yaml.safe_dump(meta, f, sort_keys=False, allow_unicode=True)

        figs_dir = out_dir / "figs"
        figs_dir.mkdir(exist_ok=True)
        self._plot_equity(result, figs_dir / "equity.png")
        self._plot_drawdown(result, figs_dir / "drawdown.png")
        self._plot_monthly_heatmap(result, figs_dir / "monthly_heatmap.png")
        self._plot_layer_decomp(result, figs_dir / "layer_decomp.png")
        self._plot_cost_drag(result, figs_dir / "cost_drag.png")
        self._plot_blocked(result, figs_dir / "blocked_trades.png")

    @staticmethod
    def _plot_equity(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(10, 4))
        r.equity_curve["total_equity"].plot(ax=ax, label="Top-K", color="black", lw=2)
        ax.set_title("Net equity curve")
        ax.legend()
        fig.tight_layout()
        fig.savefig(path, dpi=100)
        plt.close(fig)

    @staticmethod
    def _plot_drawdown(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(10, 3))
        if "drawdown" in r.equity_curve.columns:
            r.equity_curve["drawdown"].plot(ax=ax, color="red")
        ax.set_title("Drawdown")
        ax.set_ylabel("DD")
        fig.tight_layout()
        fig.savefig(path, dpi=100)
        plt.close(fig)

    @staticmethod
    def _plot_monthly_heatmap(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(10, 4))
        ret = r.equity_curve["total_equity"].pct_change().dropna()
        if ret.empty:
            ax.text(0.5, 0.5, "no returns", ha="center", va="center")
            fig.savefig(path, dpi=100)
            plt.close(fig)
            return
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
        fig.tight_layout()
        fig.savefig(path, dpi=100)
        plt.close(fig)

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
        fig.tight_layout()
        fig.savefig(path, dpi=100)
        plt.close(fig)

    @staticmethod
    def _plot_cost_drag(r: BacktestResult, path: Path) -> None:
        fig, ax = plt.subplots(figsize=(10, 3))
        if not r.trades.empty and "cost_cny" in r.trades.columns:
            main_only = r.trades[r.trades.get("account", "main") == "main"]
            if not main_only.empty:
                main_only.groupby("date")["cost_cny"].sum().cumsum().plot(ax=ax)
        ax.set_title("Cumulative cost drag (CNY)")
        fig.tight_layout()
        fig.savefig(path, dpi=100)
        plt.close(fig)

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
        fig.tight_layout()
        fig.savefig(path, dpi=100)
        plt.close(fig)
