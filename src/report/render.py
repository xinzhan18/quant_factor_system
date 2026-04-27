"""Pure load-and-plot renderer.

Reads:
* ``storage/vault/factors/F{id}.yaml`` → factor metadata
* ``storage/vault/batches/{batch_id}/result.yaml`` → candidate scalars
* ``storage/cache/batch_diagnostics/{batch_id}/{cid}/*.parquet`` → time series
  (path resolved via ``candidate.diagnostics_relpath`` relative to storage_root)

Writes:
* ``storage/vault/factors/F{id}/<chart>.png`` (15 charts)
* ``storage/vault/factors/F{id}/report.json`` (chart manifest + composite scorecard)

NEVER recomputes IC / quintile / Barra — those are Phase 2 outputs.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.graph_objects as go
import yaml

from report.composite import compute_composite
from report.charts.theme import PNG_WIDTH, PNG_HEIGHT, PNG_SCALE
from report.charts.ic_charts import (
    chart_ic_timeseries, chart_rolling_ic,
    chart_ic_distribution, chart_monthly_heatmap,
)
from report.charts.profit_charts import (
    chart_quintile_bar, chart_cumulative_returns, chart_annual_group_returns,
)
from report.charts.risk_charts import chart_style_exposure_bar, chart_alpha_waterfall
from report.charts.stability_charts import chart_stability_panel
from report.charts.decay_charts import (
    chart_ic_decay, chart_factor_distribution, chart_coverage,
)
from report.charts.uniqueness_charts import chart_correlation_bar
from report.charts.composite_charts import chart_radar

logger = logging.getLogger(__name__)


def _load_yaml(p: Path) -> dict:
    with p.open() as f:
        return yaml.safe_load(f) or {}


def _find_candidate(result: dict, key: str) -> dict:
    """Locate a candidate in result.yaml.

    For DSL factors ``key`` is the expression string; for Python factors
    it is the python_path (result.yaml stores it under ``expression``
    for both source types — see factor_writer / mine loop output).
    """
    for c in result.get("candidates", []) or []:
        if c.get("expression") == key:
            return c
    raise ValueError(
        f"No candidate in result.yaml matching key={key!r}"
    )


def _write_png(fig: go.Figure, assets_dir: Path, name: str) -> str:
    out = assets_dir / f"{name}.png"
    fig.write_image(str(out), width=PNG_WIDTH, height=PNG_HEIGHT, scale=PNG_SCALE)
    return name


def render_factor(factor_id: str, storage_root: Path | str = "storage") -> dict[str, Any]:
    storage = Path(storage_root)
    vault = storage / "vault"
    fy = vault / "factors" / f"{factor_id}.yaml"
    meta = _load_yaml(fy)
    # Prefer the most recent recompute batch when present so reports reflect
    # current metrics (the original admit batch is preserved as audit trail).
    batch_id = meta.get("revalidated_in_batch") or meta["admitted_in_batch"]
    result = _load_yaml(vault / "batches" / batch_id / "result.yaml")
    lookup_key = meta.get("expression") or meta.get("python_path")
    if not lookup_key:
        raise ValueError(
            f"factor.yaml for {factor_id} has neither 'expression' nor 'python_path'"
        )
    candidate = _find_candidate(result, lookup_key)

    diag_rel = candidate.get("diagnostics_relpath")
    if not diag_rel:
        raise ValueError(f"candidate for {factor_id} has no diagnostics_relpath")
    diag_dir = storage / diag_rel

    assets_dir = vault / "factors" / factor_id
    assets_dir.mkdir(parents=True, exist_ok=True)
    # Remove stale PNGs from previous renders so chart-set changes don't
    # leave orphan files behind.
    for stale in assets_dir.glob("*.png"):
        stale.unlink()

    ic_daily = pd.read_parquet(diag_dir / "ic_daily.parquet")
    q_train = pd.read_parquet(diag_dir / "quantile_daily_train.parquet")
    q_val = pd.read_parquet(diag_dir / "quantile_daily_validation.parquet")
    ls_daily = pd.read_parquet(diag_dir / "long_short_daily.parquet")
    cov_daily = pd.read_parquet(diag_dir / "coverage_daily.parquet")
    hist_df = pd.read_parquet(diag_dir / "factor_hist.parquet")

    composite = compute_composite(candidate)

    figs = {
        "ic_timeseries": chart_ic_timeseries(ic_daily),
        "rolling_ic": chart_rolling_ic(ic_daily),
        "ic_distribution": chart_ic_distribution(ic_daily),
        "monthly_heatmap": chart_monthly_heatmap(ic_daily),
        "quintile_bar": chart_quintile_bar(q_train, q_val),
        "cumulative_returns": chart_cumulative_returns(q_train, q_val, ls_daily),
        "annual_group_returns": chart_annual_group_returns(q_train, q_val),
        "style_exposure_bar": chart_style_exposure_bar(candidate.get("barra") or {}),
        "alpha_waterfall": chart_alpha_waterfall(
            ((candidate.get("ic") or {}).get("validation") or {}).get("ic_mean") or 0.0,
            candidate.get("barra") or {},
        ),
        "stability_panel": chart_stability_panel(candidate),
        "ic_decay": chart_ic_decay((candidate.get("ic") or {}).get("by_horizon") or {}),
        "factor_distribution": chart_factor_distribution(hist_df),
        "coverage": chart_coverage(cov_daily),
        "correlation_bar": chart_correlation_bar(
            (candidate.get("uniqueness") or {}).get("all_correlations") or {}
        ),
        "radar": chart_radar(composite),
    }

    charts: dict[str, str] = {}
    for name, fig in figs.items():
        try:
            charts[name] = _write_png(fig, assets_dir, name)
        except Exception as exc:
            logger.warning("render_factor: chart %s failed: %s", name, exc)

    manifest = {
        "factor_id": factor_id,
        "batch_id": batch_id,
        "charts": charts,
        "composite": composite,
        "scalars": {
            "ic_validation": (candidate.get("ic") or {}).get("validation"),
            "ic_train": (candidate.get("ic") or {}).get("train"),
            # Time-series stability fields (emitted by Phase 2 onto ``ic.*``).
            # Kept flat so the factor-report subagent can embed them in tables
            # without having to hunt through nested blocks.
            "ic_by_year": (candidate.get("ic") or {}).get("by_year"),
            "ic_autocorr_lag1": (candidate.get("ic") or {}).get("autocorr_lag1"),
            "cum_ic_max_drawdown": (candidate.get("ic") or {}).get("cum_ic_max_drawdown"),
            "worst_quarter_ic": (candidate.get("ic") or {}).get("worst_quarter"),
            "best_quarter_ic": (candidate.get("ic") or {}).get("best_quarter"),
            "train_validation_decay": (candidate.get("ic") or {}).get("train_validation_decay"),
            "sign_consistent": (candidate.get("ic") or {}).get("sign_consistent"),
            # Multi-horizon IC (IS + OOS for 1/3/5/10/20-day holds).
            "ic_by_horizon": (candidate.get("ic") or {}).get("by_horizon"),
            "quintile_train": (candidate.get("quintile") or {}).get("train"),
            "quintile_validation": (candidate.get("quintile") or {}).get("validation"),
            "ls_stats_train": ((candidate.get("quintile") or {}).get("ls_stats") or {}).get("train"),
            "ls_stats_validation": ((candidate.get("quintile") or {}).get("ls_stats") or {}).get("validation"),
            "uniqueness": candidate.get("uniqueness"),
            "barra": candidate.get("barra"),
            "feasibility": candidate.get("feasibility"),
            "distribution": candidate.get("distribution"),
        },
    }
    (assets_dir / "report.json").write_text(
        json.dumps(manifest, default=str, indent=2, ensure_ascii=False)
    )
    return manifest
