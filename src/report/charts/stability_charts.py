"""Stability charts — support windows + overall stability summary.

Inputs: result.yaml candidate['stability'] + candidate['ic'] scalars.
"""
from __future__ import annotations

import plotly.graph_objects as go


def chart_support_window_ic(split_stability: dict) -> go.Figure:
    means = split_stability.get("split_ic_means") or []
    labels = [f"W{i+1}" for i in range(len(means))]
    fig = go.Figure(data=go.Bar(x=labels, y=list(means)))
    sign_c = split_stability.get("sign_consistency")
    subtitle = f"(sign_consistency={sign_c})" if sign_c is not None else ""
    fig.update_layout(title=f"Support Windows IC  {subtitle}".strip(),
                       xaxis_title="Window", yaxis_title="Mean IC")
    return fig


def chart_stability_summary(candidate: dict) -> go.Figure:
    ic = candidate.get("ic", {}) or {}
    stab = (candidate.get("stability", {}) or {}).get("split_stability", {}) or {}
    rows = {
        "IS→Val decay": ic.get("train_validation_decay") or 0.0,
        "Sign consistency": stab.get("sign_consistency") or 0.0,
        "Dispersion (σ)": stab.get("dispersion") or 0.0,
    }
    fig = go.Figure(data=go.Bar(x=list(rows.keys()), y=list(rows.values())))
    fig.update_layout(title="Stability Summary")
    return fig
