"""JudgeCharts -- visualize structured judge verdict and evidence.

Reads judge_report + judge_packet data (assembled by builder._load_judge_data)
and generates Plotly figures for the verdict section of factor reports.

No computation is performed here -- pure visualization of upstream data.
"""
from __future__ import annotations

import plotly.graph_objects as go

from report.charts.theme import apply_theme, COLORS


# ── Bucket → numeric score mapping ──────────────────────────────────

_BUCKET_SCORES = {
    # Effect / Strength
    "strong": 3, "borderline": 2, "weak": 1,
    # Stability
    "good": 3, "medium": 2, "poor": 1,
    # Redundancy (inverted: low overlap = good)
    "low": 3, "acceptable": 2, "high": 1,
    # Feasibility
    "ok": 3,
    # Risk model
    # "acceptable": 2 already covered
    # Mechanism alignment
    "aligned": 3, "unclear": 2, "drifted": 1,
    # Execution gate
    "pass": 3, "warn": 2, "fail_technical": 1,
}

_SEVERITY_COLORS = {
    "fatal": COLORS["negative"],
    "high": "#ff7f0e",
    "medium": "#ffd700",
    "info": COLORS["positive"],
}

_SEVERITY_ORDER = {"fatal": 0, "high": 1, "medium": 2, "info": 3}


def _score(bucket: str) -> int:
    """Map a bucket label to a 1-3 score."""
    return _BUCKET_SCORES.get(bucket, 2)


# ── Public API ───────────────────────────────────────────────────────


def generate_charts(judge_data: dict) -> dict[str, go.Figure]:
    """Generate judge evidence charts.

    Args:
        judge_data: Dict with keys: candidate_verdict, candidate_brief,
                    validation_metrics (optional).

    Returns:
        Dict mapping chart_name -> go.Figure.  Empty entries are skipped.
    """
    if not judge_data:
        return {}

    charts = {}

    fig = _verdict_radar_6d(judge_data)
    if fig:
        charts["verdict_radar_6d"] = fig

    fig = _reason_code_bar(judge_data)
    if fig:
        charts["reason_code_bar"] = fig

    fig = _holdout_comparison(judge_data)
    if fig:
        charts["holdout_comparison"] = fig

    return charts


def verdict_badge(judge_data: dict) -> dict | None:
    """Extract structured verdict summary for skill to render as callout.

    Returns:
        Dict with verdict, reason_summary, holdout_review — or None.
    """
    if not judge_data:
        return None

    cv = judge_data.get("candidate_verdict", {})
    verdict = cv.get("verdict")
    if not verdict:
        return None

    reason_codes = cv.get("reason_codes", [])
    # Normalize: reason_codes may be list of dicts or list of strings
    normalized = []
    for rc in reason_codes:
        if isinstance(rc, str):
            normalized.append({"code": rc, "severity": "info"})
        else:
            normalized.append(rc)
    top_codes = [rc["code"] for rc in normalized if rc.get("severity") in ("fatal", "high")]
    if not top_codes:
        top_codes = [rc["code"] for rc in normalized[:3]]

    return {
        "verdict": verdict,
        "reason_summary": ", ".join(top_codes) if top_codes else "no issues",
        "holdout_review": cv.get("holdout_review_required", False),
    }


# ── Individual chart builders ────────────────────────────────────────


