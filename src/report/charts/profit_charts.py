"""Profit chart family — quintile returns + long-short.

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
    tr = q_train.mean() * ANNUALIZE
    va = q_val.mean() * ANNUALIZE
    fig = go.Figure()
    fig.add_trace(go.Bar(x=tr.index, y=tr.values, name="IS annualized"))
    fig.add_trace(go.Bar(x=va.index, y=va.values, name="OOS annualized"))
    fig.update_layout(title="Quintile Annualized Return (IS vs OOS)",
                      xaxis_title="Quintile", yaxis_title="Annual return",
                      barmode="group")
    return fig


def chart_quintile_returns_oos(q_val: pd.DataFrame) -> go.Figure:
    means = q_val.mean()
    fig = go.Figure(data=go.Bar(x=means.index, y=means.values,
                                 marker=dict(color="#ef4444")))
    fig.update_layout(title="OOS Quintile Daily Mean Return",
                       xaxis_title="Quintile", yaxis_title="Mean daily return")
    return fig


def chart_cumulative_returns(q_train: pd.DataFrame, q_val: pd.DataFrame) -> go.Figure:
    merged = pd.concat([q_train, q_val]).sort_index()
    cum = (1.0 + merged).cumprod()
    fig = go.Figure()
    for col in cum.columns:
        fig.add_trace(go.Scatter(x=cum.index, y=cum[col].values,
                                  mode="lines", name=col))
    fig.update_layout(title="Quintile Cumulative Net Value",
                       xaxis_title="Date", yaxis_title="Net value (start=1)")
    return fig


def chart_long_short(ls_daily: pd.DataFrame) -> go.Figure:
    if "split" in ls_daily.index.names:
        levels = ls_daily.index.get_level_values("split")
        tr = (ls_daily.xs("train", level="split")["long_short"]
              if "train" in levels else pd.Series(dtype=float))
        va = (ls_daily.xs("validation", level="split")["long_short"]
              if "validation" in levels else pd.Series(dtype=float))
        combined = pd.concat([tr, va]).sort_index()
    else:
        combined = ls_daily["long_short"]
    cum = (1.0 + combined).cumprod()
    fig = go.Figure(data=go.Scatter(x=cum.index, y=cum.values, mode="lines",
                                      name="Q_last − Q1"))
    fig.update_layout(title="Long-Short Cumulative Net Value",
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
