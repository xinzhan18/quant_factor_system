"""Decay / distribution / coverage charts.

Consumes:
* candidate['ic']['by_horizon'] dict → ic_decay
* factor_hist.parquet (Phase 2) → factor_distribution
* coverage_daily.parquet (Phase 2) → coverage
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def chart_ic_decay(by_horizon: dict) -> go.Figure:
    horizons = sorted(int(h) for h in by_horizon.keys())
    vals = [
        ((by_horizon.get(h) or by_horizon.get(str(h)) or {}).get("validation") or {}).get("ic_mean") or 0.0
        for h in horizons
    ]
    fig = go.Figure(data=go.Scatter(x=horizons, y=vals, mode="lines+markers"))
    fig.update_layout(title="IC Decay by Holding Period",
                       xaxis_title="Holding period (days)",
                       yaxis_title="Rank IC")
    return fig


def chart_factor_distribution(hist_df: pd.DataFrame) -> go.Figure:
    mids = (hist_df["bin_edge_lo"] + hist_df["bin_edge_hi"]) / 2.0
    fig = go.Figure()
    fig.add_trace(go.Bar(x=mids, y=hist_df["is_freq"], name="IS",
                          opacity=0.55, marker=dict(color="#3b82f6")))
    fig.add_trace(go.Bar(x=mids, y=hist_df["oos_freq"], name="OOS",
                          opacity=0.55, marker=dict(color="#ef4444")))
    fig.update_layout(title="Factor Value Distribution (IS vs OOS)",
                       xaxis_title="Standardized factor value",
                       yaxis_title="Frequency",
                       barmode="overlay")
    return fig


def chart_coverage(cov_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(data=go.Scatter(x=cov_df.index, y=cov_df["coverage"],
                                      mode="lines"))
    fig.update_layout(title="Coverage Over Time",
                       xaxis_title="Date",
                       yaxis_title="Fraction of universe")
    return fig
