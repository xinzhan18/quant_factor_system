"""IC chart family — 5 charts driven entirely by ic_daily.parquet.

Input schema (as written by phase2_execute._persist_diagnostics):
    MultiIndex(split, datetime) × column 'ic'
    split ∈ {'train', 'validation'}

All functions are pure: take the DataFrame, return a plotly Figure.
No recomputation, no IO.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go


def _split_series(ic_daily: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Return (train_series, validation_series) indexed by datetime.
    Empty Series for a missing split."""
    levels = ic_daily.index.get_level_values("split") if "split" in ic_daily.index.names else pd.Index([])
    train = (ic_daily.xs("train", level="split")["ic"]
             if "train" in levels else pd.Series(dtype=float))
    val = (ic_daily.xs("validation", level="split")["ic"]
           if "validation" in levels else pd.Series(dtype=float))
    return train, val


def chart_ic_timeseries(ic_daily: pd.DataFrame) -> go.Figure:
    tr, val = _split_series(ic_daily)
    fig = go.Figure()
    if not tr.empty:
        fig.add_trace(go.Scatter(x=tr.index, y=tr.values, mode="lines",
                                  name="Train", line=dict(color="#3b82f6", width=1)))
    if not val.empty:
        fig.add_trace(go.Scatter(x=val.index, y=val.values, mode="lines",
                                  name="Validation", line=dict(color="#ef4444", width=1)))
    fig.update_layout(title="IC Time Series",
                       xaxis_title="Date", yaxis_title="Rank IC",
                       hovermode="x unified")
    return fig


def chart_cumulative_ic(ic_daily: pd.DataFrame) -> go.Figure:
    tr, val = _split_series(ic_daily)
    combined = pd.concat([tr, val]).sort_index()
    fig = go.Figure()
    if not combined.empty:
        fig.add_trace(go.Scatter(x=combined.index, y=combined.cumsum().values,
                                  mode="lines", name="Cumulative IC"))
    fig.update_layout(title="Cumulative IC",
                       xaxis_title="Date", yaxis_title="Σ Rank IC")
    return fig


def chart_rolling_ic(ic_daily: pd.DataFrame) -> go.Figure:
    tr, val = _split_series(ic_daily)
    combined = pd.concat([tr, val]).sort_index()
    fig = go.Figure()
    for w, color in ((20, "#94a3b8"), (60, "#3b82f6"), (120, "#1e40af")):
        if combined.empty:
            continue
        r = combined.rolling(w, min_periods=max(5, w // 4)).mean()
        fig.add_trace(go.Scatter(x=r.index, y=r.values, mode="lines",
                                  name=f"{w}d", line=dict(color=color)))
    fig.update_layout(title="Rolling IC (20 / 60 / 120 day)",
                       xaxis_title="Date", yaxis_title="Mean IC")
    return fig


def chart_ic_distribution(ic_daily: pd.DataFrame) -> go.Figure:
    tr, val = _split_series(ic_daily)
    fig = go.Figure()
    if not tr.empty:
        fig.add_trace(go.Histogram(x=tr.values, nbinsx=60, name="IS",
                                    opacity=0.55, marker=dict(color="#3b82f6")))
    if not val.empty:
        fig.add_trace(go.Histogram(x=val.values, nbinsx=60, name="OOS",
                                    opacity=0.55, marker=dict(color="#ef4444")))
    fig.update_layout(title="IC Distribution",
                       xaxis_title="Daily IC", yaxis_title="Frequency",
                       barmode="overlay")
    return fig


def chart_monthly_heatmap(ic_daily: pd.DataFrame) -> go.Figure:
    tr, val = _split_series(ic_daily)
    combined = pd.concat([tr, val]).sort_index()
    if combined.empty:
        return go.Figure()
    df = combined.rename("ic").to_frame()
    df["year"] = df.index.year
    df["month"] = df.index.month
    matrix = df.groupby(["year", "month"])["ic"].mean().unstack("month")
    fig = go.Figure(data=go.Heatmap(
        z=matrix.values,
        x=[f"{m:02d}" for m in matrix.columns],
        y=matrix.index,
        colorscale="RdBu",
        zmid=0,
    ))
    fig.update_layout(title="Monthly IC Heatmap",
                       xaxis_title="Month", yaxis_title="Year")
    return fig
