"""Factor report generation -- analytics, scoring, and HTML rendering."""

from report.analytics import (
    ICAnalyzer, ProfitAnalyzer, ConditionalAnalyzer,
    DecayAnalyzer, UniquenessAnalyzer,
)
from report.scorer import CompositeScorer
from report.builder import ReportDataBuilder
from report.renderer import ReportRenderer  # deprecated but kept for backward compat

__all__ = [
    "ICAnalyzer", "ProfitAnalyzer", "ConditionalAnalyzer",
    "DecayAnalyzer", "UniquenessAnalyzer",
    "CompositeScorer", "ReportDataBuilder", "ReportRenderer",
]
