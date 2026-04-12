"""Shared Plotly theme configuration for all report charts."""
from __future__ import annotations
import plotly.graph_objects as go

COLORS = {
    "primary": "#636EFA",
    "secondary": "#EF553B",
    "positive": "#00CC96",
    "negative": "#EF553B",
    "neutral": "#AB63FA",
    "is_period": "#636EFA",
    "oos_period": "#EF553B",
    "quintile": ["#d62728", "#ff7f0e", "#bcbd22", "#2ca02c", "#1f77b4"],
    "long_short": "#9467bd",
}

PNG_WIDTH = 900
PNG_HEIGHT = 400
PNG_SCALE = 2


def apply_theme(fig: go.Figure, title: str | None = None) -> go.Figure:
    """Apply consistent theme to a Plotly figure."""
    fig.update_layout(
        template="plotly_white",
        font=dict(size=12),
        title=dict(text=title, font=dict(size=14)) if title else None,
        margin=dict(l=60, r=30, t=40 if title else 20, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig
