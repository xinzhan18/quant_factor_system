"""Stability panel — support windows + overall stability metrics (merged).

Inputs: result.yaml candidate['stability'] + candidate['ic'] scalars.
"""
from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots


def chart_stability_panel(candidate: dict) -> go.Figure:
    """Two-panel: left=per-window IC bars, right=summary metric bars."""
    stab = (candidate.get("stability", {}) or {}).get("split_stability", {}) or {}
    ic = candidate.get("ic", {}) or {}

    means = stab.get("split_ic_means") or []
    labels = [f"W{i+1}" for i in range(len(means))]
    sign_c = stab.get("sign_consistency")
    left_title = "Support Windows IC"
    if sign_c is not None:
        left_title += f"  (sign_consistency={sign_c})"

    summary = {
        "IS→Val decay": ic.get("train_validation_decay") or 0.0,
        "Sign consistency": stab.get("sign_consistency") or 0.0,
        "Dispersion (σ)": stab.get("dispersion") or 0.0,
    }

    fig = make_subplots(rows=1, cols=2, horizontal_spacing=0.12,
                        subplot_titles=(left_title, "Stability Summary"))
    fig.add_trace(go.Bar(x=labels, y=list(means), showlegend=False,
                         marker=dict(color="#3b82f6")),
                  row=1, col=1)
    fig.add_trace(go.Bar(x=list(summary.keys()), y=list(summary.values()),
                         showlegend=False, marker=dict(color="#10b981")),
                  row=1, col=2)
    fig.update_yaxes(title_text="Mean IC", row=1, col=1)
    fig.update_xaxes(title_text="Window", row=1, col=1)
    fig.update_layout(title="Stability Panel")
    return fig
