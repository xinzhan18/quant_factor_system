"""Uniqueness — library correlation bar chart."""
from __future__ import annotations

import plotly.graph_objects as go


def chart_correlation_bar(all_correlations: dict) -> go.Figure:
    items = sorted(all_correlations.items(),
                    key=lambda kv: -abs(kv[1] or 0.0))[:40]
    names = [k for k, _ in items]
    vals = [v for _, v in items]
    colors = ["#ef4444" if abs(v or 0.0) > 0.7 else "#3b82f6" for v in vals]
    fig = go.Figure(data=go.Bar(x=names, y=vals,
                                 marker=dict(color=colors)))
    fig.update_layout(title="Library Correlation Profile (|corr| descending, top 40)",
                       xaxis_title="Library factor",
                       yaxis_title="Correlation")
    return fig
