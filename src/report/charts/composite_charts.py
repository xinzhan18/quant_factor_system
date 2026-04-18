"""Composite radar chart — 7 sub-scores + overall grade in title."""
from __future__ import annotations

import plotly.graph_objects as go


SEVEN_DIMS = [
    "predictive_power", "signal_stability", "profitability",
    "monotonicity", "oos_robustness", "uniqueness", "decay_resistance",
]


def chart_radar(composite: dict) -> go.Figure:
    values = [composite.get(k, 0.0) for k in SEVEN_DIMS]
    fig = go.Figure(data=go.Scatterpolar(
        r=values + [values[0]],  # close the polygon
        theta=[k.replace("_", " ").title() for k in SEVEN_DIMS]
              + [SEVEN_DIMS[0].replace("_", " ").title()],
        fill="toself",
    ))
    fig.update_layout(
        title=(f"Composite Radar  (Score={composite.get('score', 0)}, "
               f"Grade={composite.get('grade', '-')})"),
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=False,
    )
    return fig
