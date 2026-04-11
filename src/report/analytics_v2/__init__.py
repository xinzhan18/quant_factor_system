"""Report analytics (v2) — consume ``result.yaml`` directly, no recomputation.

Per refactor_plan R4 "do not recompute", these functions walk a
``result.yaml`` candidate dict and transform it into report-ready
sections. The old ``src/report/analytics/`` module re-ran IC /
quintile / Barra per report; v2 never does — the Phase 2 numeric
output is the source of truth.

Each function takes the ``result.yaml`` candidate dict (the one that
will be passed to a factor.md subagent) and returns a structured dict
ready to render as markdown or plotly traces.
"""

from report.analytics_v2.ic import extract_ic_section
from report.analytics_v2.profit import extract_profit_section
from report.analytics_v2.risk import extract_risk_section
from report.analytics_v2.summary import build_summary

__all__ = [
    "extract_ic_section",
    "extract_profit_section",
    "extract_risk_section",
    "build_summary",
]
