"""ExecuteEvidenceCharts -- visualize pre-computed metrics from the
execute/judge pipeline.

Reads structured evidence already loaded from research_result.yaml
(via builder._load_execute_evidence) and generates Plotly figures.

No computation is performed here -- pure visualization of upstream data.
"""
from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from report.charts.theme import apply_theme, COLORS


def generate_charts(evidence: dict) -> dict[str, go.Figure]:
    """Generate all evidence charts from execute_evidence dict.

    Args:
        evidence: Dict with keys: evaluation, risk_review, feasibility,
                  similarity, diagnostics, execution_gate.

    Returns:
        Dict mapping chart_name -> go.Figure.  Empty entries are skipped.
    """
    charts = {}

    evaluation = evidence.get("evaluation", {})
    risk_review = evidence.get("risk_review", {})
    feasibility = evidence.get("feasibility", {})

    fig = _style_exposure_bar(risk_review)
    if fig:
        charts["style_exposure_bar"] = fig

    fig = _alpha_waterfall(risk_review)
    if fig:
        charts["alpha_waterfall"] = fig

    fig = _support_window_ic(evaluation)
    if fig:
        charts["support_window_ic"] = fig

    fig = _feasibility_dashboard(feasibility)
    if fig:
        charts["feasibility_dashboard"] = fig

    fig = _quintile_returns_oos(evaluation)
    if fig:
        charts["quintile_returns_oos"] = fig

    fig = _stability_summary(evaluation)
    if fig:
        charts["stability_summary"] = fig

    return charts


# ── Individual chart builders ──────────────────────────────────────────


def _style_exposure_bar(risk_review: dict) -> go.Figure | None:
    """Horizontal bar chart of Barra style factor exposures."""
    exposures = risk_review.get("style_exposures")
    if not exposures:
        return None

    # Sort by absolute value descending
    items = sorted(exposures.items(), key=lambda x: abs(x[1]))
    names = [k for k, _ in items]
    values = [v for _, v in items]
    colors = [COLORS["negative"] if v > 0.15 else COLORS["primary"] for v in values]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names, x=values, orientation="h",
        marker_color=colors,
        text=[f"{v:.3f}" for v in values],
        textposition="outside",
    ))

    # Threshold line at 0.15
    fig.add_vline(x=0.15, line_dash="dash", line_color="gray",
                  annotation_text="高暴露阈值", annotation_position="top right")

    r2 = risk_review.get("style_r_squared")
    title = "Barra 风格因子暴露"
    if r2 is not None:
        title += f"  (R² = {r2:.3f})"

    return apply_theme(fig, title=title)


def _alpha_waterfall(risk_review: dict) -> go.Figure | None:
    """Waterfall chart: raw IC → cap-neutral IC → Barra residual IC.

    Shows how much alpha survives each neutralization step.
    """
    raw = risk_review.get("raw_view_ic")
    cap_neutral = risk_review.get("cap_industry_neutral_ic")
    residual = risk_review.get("barra_residual_ic")

    if raw is None:
        return None

    # Build waterfall entries
    labels = ["Raw IC"]
    values = [abs(raw)]
    text = [f"{raw:+.4f}"]

    if cap_neutral is not None:
        drop_cap = abs(raw) - abs(cap_neutral)
        labels.append("Cap/Industry\n中性化损失")
        values.append(-drop_cap)
        text.append(f"-{drop_cap:.4f}")

        labels.append("Cap-Neutral IC")
        values.append(0)  # subtotal
        text.append(f"{cap_neutral:+.4f}")

    if residual is not None and cap_neutral is not None:
        drop_barra = abs(cap_neutral) - abs(residual)
        labels.append("Barra 风格\n剥离损失")
        values.append(-drop_barra)
        text.append(f"-{drop_barra:.4f}")

        labels.append("Residual IC")
        values.append(0)  # subtotal
        text.append(f"{residual:+.4f}")

    if len(labels) < 3:
        return None

    measures = []
    for label in labels:
        if "损失" in label:
            measures.append("relative")
        elif label in ("Cap-Neutral IC", "Residual IC"):
            measures.append("total")
        else:
            measures.append("absolute")

    fig = go.Figure(go.Waterfall(
        orientation="v",
        x=labels,
        y=values,
        measure=measures,
        text=text,
        textposition="outside",
        connector={"line": {"color": "rgb(63, 63, 63)"}},
        increasing={"marker": {"color": COLORS["positive"]}},
        decreasing={"marker": {"color": COLORS["negative"]}},
        totals={"marker": {"color": COLORS["primary"]}},
    ))

    survival = risk_review.get("alpha_survival_ratio")
    title = "Alpha 存活路径"
    if survival is not None:
        title += f"  (存活率 = {survival:.1%})"

    return apply_theme(fig, title=title)


def _support_window_ic(evaluation: dict) -> go.Figure | None:
    """Bar chart comparing IC across multiple validation windows."""
    checks = evaluation.get("support_window_checks")
    if not checks or len(checks) < 2:
        return None

    windows = [c["window_id"] for c in checks]
    ic_means = [c.get("ic_mean", c.get("ic_ir", 0)) for c in checks]
    consistent = [c.get("sign_consistency_support", True) for c in checks]

    colors = [
        COLORS["positive"] if c else COLORS["negative"]
        for c in consistent
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=windows, y=ic_means,
        marker_color=colors,
        text=[f"{v:.4f}" for v in ic_means],
        textposition="outside",
    ))

    fig.add_hline(y=0, line_dash="dot", line_color="gray")

    return apply_theme(fig, title="多验证窗口 IC 一致性")


