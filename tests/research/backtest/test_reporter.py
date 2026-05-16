"""Tests for Reporter — verify all artifacts written."""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import pytest
import yaml

from research.backtest.engine import BacktestResult
from research.backtest.reporter import Reporter


@pytest.fixture
def small_result():
    dates = pd.bdate_range("2024-06-03", periods=10)
    eq = pd.DataFrame(
        dict(
            total_equity=[1_000_000 * (1 + 0.001 * i) for i in range(10)],
            cash=[100_000] * 10,
            pending_cash=[0] * 10,
            q1_equity=[1_000_000] * 10,
            q2_equity=[1_000_000] * 10,
            q3_equity=[1_000_000] * 10,
            q4_equity=[1_000_000] * 10,
            q5_equity=[1_005_000] * 10,
            drawdown=[0.0, -0.001, -0.001, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
        ),
        index=dates,
    )
    eq.index.name = "date"
    trades = pd.DataFrame([
        dict(account="main", date=date(2024, 6, 3), symbol="A", side="buy",
             shares=1000, fill_price=10.0, cost_cny=10.0, reason="target_diff"),
        dict(account="main", date=date(2024, 6, 5), symbol="B", side="buy",
             shares=0, fill_price=10.0, cost_cny=0.0, reason="blocked_buy"),
    ])
    positions = pd.DataFrame([
        dict(date=date(2024, 6, 3), symbol="A", shares=1000,
             locked_until=date(2024, 6, 4),
             avg_cost=10.0, last_close=10.0, mkt_value=10_000),
    ])
    return BacktestResult(
        equity_curve=eq,
        trades=trades,
        positions=positions,
        metrics=dict(
            full=dict(ann_return=0.05, sharpe=0.8, max_dd=-0.001, n_days=10),
            reconciliation=dict(invariant_violations=0, max_violation_bps=0.5),
        ),
        config_snapshot=dict(initial_capital=1_000_000),
        runtime_meta=dict(snapshot_ts="2024-06-12 00:00:00",
                            signal_recompute=False, price_adjust="hfq"),
    )


def test_writes_4_parquets_and_metrics_yaml(small_result, tmp_path):
    Reporter().write(small_result, tmp_path)
    for f in ["equity_curve.parquet", "trades.parquet",
                "positions.parquet", "metrics.yaml"]:
        assert (tmp_path / f).exists(), f"{f} missing"


def test_writes_all_figures(small_result, tmp_path):
    Reporter().write(small_result, tmp_path)
    figs = tmp_path / "figs"
    for name in ["equity", "drawdown", "monthly_heatmap",
                  "layer_decomp", "cost_drag", "blocked_trades"]:
        assert (figs / f"{name}.png").exists(), f"{name}.png missing"


def test_writes_extended_figures(small_result, tmp_path):
    """11 new figures land in figs/ (some are placeholders when data missing)."""
    Reporter().write(small_result, tmp_path)
    figs = tmp_path / "figs"
    extended = [
        "equity_vs_benchmark", "excess_equity", "rolling_sharpe",
        "holding_period_hist", "sector_weight_timeseries", "topk_vs_q5_diff",
        "rank_persistence", "trade_pnl_dist", "drawdown_recovery",
        "liquidity_utilization", "cost_waterfall",
    ]
    for name in extended:
        assert (figs / f"{name}.png").exists(), f"{name}.png missing"


def test_metrics_yaml_has_benchmark_block(small_result, tmp_path):
    Reporter().write(small_result, tmp_path)
    with open(tmp_path / "metrics.yaml") as f:
        loaded = yaml.safe_load(f)
    bench = loaded["metrics"].get("benchmark")
    assert bench is not None, "benchmark block missing"
    for k in ("excess_return_ann", "info_ratio", "tracking_error_ann",
              "alpha", "beta", "available", "kind"):
        assert k in bench, f"benchmark.{k} missing"


def test_metrics_yaml_is_valid_yaml(small_result, tmp_path):
    Reporter().write(small_result, tmp_path)
    with open(tmp_path / "metrics.yaml") as f:
        loaded = yaml.safe_load(f)
    assert "metrics" in loaded
    assert "config_snapshot" in loaded
    assert "runtime_meta" in loaded


def test_equity_parquet_roundtrips(small_result, tmp_path):
    Reporter().write(small_result, tmp_path)
    df = pd.read_parquet(tmp_path / "equity_curve.parquet")
    assert "total_equity" in df.columns
    assert len(df) == 10


def test_trades_parquet_roundtrips(small_result, tmp_path):
    Reporter().write(small_result, tmp_path)
    df = pd.read_parquet(tmp_path / "trades.parquet")
    assert len(df) == 2
    assert "blocked_buy" in df["reason"].values


def test_handles_empty_positions(small_result, tmp_path):
    small_result.positions = pd.DataFrame()
    Reporter().write(small_result, tmp_path)
    # Should not error; positions.parquet exists (empty) — file present
    assert (tmp_path / "positions.parquet").exists()
