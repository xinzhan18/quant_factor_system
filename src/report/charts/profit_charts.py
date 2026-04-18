"""Profit chart family — quintile returns + long-short (merged).

Consumes Phase 2 diagnostic parquets:
* quantile_daily_train.parquet / quantile_daily_validation.parquet
  (index=datetime, columns=q1..q5, values=daily return of that quintile)
* long_short_daily.parquet (MultiIndex(split, datetime), column=long_short)

All functions are pure — no recomputation, no IO.
"""
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go

ANNUALIZE = 252


def chart_quintile_bar(q_train: pd.DataFrame, q_val: pd.DataFrame) -> go.Figure:
    """Annualized quintile returns, IS vs OOS grouped."""
    tr = q_train.mean() * ANNUALIZE
    va = q_val.mean() * ANNUALIZE
    fig = go.Figure()
    fig.add_trace(go.Bar(x=tr.index, y=tr.values, name="IS annualized"))
    fig.add_trace(go.Bar(x=va.index, y=va.values, name="OOS annualized"))
    fig.update_layout(title="Quintile Annualized Return (IS vs OOS)",
                      xaxis_title="Quintile", yaxis_title="Annual return",
                      barmode="group")
    return fig


def chart_cumulative_returns(
    q_train: pd.DataFrame,
    q_val: pd.DataFrame,
    ls_daily: pd.DataFrame | None = None,
) -> go.Figure:
    """Quintile cumulative net value + long-short overlay (if ls_daily given)."""
    merged = pd.concat([q_train, q_val]).sort_index()
    cum = (1.0 + merged).cumprod()
    fig = go.Figure()
    for col in cum.columns:
        fig.add_trace(go.Scatter(x=cum.index, y=cum[col].values,
                                  mode="lines", name=col))
    if ls_daily is not None:
        if "split" in ls_daily.index.names:
            levels = ls_daily.index.get_level_values("split")
            tr = (ls_daily.xs("train", level="split")["long_short"]
                  if "train" in levels else pd.Series(dtype=float))
            va = (ls_daily.xs("validation", level="split")["long_short"]
                  if "validation" in levels else pd.Series(dtype=float))
            ls_combined = pd.concat([tr, va]).sort_index()
        else:
            ls_combined = ls_daily["long_short"]
        if not ls_combined.empty:
            ls_cum = (1.0 + ls_combined).cumprod()
            fig.add_trace(go.Scatter(x=ls_cum.index, y=ls_cum.values,
                                      mode="lines", name="L/S (Q_last − Q1)",
                                      line=dict(color="#111827", width=2.5, dash="dash")))
    fig.update_layout(title="Quintile + L/S Cumulative Net Value",
                       xaxis_title="Date", yaxis_title="Net value (start=1)")
    return fig


def chart_annual_group_returns(q_train: pd.DataFrame, q_val: pd.DataFrame) -> go.Figure:
    merged = pd.concat([q_train, q_val]).sort_index()
    work = merged.copy()
    work["year"] = work.index.year
    ann = work.groupby("year").apply(
        lambda g: ((1.0 + g.drop(columns=["year"])).prod() - 1.0)
    )
    fig = go.Figure(data=go.Heatmap(z=ann.values, x=ann.columns, y=ann.index,
                                     colorscale="RdYlGn", zmid=0))
    fig.update_layout(title="Annual Quintile Returns",
                       xaxis_title="Quintile", yaxis_title="Year")
    return fig