def _feasibility_dashboard(feasibility: dict) -> go.Figure | None:
    """Horizontal bar dashboard of 4 key feasibility metrics."""
    if not feasibility:
        return None

    metrics = {
        "Coverage": feasibility.get("coverage"),
        "Liquidity Coverage": feasibility.get("liquidity_coverage_ratio"),
        "Turnover": feasibility.get("turnover"),
        "Tail Concentration": feasibility.get("tail_trade_concentration"),
        "Small-Cap Conc.": feasibility.get("small_cap_concentration"),
    }

    # Filter out None values
    metrics = {k: v for k, v in metrics.items() if v is not None}
    if not metrics:
        return None

    names = list(metrics.keys())
    values = list(metrics.values())

    # Color: green if good, red if concerning
    thresholds = {
        "Coverage": (0.8, True),         # higher is better
        "Liquidity Coverage": (0.7, True),
        "Turnover": (0.3, False),         # lower is better
        "Tail Concentration": (0.3, False),
        "Small-Cap Conc.": (0.4, False),
    }

    colors = []
    for name, val in zip(names, values):
        thresh, higher_better = thresholds.get(name, (0.5, True))
        if higher_better:
            colors.append(COLORS["positive"] if val >= thresh else COLORS["negative"])
        else:
            colors.append(COLORS["positive"] if val <= thresh else COLORS["negative"])

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=names, x=values, orientation="h",
        marker_color=colors,
        text=[f"{v:.2%}" if v <= 1 else f"{v:.2f}" for v in values],
        textposition="outside",
    ))

    fig.update_xaxes(range=[0, max(values) * 1.3])

    return apply_theme(fig, title="交易可行性指标")


def _quintile_returns_oos(evaluation: dict) -> go.Figure | None:
    """Bar chart of Q1-Q5 daily mean returns from OOS period."""
    qr = evaluation.get("quintile_returns")
    if not qr:
        return None

    groups = ["Q1", "Q2", "Q3", "Q4", "Q5"]
    keys = ["q1", "q2", "q3", "q4", "q5"]
    values = [qr.get(k) for k in keys]

    if any(v is None for v in values):
        return None

    # Annualize: daily_return * 242
    ann_values = [v * 242 for v in values]

    colors = [
        COLORS["positive"] if v > 0 else COLORS["negative"]
        for v in ann_values
    ]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=groups, y=ann_values,
        marker_color=colors,
        text=[f"{v:+.1%}" for v in ann_values],
        textposition="outside",
    ))

    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    fig.update_yaxes(title_text="年化收益率")

    mono = evaluation.get("monotonicity_validation")
    title = "验证期分组收益 (OOS)"
    if mono is not None:
        title += f"  (单调性 = {mono:.2f})"

    return apply_theme(fig, title=title)


def _stability_summary(evaluation: dict) -> go.Figure | None:
    """Combined stability view: train/OOS comparison + support windows + expanding."""
    ic_train = evaluation.get("ic_mean_train")
    ic_oos = evaluation.get("ic_mean_validation")
    decay_ratio = evaluation.get("train_validation_decay_ratio")
    expanding_stability = evaluation.get("expanding_window_ic_stability")
    split_stability = evaluation.get("split_stability")
    regime_stability = evaluation.get("regime_stability")

    if ic_train is None or ic_oos is None:
        return None

    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=["IS → OOS 衰减", "稳定性指标"],
        column_widths=[0.45, 0.55],
    )

    # Left panel: IS vs OOS IC bars
    fig.add_trace(go.Bar(
        x=["In-Sample", "Out-of-Sample"],
        y=[abs(ic_train), abs(ic_oos)],
        marker_color=[COLORS["is_period"], COLORS["oos_period"]],
        text=[f"{ic_train:.4f}", f"{ic_oos:.4f}"],
        textposition="outside",
        showlegend=False,
    ), row=1, col=1)

    if decay_ratio is not None:
        fig.add_annotation(
            x=0.5, y=max(abs(ic_train), abs(ic_oos)) * 0.5,
            text=f"衰减比 = {decay_ratio:.2f}",
            showarrow=False, font=dict(size=13),
            xref="x", yref="y",
        )

    # Right panel: stability metrics as horizontal bars
    stability_metrics = {}
    if expanding_stability is not None:
        stability_metrics["扩展窗口稳定性"] = expanding_stability
    if decay_ratio is not None:
        stability_metrics["IS→OOS 保持率"] = decay_ratio

    # Map bucket labels to numeric scores
    bucket_scores = {"high": 1.0, "medium": 0.6, "low": 0.3,
                     "good": 1.0, "poor": 0.3}
    if split_stability:
        stability_metrics["分段稳定性"] = bucket_scores.get(split_stability, 0.5)
    if regime_stability:
        stability_metrics["行情稳定性"] = bucket_scores.get(regime_stability, 0.5)

    if stability_metrics:
        s_names = list(stability_metrics.keys())
        s_values = list(stability_metrics.values())
        s_colors = [
            COLORS["positive"] if v >= 0.6 else
            (COLORS["neutral"] if v >= 0.3 else COLORS["negative"])
            for v in s_values
        ]

        fig.add_trace(go.Bar(
            y=s_names, x=s_values, orientation="h",
            marker_color=s_colors,
            text=[f"{v:.2f}" for v in s_values],
            textposition="outside",
            showlegend=False,
        ), row=1, col=2)

        fig.update_xaxes(range=[0, 1.15], row=1, col=2)

    fig.update_yaxes(title_text="|IC|", row=1, col=1)

    return apply_theme(fig, title="信号稳定性总览")
