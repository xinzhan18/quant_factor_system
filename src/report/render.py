"""Pure load-and-plot renderer.

Reads:
* ``storage/vault/factors/F{id}.yaml`` → factor metadata
* ``storage/vault/batches/{batch_id}/result.yaml`` → candidate scalars
* ``storage/cache/batch_diagnostics/{batch_id}/{cid}/*.parquet`` → time series
  (path resolved via ``candidate.diagnostics_relpath`` relative to storage_root)

Writes:
* ``storage/vault/factors/F{id}/<chart>.png`` (18 charts)
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
    chart_ic_timeseries, chart_cumulative_ic, chart_rolling_ic,
    chart_ic_distribution, chart_monthly_heatmap,
)
from report.charts.profit_charts import (
    chart_quintile_bar, chart_quintile_returns_oos, chart_cumulative_returns,
    chart_long_short, chart_annual_group_returns,
)
from report.charts.risk_charts import chart_style_exposure_bar, chart_alpha_waterfall
from report.charts.stability_charts import chart_support_window_ic, chart_stability_summary
from report.charts.decay_charts import (
    chart_ic_decay, chart_factor_distribution, chart_coverage,
)
from report.charts.uniqueness_charts import chart_correlation_bar
from report.charts.composite_charts import chart_radar

logger = logging.getLogger(__name__)


def _load_yaml(p: Path) -> dict:
    with p.open() as f:
        return yaml.safe_load(f) or {}


def _find_candidate(result: dict, expression: str) -> dict:
    for c in result.get("candidates", []) or []:
        if c.get("expression") == expression:
            return c
    raise ValueError(
        f"No candidate in result.yaml matching expression={expression!r}"
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
    batch_id = meta["admitted_in_batch"]
    result = _load_yaml(vault / "batches" / batch_id / "result.yaml")
    candidate = _find_candidate(result, meta["expression"])

    diag_rel = candidate.get("diagnostics_relpath")
    if not diag_rel:
        raise ValueError(f"candidate for {factor_id} has no diagnostics_relpath")
    diag_dir = storage / diag_rel

    assets_dir = vault / "factors" / factor_id
    assets_dir.mkdir(parents=True, exist_ok=True)

    ic_daily = pd.read_parquet(diag_dir / "ic_daily.parquet")
    q_train = pd.read_parquet(diag_dir / "quantile_daily_train.parquet")
    q_val = pd.read_parquet(diag_dir / "quantile_daily_validation.parquet")
    ls_daily = pd.read_parquet(diag_dir / "long_short_daily.parquet")
    cov_daily = pd.read_parquet(diag_dir / "coverage_daily.parquet")
    hist_df = pd.read_parquet(diag_dir / "factor_hist.parquet")

    composite = compute_composite(candidate)

    figs = {
        "ic_timeseries": chart_ic_timeseries(ic_daily),
        "cumulative_ic": chart_cumulative_ic(ic_daily),
        "rolling_ic": chart_rolling_ic(ic_daily),
        "ic_distribution": chart_ic_distribution(ic_daily),
        "monthly_heatmap": chart_monthly_heatmap(ic_daily),
        "quintile_bar": chart_quintile_bar(q_train, q_val),
        "quintile_returns_oos": chart_quintile_returns_oos(q_val),
        "cumulative_returns": chart_cumulative_returns(q_train, q_val),
        "long_short": chart_long_short(ls_daily),
        "annual_group_returns": chart_annual_group_returns(q_train, q_val),
        "style_exposure_bar": chart_style_exposure_bar(candidate.get("barra") or {}),
        "alpha_waterfall": chart_alpha_waterfall(
            ((candidate.get("ic") or {}).get("validation") or {}).get("ic_mean") or 0.0,
            candidate.get("barra") or {},
        ),
        "support_window_ic": chart_support_window_ic(
            (candidate.get("stability", {}) or {}).get("split_stability", {}) or {}
        ),
        "stability_summary": chart_stability_summary(candidate),
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
            "quintile_validation": (candidate.get("quintile") or {}).get("validation"),
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