def _verdict_radar_6d(judge_data: dict) -> go.Figure | None:
    """Radar chart of the 6-dimension judge assessment."""
    brief = judge_data.get("candidate_brief", {})
    evidence = judge_data.get("candidate_verdict", {}).get("evidence_summary", {})

    # Try candidate_brief buckets first, fall back to evidence_summary
    dims = {
        "Effect": brief.get("validation_effect_bucket")
                  or evidence.get("statistical_strength"),
        "Stability": brief.get("stability_bucket")
                     or evidence.get("stability"),
        "Redundancy": brief.get("redundancy_bucket")
                      or evidence.get("redundancy"),
        "Feasibility": brief.get("feasibility_bucket")
                       or evidence.get("feasibility"),
        "Risk Model": brief.get("risk_model_review_bucket")
                      or evidence.get("risk_model_review"),
        "Mechanism": evidence.get("mechanism_alignment"),
    }

    # Need at least 4 dimensions to make a useful radar
    filled = {k: v for k, v in dims.items() if v is not None}
    if len(filled) < 4:
        return None

    labels = list(filled.keys())
    scores = [_score(v) for v in filled.values()]
    bucket_labels = list(filled.values())

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],  # close the polygon
        theta=labels + [labels[0]],
        fill="toself",
        fillcolor="rgba(99, 110, 250, 0.2)",
        line=dict(color=COLORS["primary"], width=2),
        text=bucket_labels + [bucket_labels[0]],
        hovertemplate="%{theta}: %{text} (%{r}/3)<extra></extra>",
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 3], tickvals=[1, 2, 3],
                            ticktext=["Weak", "Border", "Strong"]),
        ),
    )

    verdict = judge_data.get("candidate_verdict", {}).get("verdict", "")
    title = f"6-Dimension Assessment — {verdict.upper()}" if verdict else "6-Dimension Assessment"

    return apply_theme(fig, title=title)


def _reason_code_bar(judge_data: dict) -> go.Figure | None:
    """Horizontal bar chart of reason codes, colored by severity."""
    cv = judge_data.get("candidate_verdict", {})
    reason_codes = cv.get("reason_codes", [])

    if not reason_codes:
        return None

    # Normalize: reason_codes may be list of dicts or list of strings
    normalized = []
    for rc in reason_codes:
        if isinstance(rc, str):
            normalized.append({"code": rc, "severity": "info"})
        else:
            normalized.append(rc)

    # Sort by severity (fatal first)
    sorted_codes = sorted(
        normalized,
        key=lambda rc: _SEVERITY_ORDER.get(rc.get("severity", "info"), 3),
    )

    codes = [rc["code"] for rc in sorted_codes]
    severities = [rc.get("severity", "info") for rc in sorted_codes]
    colors = [_SEVERITY_COLORS.get(s, COLORS["neutral"]) for s in severities]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=codes,
        x=[1] * len(codes),
        orientation="h",
        marker_color=colors,
        text=severities,
        textposition="inside",
        hovertemplate="%{y}: %{text}<extra></extra>",
    ))

    fig.update_xaxes(visible=False)
    fig.update_layout(
        height=max(200, 40 * len(codes) + 80),
    )

    return apply_theme(fig, title="Reason Codes")


def _holdout_comparison(judge_data: dict) -> go.Figure | None:
    """Grouped bar comparing validation vs holdout IC metrics."""
    brief = judge_data.get("candidate_brief", {})
    val_metrics = judge_data.get("validation_metrics", {})

    holdout_ic = brief.get("holdout_ic_mean")
    if holdout_ic is None:
        return None

    holdout_ir = brief.get("holdout_ic_ir")
    val_ic = val_metrics.get("ic_mean_validation")
    val_ir = val_metrics.get("ic_ir_validation")

    # Need at least IC comparison
    if val_ic is None:
        return None

    metrics = ["IC Mean"]
    val_values = [abs(val_ic)]
    holdout_values = [abs(holdout_ic)]

    if val_ir is not None and holdout_ir is not None:
        metrics.append("ICIR")
        val_values.append(abs(val_ir))
        holdout_values.append(abs(holdout_ir))

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=metrics, y=val_values,
        name="Validation",
        marker_color=COLORS["is_period"],
        text=[f"{v:.4f}" for v in val_values],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        x=metrics, y=holdout_values,
        name="Holdout",
        marker_color=COLORS["oos_period"],
        text=[f"{v:.4f}" for v in holdout_values],
        textposition="outside",
    ))

    fig.update_layout(barmode="group")

    # Annotate decay ratio
    decay_ratio = brief.get("holdout_decay_ratio")
    if decay_ratio is not None:
        fig.add_annotation(
            x=0.5, y=max(val_values + holdout_values) * 1.1,
            text=f"Holdout Decay Ratio = {decay_ratio:.2f}",
            showarrow=False, font=dict(size=13),
            xref="paper", yref="y",
        )

    return apply_theme(fig, title="Validation vs Holdout")
