"""Profit chart family — quintile returns + long-short (separate).

Consumes Phase 2 diagnostic parquets:
* quantile_daily_train.parquet / quantile_daily_validation.parquet
  (index=datetime, columns=q1..q5, values=daily return of that quintile)
* long_short_daily.parquet (MultiIndex(split, datetime), column=long_short)

Optionally consumes report-time holdout (2024) quintile returns derived
from `backtest/holdout/equity_curve.parquet` (q1_equity..q5_equity →
pct_change). Holdout is report-only — Phase 2/3 never see it.

All functions are pure — no recomputation, no IO.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

ANNUALIZE = 252

# Region styling — kept consistent across all profit charts.
_REGION_COLORS = {
    "IS": "rgba(136,136,136,0.10)",       # gray
    "OOS": "rgba(31,119,180,0.10)",       # blue
    "Holdout": "rgba(214,39,40,0.10)",    # red
}
_REGION_LINE = {
    "IS": "#888888",
    "OOS": "#1f77b4",
    "Holdout": "#d62728",
}


def _add_region_shading(fig: go.Figure,
                         q_train: pd.DataFrame,
                         q_val: pd.DataFrame,
                         q_holdout: pd.DataFrame | None) -> None:
    """Paint IS / OOS / Holdout vertical bands + boundary lines + top annotations."""
    spans = []
    if not q_train.empty:
        spans.append(("IS",       q_train.index.min(),   q_train.index.max()))
    if not q_val.empty:
        spans.append(("OOS",      q_val.index.min(),     q_val.index.max()))
    if q_holdout is not None and not q_holdout.empty:
        spans.append(("Holdout",  q_holdout.index.min(), q_holdout.index.max()))
    for label, x0, x1 in spans:
        fig.add_vrect(x0=x0, x1=x1, fillcolor=_REGION_COLORS[label],
                      line_width=0, layer="below")
        fig.add_annotation(x=x0 + (x1 - x0) / 2, y=1.04, xref="x", yref="paper",
                           text=f"<b>{label}</b>", showarrow=False,
                           font=dict(size=11, color=_REGION_LINE[label]))
    # boundary verticals between adjacent regions
    for (_, _, x_end), (_, x_next, _) in zip(spans[:-1], spans[1:]):
        boundary = x_end + (x_next - x_end) / 2
        fig.add_vline(x=boundary, line_width=1, line_dash="dot",
                      line_color="#999999")


def chart_quintile_bar(q_train: pd.DataFrame,
                        q_val: pd.DataFrame,
                        q_holdout: pd.DataFrame | None = None) -> go.Figure:
    """Annualized quintile returns, IS / OOS / Holdout grouped."""
    tr = q_train.mean() * ANNUALIZE
    va = q_val.mean() * ANNUALIZE
    fig = go.Figure()
    fig.add_trace(go.Bar(x=tr.index, y=tr.values, name="IS (train)",
                          marker_color=_REGION_LINE["IS"]))
    fig.add_trace(go.Bar(x=va.index, y=va.values, name="OOS (val)",
                          marker_color=_REGION_LINE["OOS"]))
    if q_holdout is not None and not q_holdout.empty:
        ho = q_holdout.mean() * ANNUALIZE
        fig.add_trace(go.Bar(x=ho.index, y=ho.values, name="Holdout (report-only)",
                              marker_color=_REGION_LINE["Holdout"]))
    fig.update_layout(title="Quintile Annualized Return — IS / OOS / Holdout",
                      xaxis_title="Quintile", yaxis_title="Annual return",
                      barmode="group")
    return fig


def chart_cumulative_returns(q_train: pd.DataFrame,
                              q_val: pd.DataFrame,
                              q_holdout: pd.DataFrame | None = None) -> go.Figure:
    """Quintile cumulative net value across IS / OOS / Holdout regions.

    L/S is intentionally **not** drawn here — see ``chart_long_short_cumulative``.
    Regions are painted as background bands; boundaries marked by dotted lines.
    """
    parts = [q_train, q_val]
    if q_holdout is not None and not q_holdout.empty:
        parts.append(q_holdout)
    merged = pd.concat(parts).sort_index()
    cum = (1.0 + merged).cumprod()
    fig = go.Figure()
    for col in cum.columns:
        fig.add_trace(go.Scatter(x=cum.index, y=cum[col].values,
                                  mode="lines", name=col))
    _add_region_shading(fig, q_train, q_val, q_holdout)
    fig.update_layout(title="Quintile Cumulative Net Value — IS / OOS / Holdout",
                       xaxis_title="Date", yaxis_title="Net value (start=1)")
    return fig


def chart_long_short_cumulative(ls_daily: pd.DataFrame,
                                 q_train: pd.DataFrame,
                                 q_val: pd.DataFrame,
                                 q_holdout: pd.DataFrame | None = None) -> go.Figure:
    """Long-short (Q_last − Q1) cumulative net value, separated from quintile chart.

    ``ls_daily`` carries Phase 2 train + validation L/S as a
    MultiIndex(split, datetime); holdout L/S is derived on the fly from
    ``q_holdout`` (q5 − q1) when provided.

    Regions are shaded identically to ``chart_cumulative_returns`` so the two
    figures align visually.
    """
    if "split" in ls_daily.index.names:
        levels = ls_daily.index.get_level_values("split")
        tr = (ls_daily.xs("train", level="split")["long_short"]
              if "train" in levels else pd.Series(dtype=float))
        va = (ls_daily.xs("validation", level="split")["long_short"]
              if "validation" in levels else pd.Series(dtype=float))
        ls_parts = [tr, va]
    else:
        ls_parts = [ls_daily["long_short"]]
    if q_holdout is not None and not q_holdout.empty:
        q_last = q_holdout.columns[-1]
        ls_parts.append((q_holdout[q_last] - q_holdout["q1"]))
    ls = pd.concat(ls_parts).sort_index()
    fig = go.Figure()
    if not ls.empty:
        ls_cum = (1.0 + ls).cumprod()
        fig.add_trace(go.Scatter(x=ls_cum.index, y=ls_cum.values,
                                  mode="lines", name="L/S (Q_last − Q1)",
                                  line=dict(color="#111827", width=2.0)))
    _add_region_shading(fig, q_train, q_val, q_holdout)
    fig.update_layout(title="Long-Short Cumulative Net Value — IS / OOS / Holdout",
                       xaxis_title="Date", yaxis_title="Net value (start=1)")
    return fig


def chart_annual_group_returns(q_train: pd.DataFrame,
                                q_val: pd.DataFrame,
                                q_holdout: pd.DataFrame | None = None) -> go.Figure:
    parts = [q_train, q_val]
    if q_holdout is not None and not q_holdout.empty:
        parts.append(q_holdout)
    merged = pd.concat(parts).sort_index()
    work = merged.copy()
    work["year"] = work.index.year
    ann = work.groupby("year").apply(
        lambda g: ((1.0 + g.drop(columns=["year"])).prod() - 1.0)
    )
    fig = go.Figure(data=go.Heatmap(z=ann.values, x=ann.columns, y=ann.index,
                                     colorscale="RdYlGn", zmid=0))
    fig.update_layout(title="Annual Quintile Returns — IS / OOS / Holdout",
                       xaxis_title="Quintile", yaxis_title="Year")
    return fig
