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
    """Alpha attribution waterfall: Raw IC → per-style stripping → Residual.

    Uses ``barra['style_contributions']`` (leave-one-out per-style deltas)
    if available to show each style's estimated alpha contribution. Falls
    back to a 2-stage Raw → Residual view if attributions are missing.

    Styles sorted by ``|delta_ic|`` descending (biggest killer first).
    Sum of ``delta_ic`` ≈ ``|raw_ic| − |residual_ic|`` but is not exact
    because styles are correlated; any gap lives in an explicit
    "joint/other" adjustment step so the end-bar equals the real residual.
    """
    raw_abs = abs(raw_val_ic) if raw_val_ic is not None else 0.0
    residual = barra.get("barra_residual_ic")
    residual_abs = abs(residual) if residual is not None else raw_abs
    survive = barra.get("alpha_survival_ratio")
    contribs = barra.get("style_contributions") or []
    contribs = [c for c in contribs if c.get("delta_ic") is not None]

    if not contribs or residual is None:
        # Fallback: 2-stage bar
        fig = go.Figure(data=go.Bar(
            x=["Raw |IC|", "Barra Residual |IC|"],
            y=[raw_abs, residual_abs],
            marker=dict(color=["#3b82f6", "#ef4444"]),
        ))
        subtitle = f"alpha_survival = {survive:.2f}" if survive is not None else ""
        fig.update_layout(title=f"Alpha Waterfall  {subtitle}".strip(),
                           yaxis_title="|IC|")
        return fig

    # Waterfall: Raw (absolute) → per-style relative drops → adjustment → Residual (total)
    labels = ["Raw |IC|"]
    values = [raw_abs]
    measures = ["absolute"]
    texts = [f"{raw_abs:.4f}"]

    sum_deltas = 0.0
    for c in contribs:
        delta = c["delta_ic"]
        # delta > 0 means style k was stripping alpha; show as downward bar
        labels.append(f"− {c['style']}")
        values.append(-delta)
        measures.append("relative")
        pct_str = f"  ({c['pct']:.0f}%)" if c.get("pct") is not None else ""
        texts.append(f"−{delta:.4f}{pct_str}")
        sum_deltas += delta

    # Reconcile: the approximation gap (styles are correlated → leave-one-out
    # deltas don't sum exactly to raw−residual). Show explicitly so bar end
    # matches real residual.
    expected_residual = raw_abs - sum_deltas
    adjustment = residual_abs - expected_residual
    if abs(adjustment) > 1e-5:
        labels.append("joint / other")
        values.append(adjustment)
        measures.append("relative")
        texts.append(f"{adjustment:+.4f}")

    labels.append("Residual |IC|")
    values.append(0.0)
    measures.append("total")
    texts.append(f"{residual_abs:.4f}")

    fig = go.Figure(go.Waterfall(
        x=labels,
        y=values,
        measure=measures,
        text=texts,
        textposition="outside",
        connector={"line": {"color": "#94a3b8", "dash": "dot"}},
        increasing={"marker": {"color": "#10b981"}},   # joint gains (rare, green)
        decreasing={"marker": {"color": "#ef4444"}},   # style strips (red)
        totals={"marker": {"color": "#3b82f6"}},       # anchors (blue)
    ))
    subtitle = f"alpha_survival = {survive:.2f}" if survive is not None else ""
    fig.update_layout(
        title=f"Alpha Attribution Waterfall  {subtitle}".strip(),
        yaxis_title="|IC|",
        showlegend=False,
    )
    return fig
