"""Risk charts — style exposure + alpha waterfall.

Input: result.yaml candidate['barra'] dict + validation IC scalar.
"""
from __future__ import annotations

import plotly.graph_objects as go


def chart_style_exposure_bar(barra: dict) -> go.Figure:
    exps = barra.get("style_exposures", {}) or {}
    names = list(exps.keys())
    vals = [exps[k] for k in names]
    fig = go.Figure(data=go.Bar(x=names, y=vals))
    fig.update_layout(title="Barra Style Exposures",
                       xaxis_title="Style factor",
                       yaxis_title="Exposure coefficient")
    return fig


def chart_alpha_waterfall(raw_val_ic: float, barra: dict) -> go.Figure:
    residual = barra.get("barra_residual_ic", raw_val_ic)
    survive = barra.get("alpha_survival_ratio")
    fig = go.Figure(data=go.Bar(
        x=["Raw IC (val)", "Barra Residual IC"],
        y=[raw_val_ic, residual],
        marker=dict(color=["#3b82f6", "#ef4444"]),
    ))
    subtitle = f"alpha_survival = {survive:.2f}" if survive is not None else ""
    fig.update_layout(title=f"Alpha Waterfall  {subtitle}".strip(),
                       yaxis_title="IC value")
    return fig
